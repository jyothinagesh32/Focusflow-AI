from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class StudyRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False, index=True)
    study_date = db.Column(db.Date, default=date.today)
    study_hours = db.Column(db.Float, nullable=False)
    focus_minutes = db.Column(db.Integer, nullable=False)
    breaks = db.Column(db.Integer, nullable=False)
    sleep_hours = db.Column(db.Float, nullable=False)
    screen_time = db.Column(db.Float, nullable=False)
    tasks_completed = db.Column(db.Integer, nullable=False)
    tasks_planned = db.Column(db.Integer, nullable=False)
    distraction_level = db.Column(db.Integer, nullable=False)
    mood = db.Column(db.Integer, nullable=False)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False, index=True)
    recommendation = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class Recommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False, index=True)
    recommendation = db.Column(db.Text, nullable=False)
    accepted = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default="open")
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class SubjectTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False, index=True)
    subject = db.Column(db.String(100), nullable=False)
    task = db.Column(db.String(200), nullable=False)
    deadline = db.Column(db.Date, nullable=True)
    difficulty = db.Column(db.Integer, nullable=False, default=3)
    performance = db.Column(db.Float, nullable=False, default=60)
    priority = db.Column(db.Integer, nullable=False, default=3)
    estimated_hours = db.Column(db.Float, nullable=False, default=1)
    status = db.Column(db.String(20), nullable=False, default="pending")
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class StudyAllocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False, index=True)
    subject = db.Column(db.String(100), nullable=False)
    allocated_hours = db.Column(db.Float, nullable=False)
    available_hours = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class ScheduleItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False, index=True)
    subject = db.Column(db.String(100), nullable=False)
    task = db.Column(db.String(200), nullable=False)
    scheduled_date = db.Column(db.Date, nullable=False, default=date.today)
    start_time = db.Column(db.String(5), nullable=False, default="18:00")
    duration_minutes = db.Column(db.Integer, nullable=False, default=30)
    status = db.Column(db.String(20), nullable=False, default="pending")
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

class RiskAssessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False, index=True)
    score = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(20), nullable=False)
    factors = db.Column(db.Text, nullable=False)
    assessed_at = db.Column(db.DateTime, server_default=db.func.now())
