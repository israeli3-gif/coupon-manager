import sqlite3
from datetime import datetime

# מתחברים למסד הנתונים הקיים
conn = sqlite3.connect('coupons.db')
cursor = conn.cursor()

try:
    # 1. מוסיפים את העמודה החדשה לטבלה
    cursor.execute("ALTER TABLE coupons ADD COLUMN used_date DATETIME")
    print("Column 'used_date' added successfully.")
except Exception as e:
    print("Note:", e)

# 2. מעדכנים את כל הקופונים שכבר נוצלו (is_active = 0) לתאריך של היום
now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
cursor.execute(f"UPDATE coupons SET used_date = '{now_str}' WHERE is_active = 0")

conn.commit()
conn.close()
print("Database updated! Old used coupons are set to today.")