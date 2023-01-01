from datetime import datetime

dtn = datetime.now()
dtn_zeroed = datetime(dtn.year, dtn.month, dtn.day)

class Settings:
    instance = [1]
    days = 5
    run_heuristic = True # False to only draw the Gantt diagram
    allow_unfinished_tasks = True
    debug_prints = False
    start_time = dtn_zeroed

settings = Settings()