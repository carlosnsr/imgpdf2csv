import csv
import re
import sys

def stitch_lines(input_file):
    # db
        # metadata
            # type: Living, etc.
            # status: complete, incomplete
        # header
            # status: complete, incomplete
            # fields:
                # expect X fields
                # if < X fields
                    # is incomplete
                    # if find a header later on, add it to the headers
        # items
            # status: complete, incomplete
            # fields:
                # expect X columns
                # if < X columns
                    # is incomplete
                    # if find an item field later on, add it to the items
    with open(input_file, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    # run through collecting headers
    i = 1 # The first line is the beginning of a headers
    while i < len(lines):
        line = lines[i]
        print(f"{i}: SKIPPED: {line}")
        i += 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_to_csv.py <filename>")
    else:
        stitch_lines(sys.argv[1])
