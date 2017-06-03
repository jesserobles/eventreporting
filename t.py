import csv
data = []
tmp = '{}::{}::{}'
with open('dockets', 'r') as file:
    reader = csv.reader(file)
#    rows = [line.strip() for line in file]
    for r in reader:
        docket, name, ftype = r
        print(tmp.format(docket, name, ftype))