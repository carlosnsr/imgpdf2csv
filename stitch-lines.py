import copy
import csv
import pprint
import re
import sys
from more_itertools import peekable

PRINT_ON = False
PRINT_ORPHANS = False
def print_(str):
    if PRINT_ORPHANS and "ORPHAN" in str and not "HEADER" in str:
        print(str)
        return
    if PRINT_ON:
        print(str)
    else:
        return

def next_(cursor, i):
    return (next(cursor), i + 1)

def make_item_row():
    return dict(
        desc=[],
        data=None,
        is_complete=False
    )

def make_db_row(title):
    return dict(
        title=title, # title: Living, etc.
        is_headers_complete=False,
        is_complete=False,
            # False if:
                # if len(headers) is not EXPECTED_HEADERS,
                # if len(any item) is not EXPECTED_DATA_SEGS
        headers=[],
        orphaned_headers=[],
        items=[],
            # each item:
                # description: array of strings
                # data: array of data segments
                # status:
                    # complete if len(data segments) matches EXPECTED_DATA_SEGS
                    # incomplete if < EXPECTED_DATA_SEGS
                        # if find an item field later on, add it to the items
        orphaned_data=[],
            # collection of orphan data items found when parsing the above items
                # optimistically grouped by tag
        totals=""
    )

def collect_orphans(orphans, data, line, i):
    # preserve the order of insertion for now
    orphans.append((data, (("LINE", line), ("LINE_#", i))))

def get_last_item(db, i):
    if not db:
        print(f"{i}: ERROR: no DB")
        return None

    row = db[-1]
    # could have been interrupted by a new header
    if not row["items"]:
        # print(f"{i}: INFO: interrupted by header")
        row = db[-2]

    if row["items"]:
        item = row["items"][-1]
        return item
    else:
        print(f"{i} ERROR: row[items] is empty")
        return None

EXPECTED_HEADERS = 10
EXPECTED_DATA_SEGS = 11 # 1 state enum, 9 actual data, 1 data line

def mark_row_complete(db_row):
    is_headers_complete = len(db_row["headers"]) == EXPECTED_HEADERS
    db_row["is_headers_complete"] = is_headers_complete
    db_row["is_complete"] = is_headers_complete

def mark_item_complete(item):
    is_data_complete = len(item["data"]) == EXPECTED_DATA_SEGS
    item["is_complete"] = is_data_complete

HEADER_RE = r"QUANTITY|UNIT|TAX|RCV|AGE/LIFE|COND\.|DEP %|DEPREC\.|ACV"
def extract_headers(line):
    return re.findall(HEADER_RE, line)

# Regexs to help process the data line
CURR_RE = r"\d+(?:,\d+)*\.\d+"
CRUFT_RE = r"[|_= —-]*"

QUANTITY_RE = rf"(?P<quan>{CURR_RE} EA)"
UNIT_RE = rf"(?P<unit>{CURR_RE})"
TAX_RE = rf"(?P<tax>{CURR_RE})"
RCV_RE = rf"(?P<rcv>{CURR_RE})"
AGEL_RE = rf"{CRUFT_RE}(?P<agel>\d+(?:\.\d+)*/(?:\d+ ?yrs|NA))"
COND_RE = rf"{CRUFT_RE}(?P<cond>New|Below Avg\.|Above Avg\.|Avg\.)"
DEP_RE = rf"(?P<dep>\d+(?:\.\d+)*%)"
DEPTAIL_RE = r"(?P<deptail>\[I?M\])"
DEPREC_RE = rf"(?P<deprec>\({CURR_RE}\))"
ACV_RE = rf"(?P<acv>{CURR_RE})"

MIN_RE = rf"{QUANTITY_RE} {UNIT_RE} {TAX_RE}"
TO_AGEL_RE = rf"{MIN_RE} {RCV_RE}\.? +{AGEL_RE}"
TO_COND_RE = rf"{TO_AGEL_RE} {COND_RE}"
FULL_RE = rf"{TO_COND_RE} {DEP_RE}\s+(?:{DEPTAIL_RE}\s*)?{DEPREC_RE} {ACV_RE}"

ALL_DATA_RE = None # gets set in extract_data
DEP_DATA_RE = None # gets set in extract_data
DATA_TAGS = ["quan", "unit", "tax", "rcv", "agel", "cond", "dep", "deptail", "deprec", "acv"]

def clean_ocr_issues(line):
    line = line.replace('[IM]', '[M]')
    line = re.sub(r"/[l\\] ?yrs", "/1 yrs", line)
    line = re.sub(r"/[S] ?yrs", "/5 yrs", line)
    line = re.sub(r"/S5 ?yrs", "/5 yrs", line)
    line = re.sub(r"[lI]/(\d+) ?yrs", r"1/\1 yrs", line)
    line = re.sub(r"[S]/(\d+) ?yrs", r"5/\1 yrs", line)
    line = re.sub(rf"yrs{CRUFT_RE} ?", r"yrs ", line)
    return line

def get_all_data_re():
    global ALL_DATA_RE

    if ALL_DATA_RE:
        return ALL_DATA_RE

    patterns = {
        "quan": QUANTITY_RE,
        "unit": UNIT_RE,
        "tax": TAX_RE,
        "rcv": RCV_RE,
        "agel": AGEL_RE,
        "cond": COND_RE,
        "dep": DEP_RE,
        "deptail": DEPTAIL_RE,
        "deprec": DEPREC_RE,
        "acv": ACV_RE
    }

    # combined, and each block is optional
    regex = ""
    for tag in DATA_TAGS:
        regex += rf"(?:{patterns[tag]}\s*)?"

    ALL_DATA_RE = regex

    return ALL_DATA_RE

def get_dep_data_re():
    global DEP_DATA_RE

    if DEP_DATA_RE:
        return DEP_DATA_RE

    patterns = {
        "dep": DEP_RE,
        "deptail": DEPTAIL_RE,
        "deprec": DEPREC_RE,
        "acv": ACV_RE
    }

    # combined, and each block is optional
    regex = ""
    dep_i = DATA_TAGS.index("dep")
    for tag in DATA_TAGS[dep_i:]:
        regex += rf"(?:{patterns[tag]}\s*)?"

    DEP_DATA_RE = regex

    return DEP_DATA_RE

def extract_data(line):
    line = clean_ocr_issues(line)
    data = None

    # handling dep's that confuse the unit/acv regex
    match = None
    data = None
    if re.match(DEP_RE, line):
        match = re.match(get_dep_data_re(), line)
        if match:
            data = match.groupdict()
    else:
        match = re.search(get_all_data_re(), line)
        if match:
            data = match.groupdict()

            # unit, tax, rcv, and acv all have the same regex
            # good news is that, unit is never on its own, it's always part of (quan, unit, tax)
            # so if no quantity, then unit is actually rcv or acv
            if data["quan"] is None and not data["unit"] is None:
                data["rcv_or_acv"] = data["unit"]
                data["unit"] = None

    if data:
        # Extract matches and filter out None values (missing fields)
        results = [(k, v) for k, v in data.items() if v is not None]
        return results

    return []

def process_data(line):
    line = clean_ocr_issues(line)
    m = re.search(FULL_RE, line)
    if m:
        dep = m.group("dep")
        if m.group("deptail"):
            dep = f"{dep} {m.group("deptail")}"

        return [
            "FULL",
            m.group("quan"),
            m.group("unit"),
            m.group("tax"),
            m.group("rcv"),
            m.group("agel"),
            m.group("cond"),
            dep,
            m.group("deprec"),
            m.group("acv"),
            ("LINE", line)
        ]

    m = re.search(TO_COND_RE, line)
    if m:
        return [
            "PART:COND",
            m.group("quan"),
            m.group("unit"),
            m.group("tax"),
            m.group("rcv"),
            m.group("agel"),
            m.group("cond"),
            ("LINE", line)
        ]

    m = re.search(TO_AGEL_RE, line)
    if m:
        return [
            "PART:AGEL",
            m.group("quan"),
            m.group("unit"),
            m.group("tax"),
            m.group("rcv"),
            m.group("agel"),
            ("LINE", line)
        ]

    m = re.search(MIN_RE, line)
    if m:
        return [
            "PART:MIN",
            m.group("quan"),
            m.group("unit"),
            m.group("tax"),
            ("LINE", line)
        ]

    return ["PART:NONE", ("LINE", line)]

def stitch_lines(input_file):
    with open(input_file, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    cursor = peekable(lines)

    db = []
    i = 0
    is_item = False
    skip = False
    orphans = []
    # run through once collecting headers
    while cursor:
        line, i = next_(cursor, i)

        if cursor.peek("").startswith("QUANTITY"):
            # found a header line

            # close out the current row (if any)
            if db:
                row = db[-1]
                # add orphans, then reset orphans
                row["orphaned_data"] = orphans
                print_(f"{i}: CLOSURE: {orphans}")
                orphans = []

            # is_item = False # an item could be interrupted by a header
            title = line
            row = make_db_row(title)

            # all the possible headers
            line, i = next_(cursor, i)
            headers = ["DESCRIPTION"] + extract_headers(line)
            # add to the db
            row["headers"] = headers
            mark_row_complete(row)
            db.append(row)

            print_(f"{i}: HEADERS: {headers}")
        elif re.match(r"^\d+\. \w+", line):
            # found a new item
            is_item = True
            item = make_item_row()
            # description
            item["desc"].append(line)

            # add to the most recent db row
            row = db[-1]
            row["items"].append(item)

            print_(f"{i}: ITEM:NEW: {item}")
        elif re.search(QUANTITY_RE, line):
            # this is the data line (pricing, etc.)
            # add it to the most recent item
            item = get_last_item(db, i)
            item["data"] = process_data(line)
            mark_item_complete(item)
            # print_(f"{i}: DATA:REGEX'D: {item["data"]}")
            # print_(f"{i}: DATA: {line}")

            print_(f"{i}: ITEM:DATA: {item}")
        elif line.startswith("Totals:"):
            # found a totals line
            is_item = False
            row = db[-1]
            row["totals"] = line

            print_(f"{i}: TOTALS: {line}")
        elif db:
            # is it another header?
            row = db[-1]
            headers = extract_headers(line)
            if headers:
                row["headers"].extend(headers)
                row["orphaned_headers"].extend(headers)
                mark_row_complete(row)
                print_(f"{i}: ORPHAN:HEADERS: {headers}")
                continue

            data = extract_data(line)
            if data:
                collect_orphans(orphans, data, line, i)
                print_(f"{i}: ORPHAN:EXTRACTED: {data} LINE: {line}")
                continue

            if is_item:
                # hopefully it's another description line
                item = get_last_item(db, i)
                if item:
                    item["desc"].append(line)
                    print_(f"{i}: ITEM:DESC: {item}")
                    continue
            elif line.startswith("Orig"):
                # deffo part of an item description
                is_item = True
                item = get_last_item(db, i)
                if item:
                    item["desc"].append(line)
                    print_(f"{i}: ITEM:DESC:ORIG: {item}")
                    continue

            skip = True
        else:
            skip = True

        if skip:
            print_(f"{i}: SKIPPED: {line}")
            skip = False

    return db

def select_incomplete_rows(db):
    incomplete_rows = []
    for row in db:
        # collect incomplete data, their headers, and their orphans
        incomplete_items = []
        for item in row["items"]:
            if not item["is_complete"]:
                incomplete_items.append(item)

        if incomplete_items:
            incomplete_rows.append(row)

    return incomplete_rows

def stitch_orphans(orphans):
    stitched = []
    if not orphans:
        return stitched
    # pprint.pprint(orphans)

    # flatten orphans, skipping all deptails
    flattened = [item for orphs, line in orphans for item in orphs if item[0] != "deptail"]

    # fix: unit and acv's can be confused for each other.  They only differ by their position
    # rcv_or_acv's that come after dep are definitely acv's
    # rcv_or_acv's that come before agel are definitely rcv's
    transformed = []
    after_deprec = False
    for tag, val in flattened:
        if not after_deprec and (tag == 'dep' or tag == 'deprec'):
            after_deprec = True

        if tag == 'rcv_or_acv':
            if after_deprec:
                transformed.append(('acv', val))
            else:
                transformed.append(('rcv', val))
        else:
            transformed.append((tag, val))
    flattened[:] = transformed

    tag0 = flattened[0][0]
    i0 = DATA_TAGS.index(tag0)

    while flattened:
        tag, _ = flattened[0]
        if tag == tag0:
            norph = []

        i = DATA_TAGS.index(tag)
        assert i == i0, f"Expect ({i}, {DATA_TAGS[i]}) to equal ({i0}, {tag0})"
        it = enumerate(flattened)
        for dtag in DATA_TAGS[i:]:
            if dtag == "deptail":
                norph.append((dtag, '[?]'))
                continue

            match = next(((mi, mitem) for mi, mitem in it if mitem[0] == dtag), None)
            if match:
                mi, (mtag, mval) = match
                # skip 'deptail' if is 'dep'
                if mtag == 'dep' and mval != '75%':
                    skip_next = True
                norph.append((mtag, mval))
                flattened[mi] = None

        stitched.append(norph)

        flattened = [item for item in flattened if item is not None]

    # print("stitched:")
    # pprint.pprint(stitched)
    # print("----------------------------------------")
    return stitched

EXTRA_HEADERS = ["DATA_STATUS", "LINE"]
def convert_to_csv(row):
    writer = csv.writer(sys.stdout)
    writer.writerow([f"Title: {row["title"]}"])

    assert row["is_headers_complete"], "Error: Headers aren't complete"
    assert len(row["headers"]) == EXPECTED_HEADERS, "Error: headers are missing"

    writer.writerow(row["headers"] + EXTRA_HEADERS)

    for item in row["items"]:
        description = " | ".join(item["desc"])

        data = item["data"]
        data_status = data[0]
        line = '"' + data[-1][1] + '"'
        fields = data[1:-1]

        writer.writerow([description] + fields + [data_status, line])

    return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_to_csv.py <filename>")
    else:
        db = stitch_lines(sys.argv[1])

        incomplete_rows = select_incomplete_rows(db)
        # pprint.pprint(incomplete_rows)

        for row in incomplete_rows:
            stitched = stitch_orphans(row["orphaned_data"])
            row["orphaned_data"] = stitched

        # pprint.pprint(db)

        row = db[0]
        # pprint.pprint(row)

        convert_to_csv(row)
