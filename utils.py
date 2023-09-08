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


def readTransactions(sheetTitles):
    try:
        creds = getCreds()
        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()
        # get all transactions of the month
        # and also the opening balance
        # in a single api call
        result = (
            sheet.values()
            .batchGet(
                spreadsheetId=config.SPREADSHEET_ID,
                ranges=[
                    range
                    for rangeTuple in [
                        (
                            config.RANGE_NAME.replace("<SHEET_TITLE>", sheet["title"]),
                            config.OPENING_BALANCE_CELL.replace(
                                "<SHEET_TITLE>", sheet["title"]
                            ),
                        )
                        for sheet in sheetTitles
                    ]
                    for range in rangeTuple
                ],
            )
            .execute()
        )
        ranges = iter(result.get("valueRanges", []))
        all_transactions = []
        for dataRange in ranges:
            t = {}
            transactionDataRange = dataRange
            openingBanlanceDataRange = next(ranges)

            t[OPENING_BALANCE] = float(
                openingBanlanceDataRange["values"][0][0][:-2].replace(",", "")
            )

            if "values" not in transactionDataRange:
                t[TRANSACTIONS] = []
                print(f"No transaction in sheet and range: {dataRange['range']}")
            else:
                t[TRANSACTIONS] = transactionDataRange["values"]

            all_transactions.append(t)

        return all_transactions
    except HttpError as err:
        print(err)


def updateLocalDB():
    allSheets = getAllSheets()
    db.truncate_base_table()

    allTransactions = readTransactions([sheet for sheet in allSheets])

    for data in allTransactions:
        if len(data[TRANSACTIONS]) == 0:
            print(f"No transactions in this sheet {data}. Skipping...")
            continue

        db.insert_opening_balance(data[TRANSACTIONS][0][0], data[OPENING_BALANCE])
        for t in data[TRANSACTIONS]:
            t_info = db.TransactionInfo(t[0], t[1], t[2], t[3], t[4])
            db.insert_transaction_base_info(t_info)
