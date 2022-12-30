import pandas as pd
from copy import deepcopy

from data import load, Data, save, load_saved
from heuristic import schedule_heuristic
from diagram import display_gantt
from configuration import settings

def preprocessing(raw_data: Data):
    data = deepcopy(raw_data)
    data.setup_data = data.setup_data.set_index(data.setup_data["Setup(min)"], drop = True)
    data.setup_data = data.setup_data.drop(columns="Setup(min)")
    data.inst_data = data.inst_data.rename(columns={"Proc_time(min)": "Prod_time"})
    return data

def display(instance):
    schedule = load_saved(f"schedule_{instance}.xlsx")
    display_gantt(schedule, None)

def save_all(timeline, all_tasks, instance):
    save(timeline.part, f"part_timeline_{instance}.xlsx")
    save(timeline.tool, f"tool_timeline_{instance}.xlsx")
    save(timeline.setup, f"setup_timeline_{instance}.xlsx")
    save(timeline.schedule, f"schedule_{instance}.xlsx")
    save(all_tasks, f"all_tasks_{instance}.xlsx")

def main():
    instances = settings.instance
    if isinstance(instances, int):
        instances = [instances]
    days = settings.days

    for inst in instances:
        if not settings.run_heuristic:
            display(inst)
            return
        print(f"Instance: {inst} | days: {days}")
        raw_data = load(inst)
        data = preprocessing(raw_data)
        timeline, all_tasks = schedule_heuristic(data, days)
        save_all(timeline, all_tasks, inst)
        display_gantt(timeline.schedule, inst)
    

if __name__ == "__main__":
    main()