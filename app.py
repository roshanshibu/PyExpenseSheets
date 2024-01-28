from utils import updateLocalDB
import dbHelper as db
import os
from google import auth

forceUpdate = False

if forceUpdate:
    try:
        updateLocalDB()
    except auth.exceptions.RefreshError:
        print("refreshing data...")
        os.remove("expenses.db")
        os.remove("token.json")
        updateLocalDB()

# print(db.get_expense_categories())

# get_month_expenses
# - month - optional (current month when empty), numeric value (eg: August = 8)
# - categories - optional (no filter by caregory applied when empty), a list of categories to filter by
# print(*db.get_month_expenses(month=4, categories=["Groceries", "Home"]), sep="\n")
# print(*db.get_month_expenses(month=4), sep="\n")  # all expenses from April
# print(*db.get_month_expenses(), sep="\n")  # all expenses of current month

# print(db.get_sum_of_expenses(year=2024, month=1, categories=["Groceries"]))

# print(*db.get_expense_trend_by_categories([]), sep="\n")
print(*db.get_expense_trend_by_categories(["Food & Drink"]), sep="\n")
# print(*db.get_expense_trend_by_categories(["Groceries", "Food & Drink"]), sep="\n")
