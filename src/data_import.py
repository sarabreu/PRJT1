"""Reads data from filesystem"""

#########################################################
import os
# this way we can import data from the data directory
# no matter from where we run this code
script_folder = os.path.dirname(os.path.realpath(__file__))
working_folder = os.path.normpath(script_folder + os.sep + os.pardir)

def data_file_path(name: str):
    return os.path.join(working_folder,"data",name)
#########################################################


import pandas as pd

print(data_file_path("data.xlsx"))

PREFIX = "PRJT1_2022-2023_Sched_instance_"
SUFFIX = ".xlsx"

def get_instance(number: int, sheet_name: str) -> pd.DataFrame:
    file_name = PREFIX + str(number) + SUFFIX
    file_path = data_file_path(file_name)
    return pd.read_excel(file_path, sheet_name)