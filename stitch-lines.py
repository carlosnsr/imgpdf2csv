import csv
import re
import sys

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

    db = []
    # run through once collecting headers
    i = 1 # The first line is the beginning of a headers
    while i < len(lines):
        line = lines[i]

        if line.startswith("QUANTITY"):
            # found a header line
            type_ = lines[i - 1]
            row = make_db_row(type_)

            # all the possible headers
            pattern = r"QUANTITY|UNIT|TAX|RCV|AGE/LIFE|COND\.|DEP %|DEPREC\.|ACV"
            other_headers = re.findall(pattern, lines[i])
            headers = [type_] + other_headers
            row["header"]["fields"] = headers
            if len(headers) == 10:
                row["header"]["status"] = "complete"

            print(f"{i}: HEADERS: {headers}")
        else:
            print(f"{i}: SKIPPED: {line}")
        i += 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_to_csv.py <filename>")
    else:
        stitch_lines(sys.argv[1])
