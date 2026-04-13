/* ============================================================
   DATABASE SETUP SCRIPT
   Project: Emotional Wellness Analytics Platform
   Author: Aakash Kushwah
   Purpose:
   Clean existing tables and create a structured database
   for the mental health questionnaire system.

   Tables Created:
   1. users
   2. categories
   3. questions
   4. responses
   5. scores
============================================================ */


/* ------------------------------------------------------------
STEP 1 — REMOVE OLD TABLES
This ensures we start from a completely clean database.
CASCADE removes dependent constraints automatically.
------------------------------------------------------------ */

DROP TABLE IF EXISTS responses CASCADE;
DROP TABLE IF EXISTS scores CASCADE;
DROP TABLE IF EXISTS questions CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS users CASCADE;



/* ------------------------------------------------------------
STEP 2 — USERS TABLE
Stores login credentials and demographic information.

user_id      : unique user identifier
username     : unique login name
password     : hashed password (bcrypt)
age          : demographic research field
gender       : demographic research field
country      : demographic research field
occupation   : demographic research field
created_at   : timestamp when account was created
------------------------------------------------------------ */

CREATE TABLE users (

    user_id SERIAL PRIMARY KEY,

    username TEXT UNIQUE NOT NULL,

    password TEXT NOT NULL,

    age INT,

    gender TEXT,

    country TEXT,

    occupation TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



/* ------------------------------------------------------------
STEP 3 — CATEGORIES TABLE
Stores psychological test categories.

Examples:
PHQ9
GAD7
PSS
Rosenberg
BigFive

Each category represents a questionnaire type.
------------------------------------------------------------ */

CREATE TABLE categories (

    category_id SERIAL PRIMARY KEY,

    category_name TEXT NOT NULL

);



/* ------------------------------------------------------------
STEP 4 — QUESTIONS TABLE
Stores every question belonging to a category.

Example:
PHQ9 question 1
PHQ9 question 2

category_id connects questions to the category table.
------------------------------------------------------------ */

CREATE TABLE questions (

    question_id SERIAL PRIMARY KEY,

    category_id INTEGER REFERENCES categories(category_id),

    question_text TEXT NOT NULL

);



/* ------------------------------------------------------------
STEP 5 — RESPONSES TABLE
Stores raw answers given by the user.

Each answer corresponds to one question.

answer_value values:
0 = Not at all
1 = Several days
2 = More than half the days
3 = Nearly every day
------------------------------------------------------------ */

CREATE TABLE responses (

    response_id SERIAL PRIMARY KEY,

    user_id INTEGER REFERENCES users(user_id),

    question_id INTEGER REFERENCES questions(question_id),

    answer_value INTEGER,

    response_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);



/* ------------------------------------------------------------
STEP 6 — SCORES TABLE
Stores calculated scores for each category.

Example:
User 5 → PHQ9 score = 18
User 5 → GAD7 score = 12

These scores power the dashboard analytics.
------------------------------------------------------------ */

CREATE TABLE scores (

    score_id SERIAL PRIMARY KEY,

    user_id INTEGER REFERENCES users(user_id),

    category_id INTEGER REFERENCES categories(category_id),

    score_value INTEGER,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);



/* ------------------------------------------------------------
STEP 7 — VERIFY TABLE CREATION
------------------------------------------------------------ */

SELECT * FROM users;
SELECT * FROM categories;
SELECT * FROM questions;
SELECT * FROM responses;
SELECT * FROM scores;