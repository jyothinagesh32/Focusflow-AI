-- Run after selecting the existing focusflow_ai database. Existing tables/data are retained.
CREATE TABLE IF NOT EXISTS subject_task (
 id INT AUTO_INCREMENT PRIMARY KEY, student_id INT NOT NULL, subject VARCHAR(100) NOT NULL,
 task VARCHAR(200) NOT NULL, deadline DATE NULL, difficulty INT NOT NULL DEFAULT 3,
 performance FLOAT NOT NULL DEFAULT 60, priority INT NOT NULL DEFAULT 3,
 estimated_hours FLOAT NOT NULL DEFAULT 1, status VARCHAR(20) NOT NULL DEFAULT 'pending',
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, INDEX idx_task_student(student_id),
 FOREIGN KEY(student_id) REFERENCES student(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS study_allocation (
 id INT AUTO_INCREMENT PRIMARY KEY, student_id INT NOT NULL, subject VARCHAR(100) NOT NULL,
 allocated_hours FLOAT NOT NULL, available_hours FLOAT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 INDEX idx_allocation_student(student_id), FOREIGN KEY(student_id) REFERENCES student(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS schedule_item (
 id INT AUTO_INCREMENT PRIMARY KEY, student_id INT NOT NULL, subject VARCHAR(100) NOT NULL, task VARCHAR(200) NOT NULL,
 scheduled_date DATE NOT NULL, start_time VARCHAR(5) NOT NULL DEFAULT '18:00', duration_minutes INT NOT NULL DEFAULT 30,
 status VARCHAR(20) NOT NULL DEFAULT 'pending', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, INDEX idx_schedule_student(student_id),
 FOREIGN KEY(student_id) REFERENCES student(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS risk_assessment (
 id INT AUTO_INCREMENT PRIMARY KEY, student_id INT NOT NULL, score FLOAT NOT NULL, category VARCHAR(20) NOT NULL,
 factors TEXT NOT NULL, assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, INDEX idx_risk_student(student_id),
 FOREIGN KEY(student_id) REFERENCES student(id) ON DELETE CASCADE
);
ALTER TABLE recommendation ADD COLUMN status VARCHAR(20) DEFAULT 'open';
