from data import Data
import pandas as pd
from math import sqrt

DEBUG = False

def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)

def schedule_heuristic(data: Data, days = 1):
    worktime_minutes = days * 24 * 60
    timeline_minutes = list(range(worktime_minutes))
    setup_timeline = pd.Series([0]*worktime_minutes)

    # Have a column for each machine, in each row there shall be the current
    # tool being used, or None
    all_tasks = pd.concat([data.initial_data, data.inst_data], ignore_index=True)
    all_tasks["scheduled"] = False

    unique_machines = all_tasks["Machine"].unique()

    parts_timeline = pd.DataFrame(index=timeline_minutes, columns=unique_machines)
    parts_timeline[unique_machines] = None

    tool_timeline = pd.DataFrame(index=timeline_minutes, columns=unique_machines)
    tool_timeline[unique_machines] = None

    # For the minute 0 we must check what machines were active
    # The machines with 0 production time finish at minute 0
    just_finished = data.initial_data.loc[data.initial_data["Prod_time"] == 0, ["Machine", "Tool", "Part"]]
    for machine, tool, part in just_finished.itertuples(index=False):
        parts_timeline[machine].iloc[0] = part
        tool_timeline[machine].iloc[0] = tool
        all_tasks.loc[all_tasks["Part"] == part, "scheduled"] = True

    # The machines that are still active will be from minute 0 to the finishing minute 
    under_work = data.initial_data.loc[data.initial_data["Prod_time"] > 0, ["Machine", "Tool", "Part", "Prod_time"]]
    for machine, tool, part, prodtime in under_work.itertuples(index=False):
        parts_timeline[machine].iloc[0:prodtime - 1] = part
        tool_timeline[machine].iloc[0:prodtime - 1] = tool
        all_tasks.loc[all_tasks["Part"] == part, "scheduled"] = True


    for minute in timeline_minutes[1:]:
        print(f"{minute=}")
        shift_info = data.shift_data.iloc[int(minute / 480)]
        total_operators = shift_info["Operators"]
        setup_teams = shift_info["Setup_teams"]

        # Check operating machines
        operating_machines = parts_timeline.loc[minute, parts_timeline.iloc[minute].notnull()].index.to_list()
        available_machines = parts_timeline.loc[minute, parts_timeline.iloc[minute].isnull()].index.to_list()

        # 
        if len(operating_machines) == unique_machines.shape[0]:
            break

        occupied_operators = 0
        for col, value in parts_timeline.iloc[minute].iteritems():
            if value is None or value == "setup":
                continue
            occupied_operators += all_tasks.loc[(all_tasks["Machine"] == col) & (all_tasks["Part"] == value), "Nb_Operator"].iloc[0]

        available_operators = total_operators - occupied_operators

        # Keep track of tasks that might block the loop
        blocked_tasks_lst = []
        blocked_tasks = False
        while available_operators > 0 and not blocked_tasks:
            # Check operating machines
            available_machines = parts_timeline.loc[minute, parts_timeline.loc[minute].isnull()].index.to_list()
            operating_machines = parts_timeline.loc[minute, parts_timeline.loc[minute].notnull()].index.to_list()

            if len(operating_machines) == unique_machines.shape[0]:
                break

            unscheduled_tasks = all_tasks.loc[(all_tasks["scheduled"] == False) & all_tasks["Machine"].isin(available_machines), :].copy(deep=True)
            unscheduled_tasks = unscheduled_tasks.sort_values(by="Prod_time")
            
            # Go to next minute if there are no more tasks to c
            if unscheduled_tasks.empty:
                break

            for index, task in unscheduled_tasks.iterrows():
                if index in blocked_tasks_lst:
                    # Re-running a blocked task, should exit the outer loop or
                    # else it will continue indefinitely
                    blocked_tasks = True
                    continue
                
                # Check if the task is actually not scheduled yet
                if all_tasks.loc[all_tasks["Part"] == task["Part"], "scheduled"].iloc[0] == True:
                    continue

                debug_print(f"{task['Machine']} {task['Tool']} {task['Part']}")

                # Check if the selected task requires less operators than the
                # ones currently available
                if task["Nb_Operator"] > available_operators:
                    debug_print("\t Operators not available")
                    continue
                
                # Checking for setup

                # Get last tool
                previous_tool = tool_timeline.loc[minute-1, task["Machine"]]
                setup_time = 0

                # If for some reason the previous tool is setup, stop
                if previous_tool == "setup":
                    raise Exception("previous tool is setup")
                
                # If the tool in the previous minute is None go back in time
                # until we get the last tool
                idx = 1
                while previous_tool is None and minute-idx >= 0:
                    previous_tool = tool_timeline.loc[minute-idx, task["Machine"]]
                    idx = idx + 1

                # Extract setup time based on previous tool and next tool
                setup_time = data.setup_data.loc[previous_tool, task["Tool"]]
                debug_print(f"\t {previous_tool}->{task['Tool']}: {setup_time}")
                if setup_time > 0:
                    # If for the forseable setup timeline we dont have team
                    # capacity to setup for the current task, continue
                    if any([teams == setup_teams for teams in setup_timeline[minute: minute+setup_time]]):
                        blocked_tasks_lst.append(index)
                        continue
                    # Increment the setup timeline given that a team will be
                    # dedicated to setup for this task 
                    setup_timeline[minute : minute+setup_time] = [x + 1 for x in setup_timeline[minute : minute+setup_time]]
                
                # Check if the setup time + task execution time doesn't exceed
                # our timeline window
                if minute+setup_time+task["Prod_time"] >= worktime_minutes:
                    blocked_tasks_lst.append(index)
                    debug_print("\t Index out of bounds")
                    break
                
                debug_print("\t Adding task")

                # Add part and tool to the timelines
                parts_timeline.loc[
                    minute+setup_time: minute+setup_time+task["Prod_time"], task["Machine"]
                ] = task["Part"]

                tool_timeline.loc[
                    minute+setup_time:minute+setup_time+task["Prod_time"], task["Machine"]
                ] = task["Tool"]


                # Write "setup" to the timelines if it is required
                if setup_time > 0:
                    parts_timeline.loc[
                        minute:minute+setup_time, task["Machine"]
                    ] = "setup"
                    tool_timeline.loc[
                        minute:minute+setup_time, task["Machine"]
                    ] = "setup"

                # Reduce operator availability
                available_operators -= task["Nb_Operator"]

                # Mark the current task as already scheduled
                all_tasks.loc[all_tasks["Part"] == task["Part"], "scheduled"] = True


    return parts_timeline, tool_timeline, setup_timeline