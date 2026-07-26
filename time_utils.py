from datetime import datetime, timezone
from zoneinfo import ZoneInfo

WAT = ZoneInfo("Africa/Lagos")

def now_wat() -> datetime:
    return datetime.now(WAT)

def now_iso() -> str:
    return now_wat().isoformat()

def ts() -> float:
    return now_wat().timestamp()
