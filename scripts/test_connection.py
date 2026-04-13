# =============================================================
# DATABASE CONNECTION TEST
# Author: Aakash Kushwah
# =============================================================

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.connection import get_connection

conn = get_connection()

if conn:
    print("✅ Connection Successful")
    conn.close()
else:
    print("❌ Connection Failed")