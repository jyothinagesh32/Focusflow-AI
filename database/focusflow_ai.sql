CREATE DATABASE IF NOT EXISTS focusflow_ai;
USE focusflow_ai;

CREATE TABLE IF NOT EXISTS student (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS study_record (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    study_date DATE,
    study_hours FLOAT NOT NULL,
    focus_minutes INT NOT NULL,
    breaks INT NOT NULL,
    sleep_hours FLOAT NOT NULL,
    screen_time FLOAT NOT NULL,
    tasks_completed INT NOT NULL,
    tasks_planned INT NOT NULL,
    distraction_level INT NOT NULL,
    mood INT NOT NULL,
    FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    recommendation TEXT NOT NULL,
    rating INT NOT NULL,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS recommendation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    recommendation TEXT NOT NULL,
    accepted BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE
);
