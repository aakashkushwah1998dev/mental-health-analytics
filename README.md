# 🧠 Mental Wellness Analytics System

An AI-powered Mental Health Analytics Platform that helps users assess, track, and understand their mental well-being through data-driven insights and personalized recommendations.

---

## 📌 Project Overview

This system allows users to:

- 🧾 Take scientifically inspired mental health assessments  
- 📊 View personalized dashboards and trends  
- 📈 Track emotional and psychological patterns over time  
- 🤖 Generate insights using data science and ML models  

---

## 🎯 Key Features

### 🔐 Authentication System
- Login & Registration  
- Session-based authentication  
- Secure user handling  

### 📝 Assessment Engine
- Dynamic questionnaire (PHQ9, GAD7, etc.)  
- Response storage  
- Score calculation per category  

### 📊 Dashboard
- Category-wise score visualization  
- Mental health trend analysis  
- Risk-level interpretation  

### 👤 User Profile
- Dynamic profile completion  
- Date of Birth → Age calculation  
- Personal data management  

### 💡 Recommendation Engine
- Personalized mental wellness suggestions  
- Based on score severity  

### 🤖 AI Risk Prediction (Advanced)
- Logistic Regression model  
- Predicts mental health risk probability  

---

## 🏗️ Tech Stack

| Layer        | Technology |
|-------------|-----------|
| Frontend    | Streamlit |
| Backend     | Python |
| Database    | PostgreSQL (Supabase) |
| Data Tools  | Pandas, NumPy |
| ML Model    | Scikit-learn |
| Auth Logic  | Custom Python Service |

---

## 📂 Project Structure

```bash
Mental-Health-Analytics/
│
├── app.py                         # Main entry point (landing + routing)
│
├── pages/                         # Streamlit multipage UI
│   ├── 1_Login.py                 # Login & registration
│   ├── 2_Dashboard.py             # Analytics dashboard
│   ├── 3_Questionnaire.py         # Assessment engine
│   ├── 4_Research_Info.py         # User profile & research info
│
├── database/                      # Database layer
│   └── connection.py              # PostgreSQL connection (via secrets)
│
├── auth/                          # Authentication logic
│   └── auth_service.py            # Login + register service
│
├── scripts/                       # Utility & backend scripts
│   ├── LoadQuestionsToDB.py       # Load questions from Excel
│   ├── Risk_Prediction.py         # ML model for risk prediction
│   ├── test_connection.py         # DB connection testing
│
├── data/                          # Dataset files
│   └── wellness_questions.xlsx    # Questionnaire dataset
│
├── .streamlit/                    # Streamlit configuration
│   └── secrets.toml               # DB credentials (DO NOT COMMIT)
│
├── requirements.txt               # Python dependencies
├── README.md                      # Project documentation
