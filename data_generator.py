import csv
import json
from collections import defaultdict

csv_file = "summary.csv"
locations = "location_data.json"
output_file = "route_data.json"



with open(locations, "r") as f:
    areas = json.load(f)

airport_to_area = {}
for area in areas:
    for code in area["code"]:
        airport_to_area[code] = area["name"]

data = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

with open(csv_file, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        year = row["year"]
        org = row["org_airport"]
        dest = row["dest_airport"]
        passengers = int(row["total_passengers"])

        if org not in airport_to_area or dest not in airport_to_area:
            continue

        org_area = airport_to_area[org]
        dest_area = airport_to_area[dest]

        if org_area == dest_area:
            continue 

        data[year][org_area][dest_area] += passengers # used to geen route_data

with open(output_file, "w") as f:
    json.dump(data, f, indent=4, sort_keys=True)

print("done")
