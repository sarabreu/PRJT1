import pandas as pd
from copy import deepcopy

from data import load, Data, save
from heuristic import schedule_heuristic

INSTANCE = 1

def preprocessing(raw_data: Data):
    data = deepcopy(raw_data)
    data.setup_data = data.setup_data.set_index(data.setup_data["Setup(min)"], drop = True)
    data.setup_data = data.setup_data.drop(columns="Setup(min)")
    data.inst_data = data.inst_data.rename(columns={"Proc_time(min)": "Prod_time"})
    return data


def main():
    raw_data = load(INSTANCE)
    data = preprocessing(raw_data)
    part_timeline, tool_timeline, setup_timeline = schedule_heuristic(data)
    print(part_timeline)
    print(tool_timeline)
    print(setup_timeline)
    save(part_timeline, "part_timeline.xlsx")
    save(tool_timeline, "tool_timeline.xlsx")
    save(setup_timeline, "setup_timeline.xlsx")

if __name__ == "__main__":
    main()