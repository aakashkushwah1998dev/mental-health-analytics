-- =============================================================
-- MENTAL HEALTH ANALYTICS DATABASE SETUP
-- Author: Aakash Kushwah
-- =============================================================

-- USERS
CREATE TABLE IF NOT EXISTS users (
    user_id     SERIAL PRIMARY KEY,
    username    TEXT UNIQUE NOT NULL,
    password    TEXT NOT NULL,
    age         INT,
    gender      TEXT,
    country     TEXT,
    occupation  TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CATEGORIES
CREATE TABLE IF NOT EXISTS categories (
    category_id   SERIAL PRIMARY KEY,
    category_name TEXT NOT NULL,
    description   TEXT,
    CONSTRAINT unique_category_name UNIQUE (category_name)
);

-- QUESTIONS
CREATE TABLE IF NOT EXISTS questions (
    question_id   SERIAL PRIMARY KEY,
    category_id   INTEGER,
    question_text TEXT NOT NULL,
    CONSTRAINT fk_category FOREIGN KEY (category_id)
        REFERENCES categories(category_id) ON DELETE CASCADE
);

-- RESPONSES
CREATE TABLE IF NOT EXISTS responses (
    response_id   SERIAL PRIMARY KEY,
    user_id       INTEGER,
    question_id   INTEGER,
    answer_value  INTEGER,
    response_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_resp_user     FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_resp_question FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE CASCADE
);

-- SCORES
CREATE TABLE IF NOT EXISTS scores (
    score_id    SERIAL PRIMARY KEY,
    user_id     INTEGER,
    category_id INTEGER,
    score_value INTEGER,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_score_user     FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_score_category FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE CASCADE
);

ALTER TABLE users
ADD COLUMN IF NOT EXISTS date_of_birth DATE;

-- Optional reset (only run if you WANT to clear old data)
TRUNCATE TABLE responses RESTART IDENTITY CASCADE;
TRUNCATE TABLE scores RESTART IDENTITY CASCADE;
TRUNCATE TABLE users RESTART IDENTITY CASCADE;

ALTER TABLE questions
ADD COLUMN IF NOT EXISTS is_reversed BOOLEAN DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS user_activity (
  activity_id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(user_id),
  login_count INT DEFAULT 0,
  last_login TIMESTAMP,
  total_assessments INT DEFAULT 0,
  last_assessment TIMESTAMP
);

CREATE TABLE IF NOT EXISTS assessment_attempts (
  attempt_id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(user_id),
  attempt_number INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  mood_label TEXT
);

ALTER TABLE responses ADD COLUMN IF NOT EXISTS attempt_id INT;
ALTER TABLE scores ADD COLUMN IF NOT EXISTS attempt_id INT;
