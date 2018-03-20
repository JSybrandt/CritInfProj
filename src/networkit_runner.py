#!/usr/bin/env python3

ROOT = ".."
DATA = ROOT + "/data"
EDGE_LIST = DATA + "/chicago-regional.edges"
NODE_LOCS = DATA + "/chicago-regional.nodes.csv"

import networkit as nk
import matplotlib.pyplot as plt
import tempfile
import os

print("Loading Graph")

graph = nk.readGraph(EDGE_LIST,
                     nk.Format.EdgeList,
                     directed=True,
                     separator=" ",
                     firstNode=1,
                     commentPrefix="S",
                     continuous=False)

print("Profiling")
profile = nk.profiling.Profile.create(graph, preset="minimal")
os.makedirs(DATA+'/profile', exist_ok=True)
profile.output("HTML", DATA+"/profile")

print("Creating Centrality Measure")
pr = nk.centrality.PageRank(graph)
pr.run()

scores = pr.scores()

plt.hist(scores, 100)
plt.yscale('log')
plt.show()
