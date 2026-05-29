"""Pure helpers for the task calendar view (Tk-free, testable)."""
import calendar
from collections import defaultdict
from typing import Dict, List


def month_matrix(year: int, month: int):
    """Return weeks as lists of day numbers (0 = padding), Monday-first."""
    return calendar.Calendar(firstweekday=0).monthdayscalendar(year, month)


def tasks_by_day(tasks, year: int, month: int) -> Dict[int, List]:
    """Group tasks whose due_date falls in (year, month) by day-of-month."""
    by_day = defaultdict(list)
    prefix = f"{year:04d}-{month:02d}-"
    for t in tasks:
        if t.due_date and t.due_date.startswith(prefix):
            try:
                day = int(t.due_date[8:10])
            except ValueError:
                continue
            by_day[day].append(t)
    return dict(by_day)


def prev_month(year: int, month: int):
    return (year - 1, 12) if month == 1 else (year, month - 1)


def next_month(year: int, month: int):
    return (year + 1, 1) if month == 12 else (year, month + 1)
