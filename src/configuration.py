from datetime import datetime
from enum import Enum, auto

class DayRange(Enum):
    ONE = auto()
    FIVE = auto()

dtn = datetime.now()
dtn_zeroed = datetime(dtn.year, dtn.month, dtn.day)

class Settings:
    instance = [2]
    day_range = DayRange.ONE # mudar quando quisermos 1 ou 5 dias
    days = 1 # mudar quando quisermos 1 ou 5 dias
    run_heuristic = True # False to only draw the Gantt diagram
    allow_unfinished_tasks = True
    sort_setup = True
    debug_prints = False
    start_time = dtn_zeroed

settings = Settings()