# """Reads data from filesystem"""
import pandas as pd
import os
from dataclasses import dataclass
# #########################################################
# this way we can import data from the data directory
# no matter from where we run this code
script_folder = os.path.dirname(os.path.realpath(__file__))
working_folder = os.path.normpath(script_folder + os.sep + os.pardir)

def data_file_path(name: str):
    return os.path.join(working_folder,"data",name)
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


def load(instance):
    shift_data = get_instance(instance, 'Opt_Par')
    initial_data = get_instance(instance,'Init_data')
    inst_data = get_instance(instance,'Inst_data')
    setup_data = get_instance(instance, 'Setup_data')
    return Data(shift_data, initial_data, inst_data, setup_data)


def save(timeline: pd.DataFrame, filename = "timeline.xlsx"):
    filepath = data_file_path(filename)
    timeline.to_excel(filepath)