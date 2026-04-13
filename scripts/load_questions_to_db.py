# =============================================================
# LOAD QUESTIONS FROM EXCEL TO DATABASE
# Author: Aakash Kushwah
# =============================================================

import sys
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.connection import get_connection

# -------------------------------------------------------------
# LOAD EXCEL FILE
# -------------------------------------------------------------
file_path = os.path.join(os.path.dirname(__file__), "..", "data", "wellness_questions.xlsx")
excel_data = pd.ExcelFile(file_path)

conn = get_connection()
cursor = conn.cursor()

# -------------------------------------------------------------
# LOOP THROUGH SHEETS (each sheet = one category)
# -------------------------------------------------------------
for sheet_name in excel_data.sheet_names:

    df = excel_data.parse(sheet_name)

    print(f"Processing: {sheet_name}")

    # Insert category (skip if exists)
    cursor.execute("""
        INSERT INTO categories (category_name)
        VALUES (%s)
        ON CONFLICT (category_name) DO NOTHING
        RETURNING category_id
    """, (sheet_name,))

    result = cursor.fetchone()

    if result:
        category_id = result[0]
    else:
        cursor.execute(
            "SELECT category_id FROM categories WHERE category_name = %s",
            (sheet_name,)
        )
        category_id = cursor.fetchone()[0]

    # Insert questions
    for _, row in df.iterrows():
        question_text = str(row["QuestionText"]).strip()
        if question_text:
            cursor.execute("""
                INSERT INTO questions (category_id, question_text)
                VALUES (%s, %s)
            """, (category_id, question_text))

conn.commit()
cursor.close()
conn.close()

print("✅ All questions loaded successfully.")