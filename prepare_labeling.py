import csv

INPUT_FILE = "uncertainty_report.csv"
OUTPUT_FILE = "labeling.csv"


with open(
    INPUT_FILE,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:
    reader = csv.DictReader(f)
    rows = list(reader)

fieldnames = list(reader.fieldnames)

if "human_category" not in fieldnames:
    fieldnames.append("human_category")

if "label_note" not in fieldnames:
    fieldnames.append("label_note")

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8-sig",
    newline=""
) as f:
    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()

    for row in rows:
        row.setdefault("human_category", "")
        row.setdefault("label_note", "")
        writer.writerow(row)

print(f"Created: {OUTPUT_FILE}")
print(f"Articles: {len(rows)}")
print()
print("Next:")
print("Open labeling.csv and fill human_category.")