#!/usr/bin/env python3

import os

ROOT = "../"

TPTN_FILE = os.path.join(ROOT,
    "TransportationNetworks/chicago-regional/ChicagoRegional_node.tntp")
NODE_FILE = os.path.join(ROOT,
    "data/chicago-regional.nodes.csv")

with open(TPTN_FILE) as in_file, open(NODE_FILE, 'w') as out_file:
    out_file.write("Id,X,Y\n")
    first = True
    for line in in_file:
        if first:
            first = False
            continue
        node, x, y = line.strip().split()
        x = float(x)
        y = float(y)
        out_file.write("{},{},{}\n".format(node, x, y))
