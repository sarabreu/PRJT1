from datetime import datetime
from enum import Enum, auto

class DayRange(Enum):
    ONE = auto()
    FIVE = auto()

dtn = datetime.now()
dtn_zeroed = datetime(dtn.year, dtn.month, dtn.day)

class Settings:
    # Simulated scenario settings
    instance = [3]
    day_range = DayRange.ONE # File type, change for either one day or five day files
    days = 1 # Simulated time

    # Heuristic settings
    run_heuristic = True # False to only draw the Gantt diagram
    allow_unfinished_tasks = True
    sort_setup = True
    start_time = dtn_zeroed

    # Program settings
    progressbar = True
    debug_prints = False
    run_parallelized = True

settings = Settings()