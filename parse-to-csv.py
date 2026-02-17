import csv
import re
import sys

def gen_headers(lines, start):
    metadata = { "state": "Header", "items": [] }
    section = lines[start]
    pattern = r"QUANTITY|UNIT|TAX|RCV|AGE/LIFE|COND\.|DEP %|DEPREC\.|ACV"
    others = re.findall(pattern, lines[start + 1])
    headers = [section] + others

    metadata["headers"] = headers
    return metadata

def parse_to_csv(input_file):
    with open(input_file, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    if len(lines) < 2:
        print("Error: File to short.  Does not contain data")
        return

    metadata = {}
    i = 1
    while i < len(lines):
        if i == 0:
            continue

        line = lines[i]
        if line.startswith("QUANTITY"):
            # found a header line
            metadata = gen_headers(lines, i - 1)
            headers = metadata["headers"]
            print(f"{i}: HEADERS: {headers}")
        elif re.match(r"^\d+\. ", line):
            # found an item, read in everything about it
            item = {}
            item["desc"] = [line]
            i += 1

            # the next line is the other fields
            line = lines[i]
            # pattern = r'\d+/\d+\s\w+|[A-Z][a-z]+\s[A-Z][a-z]+\.?|\[.*?\]|\(.*?\)|[\w\d\.]+%?'
            # item["segments"] = re.findall(pattern, line)
            segs = line.split(' ')
            item["segments"] = segs
            if len(segs) < 2:
                None
            else:
                item["price"] = f"{segs[0]} {segs[1]}"
            print(f"{i}: ITEM: {item}")
        else:
            print(f"{i}: SKIPPED: {line}")

        i += 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_to_csv.py <filename>")
    else:
        parse_to_csv(sys.argv[1])
