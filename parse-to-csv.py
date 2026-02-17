import csv
import re
import sys

def gen_headers(lines, start):
    section = lines[start]
    pattern = r"QUANTITY|UNIT|TAX|RCV|AGE/LIFE|COND\.|DEP %|DEPREC\.|ACV"
    others = re.findall(pattern, lines[start + 1])
    headers = [section] + others
    return headers

def parse_to_csv(input_file):
    with open(input_file, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    if len(lines) < 2:
        print("Error: File to short.  Does not contain data")
        return

    i = 1
    while i < len(lines):
        if i == 0:
            continue
        line = lines[i]

        if line.startswith("QUANTITY"):
            # found a header line
            headers = gen_headers(lines, i - 1)
            print(f"{i}: HEADERS: {headers}")
        else:
            print(f"{i}: {line}")

        i += 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_to_csv.py <filename>")
    else:
        parse_to_csv(sys.argv[1])
