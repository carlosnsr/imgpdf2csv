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
        status="incomplete"
    )

def make_db_row(type_):
    return dict(
        metadata=dict(type_=type_, status="incomplete"),
        # metadata
            # type_: Living, etc.
            # status: complete, incomplete
        header=dict(fields=[], status="incomplete"),
        # header
            # status: complete, incomplete
            # fields: []
                # expect X fields
                # if < X fields
                    # is incomplete
                    # if find a header later on, add it to the headers
        items=[],
        # items
            # each item:
                # description: array of strings
                # data: array of data segments
                # status:
                    # complete if len(data segments) matches X
                    # incomplete if < X
                        # if find an item field later on, add it to the items
        totals=""
    )

def stitch_lines(input_file):
    with open(input_file, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    cursor = peekable(lines)

    db = []
    i = 0
    is_item = False
    # run through once collecting headers
    while cursor:
        line, i = next_(cursor, i)

        if cursor.peek("").startswith("QUANTITY"):
            # found a header line
            is_item = False
            type_ = line
            row = make_db_row(type_)

            # all the possible headers
            line, i = next_(cursor, i)
            pattern = r"QUANTITY|UNIT|TAX|RCV|AGE/LIFE|COND\.|DEP %|DEPREC\.|ACV"
            other_headers = re.findall(pattern, line)
            headers = [type_] + other_headers
            # add to the db
            row["header"]["fields"] = headers
            if len(headers) == 10:
                row["header"]["status"] = "complete"
            db.append(row)

            print(f"{i}: HEADERS: {headers}")
        elif re.match(r"^\d+\. \w+", line):
            is_item = True
            # found a new item
            item = make_item_row()
            # description
            item["desc"].append(line)

            # the next line is the other fields
            line, i = next_(cursor, i)
            segs = line.split(' ')
            item["data"] = segs

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
