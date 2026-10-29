import os
import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor

MODEL_PATH = "productivity_model.pkl"

def _make_training_data():
    rng = np.random.default_rng(42)
    X = []
    y = []
    for _ in range(1000):
        study = rng.uniform(0.5, 8)
        focus = rng.uniform(10, 240)
        breaks = rng.integers(0, 12)
        sleep = rng.uniform(4, 10)
        screen = rng.uniform(0, 10)
        completed = rng.integers(0, 10)
        planned = rng.integers(max(1, completed), 12)
        distraction = rng.integers(0, 11)
        mood = rng.integers(1, 6)

        completion = completed / planned * 100
        score = (
            min(study/6*100, 100)*0.20 +
            min(focus/180*100, 100)*0.20 +
            (100 if 7 <= sleep <= 9 else max(0, 100-abs(8-sleep)*20))*0.15 +
            max(0, 100-distraction*10)*0.15 +
            max(0, 100-screen*5)*0.10 +
            completion*0.15 +
            mood*20*0.05 +
            min(100, breaks*8)*0.00
        )
        score += rng.normal(0, 4)
        X.append([study, focus, breaks, sleep, screen, completed, planned, distraction, mood])
        y.append(max(0, min(100, score)))
    return np.array(X), np.array(y)

def train_model():
    if os.path.exists(MODEL_PATH):
        return
    X, y = _make_training_data()
    model = RandomForestRegressor(n_estimators=150, random_state=42)
    model.fit(X, y)
    joblib.dump(model, MODEL_PATH)

def predict_features(features):
    train_model()
    model = joblib.load(MODEL_PATH)
    return float(model.predict([features])[0])

def predict_productivity(record):
    if not record:
        return 0
    return round(predict_features([
        record.study_hours,
        record.focus_minutes,
        record.breaks,
        record.sleep_hours,
        record.screen_time,
        record.tasks_completed,
        record.tasks_planned,
        record.distraction_level,
        record.mood
    ]), 2)
