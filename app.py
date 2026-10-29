import os, re
from datetime import date, datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from models import db, Student, StudyRecord, Feedback, Recommendation, SubjectTask, StudyAllocation, ScheduleItem, RiskAssessment
from ml_model import predict_productivity, train_model
from services import calculate_productivity_score, analyze_patterns, generate_recommendations, build_study_plan, assess_risk, optimize_allocations, clamp, what_if_simulation

app=Flask(__name__); app.config.from_object(Config); db.init_app(app)
with app.app_context():
    db.create_all()
    # Upgrade legacy tables in-place for existing installations.
    inspector=db.inspect(db.engine)
    cols={c["name"] for c in inspector.get_columns("recommendation")}
    if "status" not in cols:
        try: db.session.execute(db.text("ALTER TABLE recommendation ADD COLUMN status VARCHAR(20) DEFAULT 'open'"))
        except Exception: db.session.rollback()
    db.session.commit()
    train_model()

NAME_RE=re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ]+(?:[ '\u2019-][A-Za-zÀ-ÖØ-öø-ÿ]+)*$")
EMAIL_RE=re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
def current_student():
    sid=session.get("student_id")
    return db.session.get(Student,sid) if sid else None
def login_required_student():
    student=current_student()
    if not student: flash("Please log in to continue."); return None
    return student

@app.route("/")
def home(): return render_template("home.html")

@app.route("/register",methods=["GET","POST"])
def register():
    if request.method=="POST":
        name=request.form.get("name","").strip(); email=request.form.get("email","").strip().lower()
        password=request.form.get("password",""); confirm=request.form.get("confirm_password","")
        errors=[]
        if not NAME_RE.fullmatch(name): errors.append("Name must contain letters and spaces; hyphens or apostrophes are allowed.")
        if not EMAIL_RE.fullmatch(email): errors.append("Enter a valid email address.")
        if len(password)<8 or not re.search(r"[A-Za-z]",password) or not re.search(r"\d",password): errors.append("Password must be at least 8 characters and include a letter and a number.")
        if password!=confirm: errors.append("Password and confirm password do not match.")
        if Student.query.filter_by(email=email).first(): errors.append("This email is already registered. Please log in.")
        if errors:
            for error in errors: flash(error,"error")
            return render_template("register.html",name=name,email=email)
        student=Student(name=name,email=email,password=generate_password_hash(password))
        try:
            db.session.add(student); db.session.commit()
        except Exception:
            db.session.rollback(); flash("Registration could not be completed. Please check the details and try again.","error")
            return render_template("register.html",name=name,email=email)
        session.clear(); session["student_id"]=student.id
        return redirect(url_for("dashboard"))
    return render_template("register.html")

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=request.form.get("email","").strip().lower(); password=request.form.get("password","")
        student=Student.query.filter_by(email=email).first()
        valid=False
        if student:
            try: valid=check_password_hash(student.password,password)
            except (ValueError,TypeError): valid=False
            # Legacy plaintext hashes are upgraded after successful login.
            if not valid and student.password==password:
                valid=True; student.password=generate_password_hash(password); db.session.commit()
        if valid:
            session.clear(); session["student_id"]=student.id
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.","error")
    return render_template("login.html")

@app.route("/logout",methods=["GET","POST"])
def logout(): session.clear(); return redirect(url_for("home"))

@app.route("/dashboard")
def dashboard():
    student=current_student()
    if not student:return redirect(url_for("login"))
    records=StudyRecord.query.filter_by(student_id=student.id).order_by(StudyRecord.study_date.asc()).all()
    score=calculate_productivity_score(records); pattern=analyze_patterns(records)
    recs=generate_recommendations(records,student,Feedback.query.filter_by(student_id=student.id).all())
    tasks=SubjectTask.query.filter_by(student_id=student.id).all()
    schedule=ScheduleItem.query.filter_by(student_id=student.id).all()
    risk=assess_risk(records,tasks=tasks,schedule=schedule)
    return render_template("dashboard.html",student=student,records=records,score=score,pattern=pattern,recommendations=recs,risk=risk)

@app.route("/record",methods=["GET","POST"])
def record():
    student=current_student()
    if not student:return redirect(url_for("login"))
    if request.method=="POST":
        try:
            vals={"study_hours":float(request.form["study_hours"]),"focus_minutes":int(request.form["focus_minutes"]),"breaks":int(request.form["breaks"]),"sleep_hours":float(request.form["sleep_hours"]),"screen_time":float(request.form["screen_time"]),"tasks_completed":int(request.form["tasks_completed"]),"tasks_planned":int(request.form["tasks_planned"]),"distraction_level":int(request.form["distraction_level"]),"mood":int(request.form["mood"])}
            limits={"study_hours":(0,24),"focus_minutes":(0,1440),"breaks":(0,50),"sleep_hours":(0,24),"screen_time":(0,24),"tasks_completed":(0,1000),"tasks_planned":(1,1000),"distraction_level":(0,10),"mood":(1,5)}
            for k,(lo,hi) in limits.items():
                if not lo<=vals[k]<=hi: raise ValueError(f"{k.replace('_',' ').capitalize()} must be between {lo} and {hi}.")
            if vals["tasks_completed"]>vals["tasks_planned"]: raise ValueError("Completed tasks cannot exceed tasks planned.")
            day=date.fromisoformat(request.form["study_date"])
            db.session.add(StudyRecord(student_id=student.id,study_date=day,**vals)); db.session.commit()
            flash("Study data saved and analytics updated.")
            return redirect(url_for("dashboard"))
        except (ValueError,KeyError) as e:
            db.session.rollback(); flash(str(e) or "Please enter valid study data.","error")
    return render_template("record.html")

@app.route("/prediction")
def prediction():
    student=current_student()
    if not student:return redirect(url_for("login"))
    latest=StudyRecord.query.filter_by(student_id=student.id).order_by(StudyRecord.study_date.desc()).first()
    value=predict_productivity(latest) if latest else None
    return render_template("prediction.html",prediction=value,latest=latest)
@app.route("/analytics")
def analytics():
    student=current_student()
    if not student:return redirect(url_for("login"))
    records=StudyRecord.query.filter_by(student_id=student.id).order_by(StudyRecord.study_date.asc()).all()
    return render_template("analytics.html",records=records,pattern=analyze_patterns(records),score=calculate_productivity_score(records))
@app.route("/simulator",methods=["GET","POST"])
def simulator():
    student=current_student()
    if not student:return redirect(url_for("login"))
    result=None
    if request.method=="POST":
        try:
            vals=[float(request.form[k]) for k in ["study_hours","focus_minutes","sleep_hours","screen_time","distraction_level"]]
            if vals[0]<0 or vals[0]>24 or vals[1]<0 or vals[1]>1440 or vals[2]<0 or vals[2]>24 or vals[3]<0 or vals[3]>24 or not 0<=vals[4]<=10: raise ValueError()
            result=what_if_simulation(*vals)
        except ValueError: flash("Enter valid values within the displayed ranges.","error")
    return render_template("simulator.html",result=result)
@app.route("/recommendations",methods=["GET","POST"])
def recommendations():
    student=current_student()
    if not student:return redirect(url_for("login"))
    if request.method=="POST":
        item=db.session.get(Recommendation,int(request.form.get("id",0)))
        if item and item.student_id==student.id and request.form.get("status") in ["helpful","not_helpful","completed","dismissed"]:
            item.status=request.form["status"]; item.accepted=item.status in ["helpful","completed"]; db.session.commit()
            flash("Recommendation feedback saved.")
        return redirect(url_for("recommendations"))
    records=StudyRecord.query.filter_by(student_id=student.id).all()
    recs=generate_recommendations(records,student,Feedback.query.filter_by(student_id=student.id).all())
    saved=Recommendation.query.filter_by(student_id=student.id).all()
    existing={x.recommendation:x for x in saved}
    visible=[]
    for text in recs:
        item=existing.get(text)
        if not item:
            item=Recommendation(student_id=student.id,recommendation=text,status="open"); db.session.add(item); db.session.flush()
        if item.status not in ("completed","dismissed"): visible.append(item)
    db.session.commit()
    return render_template("recommendations.html",recommendations=visible)
@app.route("/study-plan")
def study_plan():
    student=current_student()
    if not student:return redirect(url_for("login"))
    records=StudyRecord.query.filter_by(student_id=student.id).all()
    tasks=SubjectTask.query.filter_by(student_id=student.id).order_by(SubjectTask.deadline.asc()).all()
    schedule=ScheduleItem.query.filter_by(student_id=student.id).order_by(ScheduleItem.scheduled_date,ScheduleItem.start_time).all()
    plan = build_study_plan(records, student, schedule=schedule, tasks=tasks)
    return render_template("study_plan.html", plan=plan, tasks=tasks, schedule=schedule)
@app.route("/feedback",methods=["GET","POST"])
def feedback():
    student=current_student()
    if not student:return redirect(url_for("login"))
    if request.method=="POST":
        try: rating=int(request.form["rating"])
        except (ValueError,KeyError): rating=0
        if not 1<=rating<=5: flash("Rating must be between 1 and 5.","error")
        else:
            db.session.add(Feedback(student_id=student.id,recommendation=request.form.get("recommendation","").strip(),rating=rating,comment=request.form.get("comment","").strip()))
            db.session.commit(); flash("Feedback saved and will inform future recommendation priorities.")
            return redirect(url_for("dashboard"))
    return render_template("feedback.html")

@app.route("/optimizer",methods=["GET","POST"])
def optimizer():
    student=current_student()
    if not student:return redirect(url_for("login"))
    tasks=SubjectTask.query.filter_by(student_id=student.id).order_by(SubjectTask.deadline.asc()).all()
    allocations=[]
    if request.method=="POST":
        try:
            hours=float(request.form.get("available_hours","0"))
            if not 0<hours<=112: raise ValueError("Available hours must be greater than 0 and no more than 112 per week.")
            subject=request.form.get("subject","").strip(); taskname=request.form.get("task","").strip()
            if subject and taskname:
                difficulty=int(request.form.get("difficulty",3)); performance=float(request.form.get("performance",60)); priority=int(request.form.get("priority",3)); estimate=float(request.form.get("estimated_hours",1))
                if not 1<=difficulty<=5 or not 0<=performance<=100 or not 1<=priority<=5 or not .25<=estimate<=112: raise ValueError("Check difficulty, performance, priority, and estimated hours.")
                deadline=request.form.get("deadline") or None
                db.session.add(SubjectTask(student_id=student.id,subject=subject,task=taskname,deadline=date.fromisoformat(deadline) if deadline else None,difficulty=difficulty,performance=performance,priority=priority,estimated_hours=estimate))
                db.session.commit(); tasks=SubjectTask.query.filter_by(student_id=student.id).order_by(SubjectTask.deadline.asc()).all()
            result=optimize_allocations(tasks,hours)
            StudyAllocation.query.filter_by(student_id=student.id).delete()
            for entry in result: db.session.add(StudyAllocation(student_id=student.id,subject=entry["task"].subject,allocated_hours=entry["hours"],available_hours=hours))
            # Build/refresh future schedule without deleting completed sessions.
            start=datetime.strptime(request.form.get("start_time","18:00"),"%H:%M")
            cursor=start
            for entry in result:
                t=entry["task"]; mins=max(15,int(entry["hours"]*60))
                if not ScheduleItem.query.filter_by(student_id=student.id,subject=t.subject,task=t.task,status="completed").first():
                    db.session.add(ScheduleItem(student_id=student.id,subject=t.subject,task=t.task,scheduled_date=date.today(),start_time=cursor.strftime("%H:%M"),duration_minutes=mins,status="pending"))
                cursor += timedelta(minutes=mins+10)
            db.session.commit(); flash("Allocation saved and the study schedule updated.")
            allocations=result
        except (ValueError,TypeError) as e:
            db.session.rollback(); flash(str(e) or "Please enter valid optimizer values.","error")
    else:
        latest=StudyAllocation.query.filter_by(student_id=student.id).all()
        allocations=[{"task":next((t for t in tasks if t.subject==a.subject),None),"hours":a.allocated_hours,"subject":a.subject} for a in latest]
    return render_template("optimizer.html",tasks=tasks,allocations=allocations)

@app.route("/risk")
def risk():
    student=current_student()
    if not student:return redirect(url_for("login"))
    records=StudyRecord.query.filter_by(student_id=student.id).order_by(StudyRecord.study_date.asc()).all()
    tasks=SubjectTask.query.filter_by(student_id=student.id).all()
    schedule=ScheduleItem.query.filter_by(student_id=student.id).all()
    result=assess_risk(records,tasks=tasks,schedule=schedule)
    if result["score"] is not None:
        db.session.add(RiskAssessment(student_id=student.id,score=result["score"],category=result["category"],factors="; ".join(result["factors"]))); db.session.commit()
    history=RiskAssessment.query.filter_by(student_id=student.id).order_by(RiskAssessment.assessed_at.desc()).limit(10).all()
    return render_template("risk.html",risk=result,history=history)

@app.route("/schedule/update",methods=["POST"])
def schedule_update():
    student=current_student()
    if not student:return redirect(url_for("login"))
    item=db.session.get(ScheduleItem,int(request.form.get("item_id",0)))
    status=request.form.get("status")
    if item and item.student_id==student.id and status in ["completed","pending","missed"]:
        item.status=status; db.session.commit()
        if status=="missed":
            # Move missed work to tomorrow; preserve original row as history.
            db.session.add(ScheduleItem(student_id=student.id,subject=item.subject,task=item.task,scheduled_date=date.today()+timedelta(days=1),start_time=item.start_time,duration_minutes=item.duration_minutes,status="pending"))
            db.session.commit()
        flash("Schedule status updated.")
    return redirect(url_for("study_plan"))

@app.route("/api/chart-data")
def chart_data():
    student=current_student()
    if not student:return jsonify({"error":"login required"}),401
    records=StudyRecord.query.filter_by(student_id=student.id).order_by(StudyRecord.study_date.asc()).all()
    return jsonify({"dates":[str(r.study_date) for r in records],"scores":[calculate_productivity_score([r]) for r in records],"hours":[r.study_hours for r in records]})

if __name__=="__main__": app.run(debug=os.environ.get("FLASK_DEBUG","0")=="1")
