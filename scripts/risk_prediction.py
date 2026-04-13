# =============================================================
# RISK PREDICTION ENGINE
# Author: Aakash Kushwah
# =============================================================

import sys
import os
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.connection import get_connection

# -------------------------------------------------------------
# LOAD DATA
# -------------------------------------------------------------
conn = get_connection()

df = pd.read_sql("""
    SELECT user_id, category_id, score_value
    FROM scores
""", conn)

conn.close()

print("✅ Score data loaded.")

# -------------------------------------------------------------
# BUILD FEATURE MATRIX
# -------------------------------------------------------------
feature_df = df.pivot(
    index="user_id",
    columns="category_id",
    values="score_value"
).fillna(0)

# Simulated risk label: PHQ9 >= 15 → high risk
feature_df["risk_label"] = (feature_df.iloc[:, 0] >= 15).astype(int)

X = feature_df.drop(columns=["risk_label"])
y = feature_df["risk_label"]

# -------------------------------------------------------------
# TRAIN MODEL
# -------------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = LogisticRegression()
model.fit(X_train, y_train)

accuracy = model.score(X_test, y_test)
print(f"✅ Model trained. Accuracy: {accuracy:.2f}")


# -------------------------------------------------------------
# PREDICTION FUNCTION
# -------------------------------------------------------------
def predict_risk(user_scores: list) -> float:
    """
    Predicts depression risk probability.
    user_scores: list of scores in category_id order
    Returns: float between 0 and 1
    """
    probability = model.predict_proba([user_scores])[0][1]
    return probability