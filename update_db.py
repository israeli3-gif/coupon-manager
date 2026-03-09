import sqlite3

# מתחברים למסד הנתונים
conn = sqlite3.connect('coupons.db')
cursor = conn.cursor()

# מעדכנים את כל הרשתות לפורמט התקין (ה-Enum שלנו)
cursor.execute("UPDATE coupons SET company = 'Shufersal' WHERE company = 'shufersal'")
cursor.execute("UPDATE coupons SET company = 'Victory' WHERE company = 'victory'")
cursor.execute("UPDATE coupons SET company = 'Wolt' WHERE company = 'wolt'")
cursor.execute("UPDATE coupons SET company = 'BuyMe' WHERE company = 'buyme'")

# שומרים את השינויים וסוגרים
conn.commit()
conn.close()

print("Data cleansing complete! All companies are now capitalized correctly.")