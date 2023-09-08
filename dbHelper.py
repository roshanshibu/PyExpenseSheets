import sqlite3 as sql
import config
import dateutil.parser as parser
from datetime import datetime

INCOME = "income"
EXPENSE = "expense"


class TransactionInfo:
    def __init__(self, date, name, income, expense, category):
        # print(f"{date}|{name}|{income}|{expense}|{category}")
        self.date = parser.parse(date)
        self.name = name
        self.transactionType = INCOME if len(income) > 0 else EXPENSE
        self.value = float(
            (income if len(income) > 0 else expense)[:-2].replace(",", "")
        )
        self.category = category


def execute(conn, sql_command, params=None, return_rows=False):
    """execute a given sql statement
    conn -> Connection object
    sql_command -> any sql statement
    params -> a tuple containing variables that can be plugged into the sql_command
    """
    ret = False
    try:
        c = conn.cursor()
        if params is None:
            c.execute(sql_command)
        else:
            c.execute(sql_command, params)

        ret = True
        if return_rows:
            rows = c.fetchall()
            return (ret, rows)
        return ret
    except sql.Error as e:
        print("SQL Error:: %s", str(e))
        ret = False
    except:
        print("Unexpected Error!")
        ret = False
    if return_rows:
        return (ret, None)
    return ret


def truncate_base_table():
    if execute(conn, "DELETE FROM base;"):
        if execute(conn, "DELETE FROM SQLITE_SEQUENCE WHERE name='base';"):
            conn.commit()
            return True
    return False


def insert_transaction_base_info(t_info):
    # insert an entry to table
    insert_into_base_sql = """
                                INSERT INTO base (Date, Name,
                                    Type, Value, 
                                    Category)
                                VALUES (?, ?, ?, ?, ?)
                            """
    insert_into_base_values_tup = (
        t_info.date,
        t_info.name,
        t_info.transactionType,
        t_info.value,
        t_info.category,
    )
    if execute(conn, insert_into_base_sql, insert_into_base_values_tup):
        conn.commit()
        return True
    else:
        return False


def insert_opening_balance(date, openingBalance):
    sql = """
                INSERT INTO base (Date, Name,
                    Type, Value, 
                    Category)
                VALUES (?, 'Opening Balance', 'openingBalance', ?, 'openingBalance')
            """
    data_tup = (parser.parse(date), openingBalance)
    if execute(conn, sql, data_tup):
        conn.commit()
        return True
    else:
        return False


def get_expense_categories():
    sql = f'SELECT DISTINCT Category FROM base WHERE Type="{EXPENSE}"'
    categories = execute(conn, sql, return_rows=True)
    return [category[0] for category in categories[1]]


def get_month_expenses(year=None, month=None, categories=None):
    # get expenses of a specific month and year
    # month value is a number (Jam = 1, Feb = 2 ...)
    # if no value is provided for month, the current month is used
    # if no value is provided for year, the current year is used
    sql = "SELECT Date, Name, Value, Category FROM base"

    # filter Year
    if year is None:
        year = datetime.now().year
    year = str(year)
    sql += f" WHERE strftime('%Y', Date) = '{year}'"

    # filter Month
    if month is None:
        month = datetime.now().month
    month = str(month)
    if int(month) < 10 and len(month) == 1:
        month = "0" + month
    sql += f" AND strftime('%m', Date) = '{month}'"

    # filter Categories
    if categories is not None:
        # check if the provided categories are valid categories from db
        if not all(c in get_expense_categories() for c in categories):
            raise ValueError("Category not found!")
        categoriesString = "','".join(categories)
        sql += f" AND Category IN ('{categoriesString}')"

    # Expenses only
    sql += f" AND Type = '{EXPENSE}'"

    expenses = execute(conn, sql, return_rows=True)
    return expenses[1]


def get_sum_of_expenses(categories, year=None, month=None):
    filteredExpenses = get_month_expenses(year=year, month=month, categories=categories)
    return sum(expesne[2] for expesne in filteredExpenses)


# create and connect to the db if not already present
database = config.DB_PATH
try:
    conn = sql.connect(database)
except sql.Error as e:
    print(
        f"Exception while creating/connecting to database file [{database}]:[{str(e)}]"
    )

# create table "base" if not already present
sql_create_base_table = """ CREATE TABLE IF NOT EXISTS base (
                                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                                    Date TEXT,
                                    Name TEXT,
                                    Type TEXT,
                                    Value REAL,
                                    Category TEXT
                                ); """

if not execute(conn, sql_create_base_table):
    print("Failed to create table [base]!")


# conn.close()
