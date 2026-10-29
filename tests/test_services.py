from datetime import date
from types import SimpleNamespace
from services import calculate_productivity_score, assess_risk, optimize_allocations

def record(day, hours=2, focus=90, sleep=7, completed=4, planned=5, distraction=3):
    return SimpleNamespace(study_date=day, study_hours=hours, focus_minutes=focus, breaks=2,
        sleep_hours=sleep, screen_time=2, tasks_completed=completed, tasks_planned=planned,
        distraction_level=distraction, mood=3)

def test_score_is_bounded_and_deterministic():
    r=record(date.today())
    assert calculate_productivity_score([r]) == calculate_productivity_score([r])
    assert 0 <= calculate_productivity_score([r]) <= 100

def test_missing_records_have_no_fake_score():
    assert calculate_productivity_score([]) is None

def test_risk_needs_enough_records():
    assert assess_risk([record(date.today())])["score"] is None

def test_optimizer_never_exceeds_available_hours():
    tasks=[SimpleNamespace(status="pending",deadline=None,performance=40,difficulty=5,priority=5,estimated_hours=10,subject="A",task="A"),
           SimpleNamespace(status="pending",deadline=None,performance=80,difficulty=2,priority=2,estimated_hours=10,subject="B",task="B")]
    allocations=optimize_allocations(tasks,3)
    assert sum(a["hours"] for a in allocations) <= 3.00001
