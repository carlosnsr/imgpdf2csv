import csv
import re
import sys
from more_itertools import peekable

def next_(cursor, i):
    return (next(cursor), i + 1)

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
        items=dict(rows=[], status="incomplete")
        # items
            # status: complete, incomplete
            # rows: []
                # expect X fields in each row
                # if < X fields
                    # is incomplete
                    # if find an item field later on, add it to the items
    )

def stitch_lines(input_file):
    with open(input_file, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    cursor = peekable(lines)

    db = []
    i = 0
    # run through once collecting headers
    while cursor:
        line, i = next_(cursor, i)

        if cursor.peek("").startswith("QUANTITY"):
            # found a header line
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
            # found a new item
            # description
            descriptions = [line]

            # the next line is the other fields
            line, i = next_(cursor, i)
            segs = line.split(' ')

            # add to the most recent db row
            item = [descriptions] + segs
            row = db[-1]
            row["items"]["rows"].append(item)

            print(f"{i}: ITEM: {item}")
        else:
            print(f"{i}: SKIPPED: {line}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_to_csv.py <filename>")
    else:
        stitch_lines(sys.argv[1])
