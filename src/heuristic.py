import os

from tqdm import tqdm
from data import Data, Timeline
import pandas as pd
from datetime import timedelta
from configuration import settings
import math

def debug_print(*args, **kwargs):
    if settings.debug_prints:
        print(*args, **kwargs)


def sort_by_setup(unique_machines, timeline: Timeline, minute, data, unscheduled_tasks: pd.DataFrame):
    
    # Dataframe with machines as lines and unscheduled tasks as columns
    setup_df = pd.DataFrame(index = unique_machines, columns=unscheduled_tasks["Part"])
    
    unscheduled_tasks_cpy = unscheduled_tasks.copy(deep=True)

    #Look for the previous tool used in each machine
    for machine in unique_machines:
        previous_tool = timeline.tool.loc[minute-1, machine]
        
        # If the tool in the previous minute is None go back in time
        # until we get the last tool
        idx = 1
        while previous_tool is None and minute-idx >= 0:
            previous_tool = timeline.tool.loc[minute-idx, machine]
            idx = idx + 1
    
        #Tools used for each unscheduled task
        for _, task in unscheduled_tasks.iterrows():
            if task["Machine"] == machine:
                setup_time = data.setup_data.loc[previous_tool, task["Tool"]]
                setup_df.loc[machine, task["Part"]] = setup_time

    for machine in setup_df.index:
        parts_with_setup = setup_df.loc[machine, :].dropna()

        if parts_with_setup.empty:
            continue

        parts_with_setup = parts_with_setup.sort_values()
        parts_with_setup = list(parts_with_setup.index)

        correspondence = {part: order for order, part in enumerate(parts_with_setup)}
        unscheduled_tasks_cpy = unscheduled_tasks_cpy.sort_values(
            by="Part",
            key=lambda column: column.map(correspondence)
        )

    return unscheduled_tasks_cpy



def schedule_heuristic(data: Data, inst, days = 5):
    start_time = settings.start_time

    worktime_minutes = days * 24 * 60
    timeline_minutes = list(range(worktime_minutes))
    setup_timeline = pd.Series([0]*worktime_minutes)
    schedule_df = pd.DataFrame(columns=["Task", "Start", "Finish", "Resource"])

    data.initial_data["init"] = True
    data.inst_data["init"] = False
    all_tasks = pd.concat([data.initial_data, data.inst_data], ignore_index=True)
    all_tasks["scheduled"] = False

    unique_machines = all_tasks["Machine"].unique()

    # Have a column for each machine, in each row there shall be the current
    # tool being used, or None
    part_timeline = pd.DataFrame(index=timeline_minutes, columns=unique_machines)
    part_timeline[unique_machines] = None

    tool_timeline = pd.DataFrame(index=timeline_minutes, columns=unique_machines)
    tool_timeline[unique_machines] = None

    packs_hour = pd.DataFrame(index=list(range(worktime_minutes)), columns=["Packs_hour"])
    packs_hour["Packs_hour"] = 0
    timeline = Timeline(setup_timeline, part_timeline, tool_timeline, schedule_df, packs_hour)

    # For the minute 0 we must check what machines were active
    # The machines with 0 production time finish at minute 0
    just_finished = data.initial_data.loc[data.initial_data["Prod_time"] == 0, ["Machine", "Tool", "Part"]]
    for machine, tool, part in just_finished.itertuples(index=False):
        timeline.part[machine].iloc[0] = part
        timeline.tool[machine].iloc[0] = tool
        all_tasks.loc[(all_tasks["Part"] == part) & (all_tasks["init"] == True), "scheduled"] = True

    # The machines that are still active will be from minute 0 to the finishing minute 
    under_work = data.initial_data.loc[data.initial_data["Prod_time"] > 0, ["Machine", "Tool", "Part", "Prod_time"]]
    for machine, tool, part, prodtime in under_work.itertuples(index=False):
        timeline.part[machine].iloc[0:prodtime - 1] = part
        timeline.tool[machine].iloc[0:prodtime - 1] = tool
        all_tasks.loc[(all_tasks["Part"] == part) & (all_tasks["init"] == True), "scheduled"] = True
        schedule_row = pd.DataFrame(
            {
                "Task": [machine],
                "Start": [start_time],
                "Finish": [start_time + timedelta(minutes=prodtime-1)],
                "Resource": [f"{part}: {tool}"]
            }
        )
        timeline.schedule = pd.concat([timeline.schedule, schedule_row]).reset_index(drop=True)
       
    minutes = list(timeline_minutes[1:])
    for minute in tqdm(minutes, desc=f"Instance {inst}", position=inst-1, leave=False):
        if (all_tasks["scheduled"] == True).all():
            break

        # Shift information, such as total operators and setup team capacity
        shift_info = data.shift_data.iloc[int(minute % 1440 / 480)]
        total_operators = shift_info["Operators"]
        setup_teams = shift_info["Setup_teams"]

        # Get operating machines and available machines
        operating_machines = timeline.part.loc[minute, timeline.part.iloc[minute].notnull()].index.to_list()
        available_machines = timeline.part.loc[minute, timeline.part.iloc[minute].isnull()].index.to_list()

        # Check if all the machines are running. If so, skip to the next minute
        if len(operating_machines) == unique_machines.shape[0]:
            continue

        # Get maximum production rate
        max_packs_hour = shift_info["Log_train(packs/hour)"]

        if timeline.packs_hour.loc[minute, "Packs_hour"] >= max_packs_hour:
            print(f"Exceeded packs_hour capacity: {timeline.packs_hour.loc[minute, 'Packs_hour']} / {max_packs_hour}")
            continue
        
        # Calculate how many operators are occupied based on the sum of operator
        # requirements for all the currently running tasks
        occupied_operators = 0
        for value in timeline.part.iloc[minute].values:
            if value is None or value == "setup":
                continue
            occupied_operators += all_tasks.loc[all_tasks["Part"] == value, "Nb_Operator"].iloc[0]

        available_operators = total_operators - occupied_operators

        # Keep track of tasks that might block the loop
        blocked_tasks_lst = []
        blocked_tasks = False
        while available_operators > 0 and not blocked_tasks:
            # Get operating machines and available machines
            operating_machines = timeline.part.loc[minute, timeline.part.loc[minute].notnull()].index.to_list()
            available_machines = timeline.part.loc[minute, timeline.part.loc[minute].isnull()].index.to_list()
            used_tools = timeline.tool.loc[minute, timeline.tool.loc[minute].notnull()].values

            # Check if all the machines are running. If so, skip to the next minute
            if len(operating_machines) == unique_machines.shape[0]:
                break
            
            # Get unscheduled tasks whose required machine and tool is also available
            unscheduled_tasks = all_tasks.loc[
                (all_tasks["scheduled"] == False)
                & all_tasks["Machine"].isin(available_machines)
                & (all_tasks["init"] == False)
                & (~all_tasks["Tool"].isin(used_tools))
                , :].copy(deep=True)
            unscheduled_tasks = unscheduled_tasks.sort_values(by="Prod_time")
            unscheduled_tasks = unscheduled_tasks.reset_index(drop=True)


            # Go to next minute if there are no more tasks to complete
            if unscheduled_tasks.empty:
                break

            """SHORTEST SETUP TIME"""
            if settings.sort_setup:
                unscheduled_tasks = sort_by_setup(unique_machines, timeline, minute, data, unscheduled_tasks)

            for index, task in unscheduled_tasks.iterrows():
                # print(current_packs_hour)
                """CHECK ALL SCHEDULING RESTRICTIONS BEFORE ADDING TASK"""

                if index in blocked_tasks_lst:
                    # Re-running a blocked task, should exit the outer loop or
                    # else it will continue indefinitely
                    blocked_tasks = True
                    continue
                
                # Check if the task is already scheduled
                is_scheduled = all_tasks.loc[(all_tasks["Part"] == task["Part"]) & (all_tasks["init"] == False), "scheduled"].iloc[0]
                if is_scheduled == True:
                    blocked_tasks_lst.append(index)
                    continue
                
                # Check if the needed tool is not available
                needed_tool = all_tasks.loc[(all_tasks["Part"] == task["Part"]) & (all_tasks["init"] == False), "Tool"].iloc[0]
                used_tools = timeline.tool.loc[minute, [col for col in timeline.tool.columns if col != task["Machine"]]].values
                if needed_tool in used_tools:
                    blocked_tasks_lst.append(index)
                    continue

                debug_print(f"{task['Machine']} {task['Tool']} {task['Part']}")

                # Check if the selected task requires more operators than the
                # ones currently available
                if task["Nb_Operator"] > available_operators:
                    debug_print("\t Operators not available")
                    blocked_tasks_lst.append(index)
                    continue

                # Checking for setup
                # Get last tool
                previous_tool = timeline.tool.loc[minute-1, task["Machine"]]
                setup_time = 0

                # If for some reason the previous tool is setup, stop
                if previous_tool == "setup":
                    raise Exception("previous tool is setup")
                
                # If the tool in the previous minute is None go back in time
                # until we get the last tool
                idx = 1
                while previous_tool is None and minute-idx >= 0:
                    previous_tool = timeline.tool.loc[minute-idx, task["Machine"]]
                    idx = idx + 1

                # Extract setup time based on previous tool and next tool
                setup_time = 0
                if minute-idx >= 0:
                    setup_time = data.setup_data.loc[previous_tool, task["Tool"]]
                debug_print(f"\t {previous_tool}->{task['Tool']}: {setup_time}")
                if setup_time > 0:
                    # If for the forseable setup timeline we dont have team
                    # capacity to setup for the current task, continue
                    if any([teams == setup_teams for teams in timeline.setup[minute: minute+setup_time]]):
                        blocked_tasks_lst.append(index)
                        continue
                    # Increment the setup timeline given that a team will be
                    # dedicated to setup for this task 
                    timeline.setup[minute : minute+setup_time] = [x + 1 for x in timeline.setup[minute : minute+setup_time]]
                    
                    
                # Check if the setup time + task execution time doesn't exceed
                # our timeline window
                finish = minute+setup_time+task["Prod_time"]-1
                if finish >= worktime_minutes:
                    if not settings.allow_unfinished_tasks:
                        blocked_tasks_lst.append(index)
                        debug_print("\t Index out of bounds")
                        break
                    finish = worktime_minutes - 1

                # Check if allocating the task surpasses packs/hour capacity
                scheduled_tasks_packs_hour = timeline.packs_hour.loc[minute, "Packs_hour"]
                max_packs = data.shift_data.iloc[int(finish % 1440 / 480)]["Log_train(packs/hour)"]
                if scheduled_tasks_packs_hour + math.floor(task["Packs_hour"]) >= max_packs:
                    blocked_tasks_lst.append(index)
                    continue
                
                """TASK PASSED ALL RESTRICTIONS, HAS APPROVAL TO BE SCHEDULED"""
                
                debug_print("\t Adding task")

                all_tasks.loc[(all_tasks["Part"] == task["Part"]) & (all_tasks["init"] == False), "setup"] = setup_time
                # Add start minute of scheduled task
                all_tasks.loc[(all_tasks["Part"] == task["Part"]) & (all_tasks["init"] == False), "start"] = minute

                schedule_row = pd.DataFrame(
                    {
                        "Task": [task["Machine"]],
                        "Start": [start_time + timedelta(minutes=int(minute+setup_time))],
                        "Finish": [start_time + timedelta(minutes=int(finish))],
                        "Resource": [f"{task['Part']}: {task['Tool']}"]
                    }
                )
                timeline.schedule = pd.concat([timeline.schedule, schedule_row]).reset_index(drop=True)
                
                # Add part and tool to the timelines
                timeline.part.loc[
                    minute+setup_time:finish, task["Machine"]
                ] = task["Part"]

                timeline.tool.loc[
                    minute+setup_time:finish, task["Machine"]
                ] = task["Tool"]


                # Write "setup" to the timelines if it is required
                if setup_time > 0:
                    schedule_row = pd.DataFrame(
                        {
                            "Task": [task["Machine"]],
                            "Start": [start_time + timedelta(minutes=int(minute))],
                            "Finish": [start_time + timedelta(minutes=int(minute+setup_time-1))],
                            "Resource": ["Setup"]
                        }
                    )
                    timeline.schedule = pd.concat([timeline.schedule, schedule_row]).reset_index(drop=True)
                    timeline.part.loc[
                        minute:minute+setup_time-1, task["Machine"]
                    ] = "setup"
                    timeline.tool.loc[
                        minute:minute+setup_time-1, task["Machine"]
                    ] = "setup"

                # Reduce operator availability
                available_operators -= task["Nb_Operator"]

                # Increase current packs per hour
                timeline.packs_hour.loc[minute+setup_time:finish, "Packs_hour"] +=  math.floor(task["Packs_hour"])

                # Mark the current task as already scheduled
                all_tasks.loc[(all_tasks["Part"] == task["Part"]) & (all_tasks["init"] == False), "scheduled"] = True

    return timeline, all_tasks