from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from init import getCreds
import config
import dbHelper as db

TRANSACTIONS = "transactions"
OPENING_BALANCE = "openingBalance"


# get all the sheets in the given spreadsheet
def getAllSheets():
    try:
        creds = getCreds()
        service = build("sheets", "v4", credentials=creds)
        spreadsheet = service.spreadsheets()
        result = spreadsheet.get(spreadsheetId=config.SPREADSHEET_ID).execute()
        return [
            {
                "id": sheet.get("properties").get("sheetId"),
                "title": sheet.get("properties").get("title"),
            }
            for sheet in result.get("sheets")
        ]

    except HttpError as err:
        print(err)


def readTransactions(sheetTitle):
    try:
        creds = getCreds()
        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()
        # get all transactions of the month ...
        # ... and also the opening balance
        result = (
            sheet.values()
            .batchGet(
                spreadsheetId=config.SPREADSHEET_ID,
                ranges=[
                    config.RANGE_NAME.replace("<SHEET_TITLE>", sheetTitle),
                    config.OPENING_BALANCE_CELL.replace("<SHEET_TITLE>", sheetTitle),
                ],
            )
            .execute()
        )
        ranges = result.get("valueRanges", [])
        transactions = []
        if "values" not in ranges[0]:
            print("No transactions found.")
        else:
            transactions = ranges[0]["values"]
        openingBalance = float(ranges[1]["values"][0][0][:-2].replace(",", ""))
        return {TRANSACTIONS: transactions, OPENING_BALANCE: openingBalance}
    except HttpError as err:
        print(err)


def writeToLocalDB():
    allSheets = getAllSheets()
    db.truncate_base_table()
    for sheet in allSheets:
        data = readTransactions(sheet["title"])

        if len(data[TRANSACTIONS]) == 0:
            print(f"No transactions in this sheet {sheet['title']}")
            continue

        db.insert_opening_balance(data[TRANSACTIONS][0][0], data[OPENING_BALANCE])
        for t in data[TRANSACTIONS]:
            t_info = db.TransactionInfo(t[0], t[1], t[2], t[3], t[4])
            db.insert_transaction_base_info(t_info)
