# """Reads data from filesystem"""
import pandas as pd
import os
from dataclasses import dataclass
# #########################################################
# this way we can import data from the data directory
# no matter from where we run this code
script_folder = os.path.dirname(os.path.realpath(__file__))
working_folder = os.path.normpath(script_folder + os.sep + os.pardir)

def data_file_path(name: str, folder = "data"):
    return os.path.join(working_folder,folder,name)
# #########################################################

from configuration import settings, DayRange
PREFIX = "PRJT1_2022-2023_Sched5_instance_" if settings.day_range == DayRange.FIVE else "PRJT1_2022-2023_Sched_instance_"
SUFFIX = ".xlsx"

def get_instance(number: int, sheet_name: str) -> pd.DataFrame:
    file_name = PREFIX + str(number) + SUFFIX
    file_path = data_file_path(file_name)
    return pd.read_excel(file_path, sheet_name)


@dataclass
class Data:
    shift_data: pd.DataFrame
    initial_data: pd.DataFrame
    inst_data: pd.DataFrame
    setup_data: pd.DataFrame

@dataclass
class Timeline:
    setup: pd.DataFrame
    part: pd.DataFrame
    tool: pd.DataFrame
    schedule: pd.DataFrame
    packs_hour: pd.DataFrame
    working_operators_hour: pd.DataFrame

    def save(self, suffix):
        save(self.schedule, f"schedule_{suffix}.xlsx")
        save(self.part, f"part_timeline_{suffix}.xlsx")
        save(self.tool, f"tool_timeline_{suffix}.xlsx")
        save(self.setup, f"setup_timeline_{suffix}.xlsx")
        save(self.packs_hour, f"packs_hour_{suffix}.xlsx")
        save(self.working_operators_hour, f"working_operators_{suffix}.xlsx") 

def load(instance):
    print(f"Loading Opt_Par for Instance {instance}")
    shift_data = get_instance(instance, 'Opt_Par')
    print(f"Loading Init_data for Instance {instance}")
    initial_data = get_instance(instance,'Init_data')
    print(f"Loading Inst_data for Instance {instance}")
    inst_data = get_instance(instance,'Inst_data')
    print(f"Loading Setup_data for Instance {instance}")
    setup_data = get_instance(instance, 'Setup_data')
    return Data(shift_data, initial_data, inst_data, setup_data)

def load_saved(name):
    print(f"Loading {name}")
    file_path = data_file_path(name, folder = "outputs")
    return pd.read_excel(file_path)

def save(timeline: pd.DataFrame, filename):
    # print(f"Saving {filename}")
    filepath = data_file_path(filename, folder = "outputs")
    timeline.to_excel(filepath)

def save_gantt(fig, filename):
    filepath = data_file_path(filename, folder = "outputs")
    fig.write_html(filepath)