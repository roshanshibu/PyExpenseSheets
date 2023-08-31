from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from init import getCreds
import config
import dbHelper as db


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
        result = (
            sheet.values()
            .get(
                spreadsheetId=config.SPREADSHEET_ID,
                range=config.RANGE_NAME.replace("<SHEET_TITLE>", sheetTitle),
            )
            .execute()
        )
        values = result.get("values", [])
        if not values:
            print("No data found.")

        # for row in values:
        #     print(f"{row[0]}, {row[1]}, {row[2]}, {row[3]}, {row[4]}")
        return values
    except HttpError as err:
        print(err)


def writeToLocalDB():
    allSheets = getAllSheets()
    db.truncate_base_table()
    for sheet in allSheets:
        transactions = readTransactions(sheet["title"])
        for t in transactions[1:]:
            t_info = db.TransactionInfo(t[0], t[1], t[2], t[3], t[4])
            db.insert_transaction_base_info(t_info)
