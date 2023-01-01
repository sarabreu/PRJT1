from datetime import datetime
from enum import Enum, auto

class DayRange(Enum):
    ONE = auto()
    FIVE = auto()

dtn = datetime.now()
dtn_zeroed = datetime(dtn.year, dtn.month, dtn.day)

class Settings:
    instance = [2]
    day_range = DayRange.FIVE # mudar quando quisermos 1 ou 5 dias
    days = 5
    run_heuristic = True # False to only draw the Gantt diagram
    allow_unfinished_tasks = True
    debug_prints = False
    start_time = dtn_zeroed

settings = Settings()