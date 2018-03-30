#!/usr/bin/env python3

import os

ROOT = "../"
TPTN_NET_FILE = os.path.join(ROOT,
    "TransportationNetworks/chicago-regional/ChicagoRegional_net.tntp")
TPTN_FLOW_FILE = os.path.join(ROOT,
    "TransportationNetworks/chicago-regional/ChicagoRegional_flow.txt")
EDGE_FILE = os.path.join(ROOT,
    "data/chicago-regional.edges")


edge2flow = {}

print("Loading flows")
with open(TPTN_FLOW_FILE) as in_file:
    for line in in_file:
        line = line.strip()
        if len(line) == 0:
            # skip, its empty
            continue
        if line[0] == '<':
            # skip, its metadata
            continue
        if line[0] == '~':
            # skip, its comment
            continue
        tokens = line.split()
        tail = int(tokens[0])
        head = int(tokens[1])
        flow = float(tokens[3])
        edge2flow[(tail, head)] = flow

print("Converting Network")
with open(TPTN_NET_FILE) as in_file, open(EDGE_FILE, 'w') as out_file:
    out_file.write("Source Target Weight\n")

    for line in in_file:
        line = line.strip()
        if len(line) == 0:
            # skip, its empty
            continue
        if line[0] == '<':
            # skip, its metadata
            continue
        if line[0] == '~':
            # skip, its comment
            continue
        tokens = line.split()

        tail = int(tokens[0])
        head = int(tokens[1])
        edge_cap = float(tokens[2])  # cars/h
        edge_length = float(tokens[3])  # miles
        fftime = float(tokens[4])  # free flow time
        b = float(tokens[5])  # ?
        power = float(tokens[6]) # ?
        speed = float(tokens[7])  # speed limit
        toll = float(tokens[8])  # toll (cents) (mostly 0)
        edge_type = float(tokens[9])

        flow = edge2flow[(tail, head)]

        travel_time = fftime * (1 + b * (flow / edge_cap) ** power)

        out_file.write("{} {} {}\n".format(tail, head, travel_time))
