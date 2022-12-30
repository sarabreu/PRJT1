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


PREFIX = "PRJT1_2022-2023_Sched_instance_"
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

def load(instance):
    print("Loading Opt_Par")
    shift_data = get_instance(instance, 'Opt_Par')
    print("Loading Init_data")
    initial_data = get_instance(instance,'Init_data')
    print("Loading Inst_data")
    inst_data = get_instance(instance,'Inst_data')
    print("Loading Setup_data")
    setup_data = get_instance(instance, 'Setup_data')
    return Data(shift_data, initial_data, inst_data, setup_data)

def load_saved(name):
    print(f"Loading {name}")
    file_path = data_file_path(name, folder = "outputs")
    return pd.read_excel(file_path)

def save(timeline: pd.DataFrame, filename):
    print(f"Saving {filename}")
    filepath = data_file_path(filename, folder = "outputs")
    timeline.to_excel(filepath)

def save_gantt(fig, filename):
    filepath = data_file_path(filename, folder = "outputs")
    fig.write_html(filepath)