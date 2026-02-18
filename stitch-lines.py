import csv
import re
import sys
from more_itertools import peekable

def next_(cursor, i):
    return (next(cursor), i + 1)

def make_item_row():
    return dict(
        desc=[],
        data=None,
        is_complete=False
    )

def make_db_row(type_):
    return dict(
        type_=type_, # type_: Living, etc.
        is_headers_complete=False,
        is_complete=False,
            # False if:
                # if len(headers) is not 10,
                # if len(any item) is not X
        headers=[],
        items=[],
            # each item:
                # description: array of strings
                # data: array of data segments
                # status:
                    # complete if len(data segments) matches X
                    # incomplete if < X
                        # if find an item field later on, add it to the items
        totals=""
    )

EXPECTED_HEADERS = 10
HEADER_PATTERN = r"QUANTITY|UNIT|TAX|RCV|AGE/LIFE|COND\.|DEP %|DEPREC\.|ACV"
EXPECTED_DATA_SEGS = 13

def mark_row_complete(db_row):
    is_headers_complete = len(db_row["headers"]) == EXPECTED_HEADERS
    db_row["is_headers_complete"] = is_headers_complete
    db_row["is_complete"] = is_headers_complete

def mark_item_complete(item):
    is_data_complete = len(item["data"]) == EXPECTED_DATA_SEGS
    item["is_complete"] = is_data_complete

def extract_headers(line):
    return re.findall(HEADER_PATTERN, line)

QUANTITY_PATTERN = r"(?P<quan>\d+\.\d+ EA)"

def stitch_lines(input_file):
    with open(input_file, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    cursor = peekable(lines)

    db = []
    i = 0
    is_item = False
    skipped = False
    # run through once collecting headers
    while cursor:
        line, i = next_(cursor, i)

        if cursor.peek("").startswith("QUANTITY"):
            # found a header line
            # is_item = False # an item could be interrupted by a header
            type_ = line
            row = make_db_row(type_)

            # all the possible headers
            line, i = next_(cursor, i)
            headers = [type_] + extract_headers(line)
            # add to the db
            row["headers"] = headers
            mark_row_complete(row)
            db.append(row)

            print(f"{i}: HEADERS: {headers}")
        elif re.match(r"^\d+\. \w+", line):
            # found a new item
            is_item = True
            item = make_item_row()
            # description
            item["desc"].append(line)

            # add to the most recent db row
            row = db[-1]
            row["items"].append(item)

            print(f"{i}: ITEM: {item}")
        elif re.match(QUANTITY_PATTERN, line):
            # the next line is the other fields
            segs = line.split(' ')
            print(f"{i}: DATA: {line}")
            item["data"] = segs
            mark_item_complete(item)

            # add to the most recent db row
            row = db[-1]
            row["items"].append(item)

            print(f"{i}: ITEM: {item}")
        elif line.startswith("Totals:"):
            # found a totals line
            is_item = False
            row = db[-1]
            row["totals"] = line

            print(f"{i}: TOTALS: {line}")
        elif db:
            # is it another header?
            row = db[-1]
            headers = extract_headers(line)
            if headers:
                row["headers"].extend(headers)
                mark_row_complete(row)
                print(f"{i}: ORPHAN_HEADERS: {headers}")
            elif is_item:
                # hopefully it's another description line
                # but first check if it's an orphan
                if re.match(r"^\w+%", line):
                    is_item = False
                    print(f"{i}: BLIP: {line}")
                    continue

                # could have been interrupted by a new header
                if not row["items"]:
                    print(f"{i} INFO: interrupted by header")
                    row = db[-2]

                if row["items"]:
                    item = row["items"][-1]
                    item["desc"].append(line)
                    print(f"{i}: ITEM_DESC: {item}")
                else:
                    print(f"{i} ERROR: row[items] is empty")
                    skipped = True
            else:
                skipped = True
        else:
            skipped = True

        if skipped:
            print(f"{i}: SKIPPED: {line}")
            skipped = False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_to_csv.py <filename>")
    else:
        stitch_lines(sys.argv[1])
