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

def mark_row_complete(db_row):
    is_headers_complete = len(db_row["headers"]) == 10
    db_row["is_complete"] = is_headers_complete

def mark_item_complete(item):
    is_data_complete = len(item["data"]) == 13
    item["is_complete"] = is_data_complete

def stitch_lines(input_file):
    with open(input_file, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    cursor = peekable(lines)

    db = []
    i = 0
    is_item = False
    is_header = False
    # run through once collecting headers
    while cursor:
        line, i = next_(cursor, i)

        if cursor.peek("").startswith("QUANTITY"):
            # found a header line
            is_header = True
            is_item = False
            type_ = line
            row = make_db_row(type_)

            # all the possible headers
            line, i = next_(cursor, i)
            pattern = r"QUANTITY|UNIT|TAX|RCV|AGE/LIFE|COND\.|DEP %|DEPREC\.|ACV"
            other_headers = re.findall(pattern, line)
            headers = [type_] + other_headers
            # add to the db
            row["headers"] = headers
            mark_row_complete(row)
            db.append(row)

            print(f"{i}: HEADERS: {headers}")
        elif re.match(r"^\d+\. \w+", line):
            is_header = False
            is_item = True
            # found a new item
            item = make_item_row()
            # description
            item["desc"].append(line)

            # the next line is the other fields
            line, i = next_(cursor, i)
            segs = line.split(' ')
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
        elif is_item:
            # is hopefully another description line
            row = db[-1]
            item = row["items"][-1]
            item["desc"].append(line)
            print(f"{i}: ITEM_DESC: {item}")
        else:
            print(f"{i}: SKIPPED: {line}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_to_csv.py <filename>")
    else:
        stitch_lines(sys.argv[1])
