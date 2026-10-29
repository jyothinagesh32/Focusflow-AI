from statistics import mean
from datetime import date, timedelta
from ml_model import predict_features

# Configurable weights; factors are normalized to 0..100.
SCORE_WEIGHTS = {"completion": .25, "focus": .20, "sleep": .15, "distraction": .10, "screen": .05, "mood": .05, "study": .20}

def clamp(v, lo=0, hi=100):
    return max(lo, min(hi, float(v)))

def calculate_productivity_score(records):
    if not records: return None
    daily=[]
    for r in records:
        completion=clamp((max(0,r.tasks_completed)/max(1,r.tasks_planned))*100)
        focus=clamp(max(0,r.focus_minutes)/180*100)
        sleep=clamp(100-abs(8-max(0,r.sleep_hours))*20)
        distraction=clamp(100-max(0,r.distraction_level)*10)
        screen=clamp(100-max(0,r.screen_time)*5)
        mood=clamp(max(1,min(5,r.mood))*20)
        study=clamp(max(0,r.study_hours)/6*100)
        vals={"completion":completion,"focus":focus,"sleep":sleep,"distraction":distraction,"screen":screen,"mood":mood,"study":study}
        daily.append(sum(vals[k]*SCORE_WEIGHTS[k] for k in vals)/sum(SCORE_WEIGHTS.values()))
    return round(mean(daily),2)

def analyze_patterns(records):
    if not records: return {"best_focus_day":"No data","average_study_hours":0,"average_sleep":0,"average_distraction":0,"completion_rate":0,"trend":"No data"}
    ordered=sorted(records,key=lambda r:r.study_date or date.min)
    planned=sum(max(0,r.tasks_planned) for r in ordered); done=sum(max(0,r.tasks_completed) for r in ordered)
    scores=[calculate_productivity_score([r]) for r in ordered]
    delta=scores[-1]-scores[0]
    return {"best_focus_day":str(max(ordered,key=lambda r:r.focus_minutes).study_date),"average_study_hours":round(mean(r.study_hours for r in ordered),2),"average_sleep":round(mean(r.sleep_hours for r in ordered),2),"average_distraction":round(mean(r.distraction_level for r in ordered),2),"completion_rate":round(done/planned*100,2) if planned else 0,"trend":"Improving" if delta>2 else "Declining" if delta < -2 else "Stable","score_change":round(delta,2)}

def assess_risk(records, tasks=None, schedule=None):
    """Assess productivity risk from recent study records, subject tasks and timetable sessions."""
    tasks = tasks or []
    schedule = schedule or []
    ordered = sorted(records or [], key=lambda r: r.study_date or date.min)
    recent = ordered[-7:]
    factors, actions, components = [], [], []

    def status_rows(rows, label):
        completed = [x for x in rows if (getattr(x, "status", "") or "").strip().lower() == "completed"]
        pending = [x for x in rows if (getattr(x, "status", "") or "").strip().lower() == "pending"]
        missed = [x for x in rows if (getattr(x, "status", "") or "").strip().lower() == "missed"]
        if not rows:
            return
        total = len(rows)
        missed_rate = len(missed) / total * 100
        pending_rate = len(pending) / total * 100
        if missed:
            components.append(min(40, 12 + missed_rate * 0.35))
            names = [f"{getattr(x, 'subject', 'Subject')}: {getattr(x, 'task', 'Study task')}" for x in missed[:3]]
            factors.append(f"{len(missed)} {label} marked missed: " + ", ".join(names) + ".")
            actions.append(f"Recover missed {label.lower()} by rescheduling the most urgent item first and splitting it into smaller steps.")
        if pending_rate >= 70:
            components.append(min(25, pending_rate * 0.25))
            factors.append(f"{pending_rate:.0f}% of {label.lower()} are still pending.")
            actions.append(f"Prioritize the nearest deadline or next scheduled {label.lower()} and finish it before adding more work.")
        if not completed and pending:
            components.append(10)
            factors.append(f"No {label.lower()} have been marked completed yet.")
            actions.append("Start with one short task/session and update its status immediately after finishing.")

    if recent:
        # Assess available study records immediately; do not require 3 records
        # before showing a useful alert. Trend comparison is only possible with 6+.
        planned = sum(max(0, r.tasks_planned) for r in recent)
        done = sum(max(0, r.tasks_completed) for r in recent)
        completion = done / planned * 100 if planned else 50
        avg_sleep = mean(r.sleep_hours for r in recent)
        avg_study = mean(r.study_hours for r in recent)
        high_distraction = mean(r.distraction_level for r in recent)
        trend = (calculate_productivity_score(recent[-3:]) - calculate_productivity_score(recent[:3])) if len(recent) >= 6 else 0
        if completion < 60:
            components.append(min(40, (60 - completion) * 0.65))
            factors.append(f"Task completion in recent study records is {completion:.0f}%, below the 60% target.")
            actions.append("Reduce today's task list and finish the nearest deadline first.")
        if avg_sleep < 6.5:
            components.append(min(20, (6.5 - avg_sleep) * 8))
            factors.append(f"Average sleep is {avg_sleep:.1f} hours, which may affect focus.")
            actions.append("Aim for a consistent sleep routine and avoid late-night study overload.")
        if avg_study < 1.5:
            components.append(min(20, (1.5 - avg_study) * 12))
            factors.append(f"Average recorded study time is {avg_study:.1f} hours per day.")
            actions.append("Schedule one realistic focused study block each day and build gradually.")
        if trend < -5:
            components.append(min(25, abs(trend) * 1.2))
            factors.append("Recent productivity scores show a downward trend.")
            actions.append("Review recent changes and reduce the workload until your routine stabilizes.")
        if high_distraction >= 7:
            components.append(min(20, (high_distraction - 6) * 5))
            factors.append(f"Distraction level averages {high_distraction:.1f}/10.")
            actions.append("Try a 25-minute distraction-free study block with notifications off.")

    # Evaluate both sources independently so timetable risk is not ignored when subject tasks exist.
    status_rows(tasks, "subject tasks")
    status_rows(schedule, "timetable sessions")

    if not ordered and not tasks and not schedule:
        return {
            "score": None,
            "category": "Insufficient data",
            "factors": ["Add at least 3 study records or create tracked study tasks/sessions to calculate a risk indicator."],
            "actions": ["Record daily study activity or add tasks/timetable sessions to enable personalized risk alerts."]
        }

    score = round(clamp(sum(components)), 1)
    category = "High Risk" if score >= 60 else "Moderate Risk" if score >= 30 else "Low Risk"
    if not factors:
        factors = ["No strong warning signal was found in the available recent records and task statuses."]
    if not actions:
        actions = ["Maintain the current routine, update task statuses honestly, and review progress weekly."]
    return {"score": score, "category": category, "factors": factors, "actions": actions}

def generate_recommendations(records, student, feedback=None):
    if not records: return ["Start entering daily study data so FocusFlow AI can analyze your personal pattern."]
    recent=sorted(records,key=lambda r:r.study_date or date.min)[-7:]; latest=recent[-1]; recs=[]
    if latest.sleep_hours<7: recs.append("Sleep improvement: aim for a consistent 7–9 hour sleep window; recent sleep is below 7 hours.")
    if latest.distraction_level>=7: recs.append("Focus support: silence notifications and complete one 25-minute study block with your phone away.")
    if latest.study_hours<2: recs.append("Study consistency: schedule a realistic 45-minute session today, then build gradually.")
    if latest.tasks_planned and latest.tasks_completed/latest.tasks_planned<.6: recs.append("Task completion: choose the two highest-priority tasks and split each into smaller steps.")
    if mean(r.study_hours for r in recent)<2: recs.append("Time allocation: reserve a repeatable daily study window rather than relying on last-minute sessions.")
    if feedback:
        low=sum(1 for f in feedback if f.rating<=2); high=sum(1 for f in feedback if f.rating>=4)
        if low>high: recs.append("Feedback adaptation: previous advice was not consistently helpful; try smaller, more specific goals and rate the next suggestion.")
    if not recs: recs.append("Your recent indicators look balanced. Maintain your routine and review the weekly trend.")
    return recs

def build_study_plan(records, student, schedule=None, tasks=None):
    """Return separate, task-specific guidance for completed, pending and missed work."""
    schedule = schedule or []
    tasks = tasks or []
    recs = generate_recommendations(records, student)
    score = calculate_productivity_score(records) or 0
    focus_blocks = 2 if score < 50 else 3 if score < 70 else 4

    plan = [
        f"Your focus target: {focus_blocks} focused study block(s) of 25–50 minutes, based on your current productivity score ({score:.0f}/100)."
    ]

    # SubjectTask statuses are handled independently from timetable session statuses.
    task_completed = [t for t in tasks if (t.status or "").lower() == "completed"]
    task_pending = [t for t in tasks if (t.status or "").lower() == "pending"]
    task_missed = [t for t in tasks if (t.status or "").lower() == "missed"]

    if tasks:
        plan.append(f"SUBJECT TASKS — {len(task_completed)} completed, {len(task_pending)} pending, {len(task_missed)} missed.")
        for t in task_completed[:5]:
            plan.append(f"COMPLETED: '{t.task}' ({t.subject}) is finished. Keep it completed; move to your next priority.")
        ordered_pending = sorted(
            task_pending,
            key=lambda t: (t.deadline or date.max, -getattr(t, "priority", 3), t.subject, t.task)
        )
        for t in ordered_pending[:5]:
            deadline_text = f" Deadline: {t.deadline}." if t.deadline else ""
            plan.append(
                f"PENDING: Work on '{t.task}' ({t.subject}) next. Estimated time: "
                f"{getattr(t, 'estimated_hours', 1)} hour(s). Priority: {getattr(t, 'priority', 3)}."
                f"{deadline_text} Split it into small steps and mark it completed when done."
            )
        for t in task_missed[:5]:
            plan.append(
                f"MISSED: '{t.task}' ({t.subject}) needs recovery. Reschedule it, work for 20–25 minutes first, "
                "and update its status after you complete it."
            )
        if not task_pending and not task_missed:
            plan.append("All subject tasks are completed. Add your next learning goal to create a new task-specific plan.")

    session_completed = [s for s in schedule if (s.status or "").lower() == "completed"]
    session_pending = [s for s in schedule if (s.status or "").lower() == "pending"]
    session_missed = [s for s in schedule if (s.status or "").lower() == "missed"]

    if schedule:
        plan.append(f"TIMETABLE SESSIONS — {len(session_completed)} completed, {len(session_pending)} pending, {len(session_missed)} missed.")
        for s in session_completed[:5]:
            plan.append(
                f"COMPLETED SESSION: '{s.task}' ({s.subject}) on {s.scheduled_date} at {s.start_time} is done. "
                "Do not repeat it; continue with the next unfinished session."
            )
        ordered_sessions = sorted(session_pending, key=lambda s: (s.scheduled_date, s.start_time or "23:59"))
        for s in ordered_sessions[:5]:
            plan.append(
                f"PENDING SESSION: '{s.task}' ({s.subject}) is scheduled for {s.scheduled_date} at {s.start_time} "
                f"for {s.duration_minutes} minutes. Prepare the required materials and complete this session."
            )
        for s in session_missed[:5]:
            plan.append(
                f"MISSED SESSION: '{s.task}' ({s.subject}) from {s.scheduled_date} needs recovery. "
                "Use the rescheduled pending session and finish this work before adding extra sessions."
            )

    if not tasks and not schedule:
        plan.extend([
            "Morning: begin with one difficult subject while your energy is high.",
            "Afternoon: spend 30–45 minutes revising and practising questions.",
            "Evening: review what you learned and prepare tomorrow's top three tasks.",
            "Add subject tasks or timetable sessions to receive separate completed, pending and missed guidance."
        ])

    if recs:
        plan.append("PRODUCTIVITY GUIDANCE: " + recs[0])
    return plan

def optimize_allocations(tasks, available_hours):
    available=max(0,float(available_hours))
    pending=[t for t in tasks if t.status not in ("completed","dismissed")]
    if not pending or available<=0: return []
    weights=[]
    today=date.today()
    for t in pending:
        urgency=1.0
        if t.deadline:
            days=(t.deadline-today).days
            urgency=3.0 if days<=1 else 2.0 if days<=3 else 1.0 if days<=7 else .6
        weakness=max(.2,(100-clamp(t.performance))/100)
        weight=max(.1,t.priority)*(.5+max(1,min(5,t.difficulty))/5)*urgency*(.5+weakness)
        weights.append(weight)
    total=sum(weights)
    # Allocate in proportion to weighted priority, capped by estimated task demand.
    raw=[available*w/total for w in weights]
    allocations=[min(max(.25,t.estimated_hours),h) for t,h in zip(pending,raw)]
    used=sum(allocations)
    # distribute any unused capacity proportionally to unmet task estimates
    remaining=max(0,available-used)
    for i,t in enumerate(pending):
        add=min(remaining,max(0,t.estimated_hours-allocations[i]))
        allocations[i]+=add; remaining-=add
    # final scale guarantees total never exceeds available hours
    total_alloc=sum(allocations)
    if total_alloc>available and total_alloc:
        allocations=[x*available/total_alloc for x in allocations]
    return [{"task":t,"hours":round(h,2)} for t,h in zip(pending,allocations) if h>0]

def what_if_simulation(study_hours, focus_minutes, sleep_hours, screen_time, distraction_level):
    return round(clamp(predict_features([study_hours,focus_minutes,1,sleep_hours,screen_time,4,5,distraction_level,3])),2)
