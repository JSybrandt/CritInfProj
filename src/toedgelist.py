#!/usr/bin/env python3

import os
ROOT = "../"
TPTN_FILE = os.path.join(ROOT,
    "TransportationNetworks/chicago-regional/ChicagoRegional_net.tntp")
EDGE_FILE = os.path.join(ROOT,
    "data/chicago-regional.edges")

with open(TPTN_FILE) as in_file, open(EDGE_FILE, 'w') as out_file:
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

        from_node = int(tokens[0])
        to_node = int(tokens[1])
        edge_cap = float(tokens[2])
        edge_length = float(tokens[3])
        ftime = float(tokens[4])
        b = float(tokens[5])
        power = float(tokens[6])
        speed = float(tokens[7])
        toll = float(tokens[8])
        edge_type = float(tokens[9])

        out_file.write("{} {} {}\n".format(
            from_node, to_node, edge_length))

