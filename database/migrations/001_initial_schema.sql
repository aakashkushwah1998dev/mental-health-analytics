-- =============================================================
-- Mental Health Analytics - Initial Production Schema
-- Safe, idempotent migration for Supabase/PostgreSQL
-- =============================================================

CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    user_code TEXT UNIQUE,
    age INT,
    gender TEXT,
    country TEXT,
    occupation TEXT,
    date_of_birth DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS categories (
    category_id SERIAL PRIMARY KEY,
    category_name TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS questions (
    question_id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES categories(category_id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    is_reversed BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS assessment_attempts (
    attempt_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    attempt_number INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    mood_label TEXT
);

CREATE TABLE IF NOT EXISTS responses (
    response_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    question_id INTEGER REFERENCES questions(question_id) ON DELETE CASCADE,
    answer_value INTEGER NOT NULL,
    response_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    attempt_id INT REFERENCES assessment_attempts(attempt_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS scores (
    score_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(category_id) ON DELETE CASCADE,
    score_value INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    attempt_id INT REFERENCES assessment_attempts(attempt_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_activity (
    activity_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    login_count INT DEFAULT 0,
    last_login TIMESTAMP,
    total_assessments INT DEFAULT 0,
    last_assessment TIMESTAMP
);

ALTER TABLE scores
DROP CONSTRAINT IF EXISTS scores_user_id_category_id_key;

ALTER TABLE scores
DROP CONSTRAINT IF EXISTS scores_attempt_id_category_id_key;

ALTER TABLE scores
ADD CONSTRAINT scores_attempt_id_category_id_key UNIQUE (attempt_id, category_id);

UPDATE users
SET user_code = 'USR' || LPAD(user_id::text, 6, '0')
WHERE user_code IS NULL;

CREATE INDEX IF NOT EXISTS idx_scores_user_attempt ON scores (user_id, attempt_id);
CREATE INDEX IF NOT EXISTS idx_attempts_user_created_at ON assessment_attempts (user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_responses_user_attempt ON responses (user_id, attempt_id);
