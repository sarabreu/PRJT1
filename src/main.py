from copy import deepcopy

from tqdm import tqdm

from heuristic import schedule_heuristic
from diagram import display_gantt
from configuration import settings, DayRange
import multiprocessing
import time
from multiprocessing import freeze_support, Lock

from data import save_gantt, load, Data, save, load_saved

def preprocessing(raw_data: Data):
    data = deepcopy(raw_data)
    data.setup_data = data.setup_data.set_index(data.setup_data["Setup(min)"], drop = True)
    data.setup_data = data.setup_data.drop(columns="Setup(min)")
    data.inst_data = data.inst_data.rename(columns={"Proc_time(min)": "Prod_time"})
    return data

def display(instance):
    sorted_setup = "_sorted_setup" if settings.sort_setup else "_spt"
    days_file = "_5_days" if settings.day_range == DayRange.FIVE else "_1_day"
    suffix = str(instance) + sorted_setup + days_file
    schedule = load_saved(f"schedule_{suffix}.xlsx")
    fig = display_gantt(schedule, instance)
    if not settings.run_heuristic:
        save_gantt(fig, f"gantt_{suffix}.html")

def save_all(timeline, all_tasks, instance):
    sorted_setup = "_sorted_setup" if settings.sort_setup else "_spt"
    days_file = "_5_days" if settings.day_range == DayRange.FIVE else "_1_day"
    suffix = str(instance) + sorted_setup + days_file
    save(timeline.part, f"part_timeline_{suffix}.xlsx")
    save(timeline.tool, f"tool_timeline_{suffix}.xlsx")
    save(timeline.setup, f"setup_timeline_{suffix}.xlsx")
    save(timeline.schedule, f"schedule_{suffix}.xlsx")
    save(timeline.packs_hour, f"packs_hour_{suffix}.xlsx")
    save(all_tasks, f"all_tasks_{suffix}.xlsx")

def run_once(inst):
    days = settings.days
    if not settings.run_heuristic:
        display(inst)
        return
    print(f"Instance: {inst} | days: {days}")
    raw_data = load(inst)
    data = preprocessing(raw_data)
    timeline, all_tasks = schedule_heuristic(data, inst, days)
    save_all(timeline, all_tasks, inst)

def run_parallel(instances: list):
    freeze_support()
    with multiprocessing.Pool(len(instances), initializer=tqdm.set_lock, initargs=(Lock(),)) as p:
        p.map(run_once, instances)

def main():
    start_time = time.time()
    instances = settings.instance
    if isinstance(instances, int):
        instances = [instances]

    if len(instances) > 1 and settings.run_parallelized:
        run_parallel(instances)
    else:
        for inst in instances:
            run_once(inst)

    end_time = time.time()
    
    print(f"\nThe program took {end_time-start_time:.2f} seconds to run.")
    time.sleep(1)
    print("\nDisplaying Gantt charts in 3...")
    time.sleep(1)
    print("2...")
    time.sleep(1)
    print("1...")
    time.sleep(1)
    print("...")
    for inst in instances:
        display(inst)

if __name__ == "__main__":
    main()