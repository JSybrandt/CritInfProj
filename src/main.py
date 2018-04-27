#!/usr/bin/env python3

import pickle
import matplotlib as mpl
import numpy as np
from scipy.interpolate import griddata
from scipy.spatial import ConvexHull, Delaunay
from math import isnan
from colorsys import *
import networkit as nk
import networkx as nx
from copy import deepcopy

import tkinter as tk

from PIL import Image, ImageDraw

ANUGA_DATA = "../data/anuga_output_{}.pkl"
NODE_POS_DATA = "../data/chicago-regional.nodes.csv"
FLOW_DATA = "../TransportationNetworks/chicago-regional/ChicagoRegional_flow.txt"
NET_DATA = "../TransportationNetworks/chicago-regional/ChicagoRegional_net.tntp"
DATA_OUT = "../results/{}.pkl"


def interact():
    import code
    code.InteractiveConsole(locals=globals()).interact()


def in_hull(pt, hull):
    if not isinstance(hull, Delaunay):
        hull = Delaunay(hull)
    return hull.find_simplex(pt) >= 0


def loadFlows():
    edge2flow = {}
    with open(FLOW_DATA) as file:
        for line in file:
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
    return edge2flow


def loadNetData():
    edge2data = {}
    with open(NET_DATA) as file:
        for line in file:
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
            data = {
                "edge_cap" : float(tokens[2]),  # cars/h
                "edge_length" : float(tokens[3]),  # miles
                "fftime" : float(tokens[4]),  # free flow time
                "b" : float(tokens[5]),  # ?
                "power" : float(tokens[6]), # ?
                "speed" : float(tokens[7]),  # speed limit
                "toll" : float(tokens[8]),  # toll (cents) (mostly 0)
                "edge_type" : float(tokens[9]),
            }
            edge2data[(tail, head)] = data
    return edge2data


def loadNodePos():
    node2pos = {}
    with open(NODE_POS_DATA) as file:
        first = True
        for line in file:
            if first:
                first = False
                continue
            i, x, y = line.strip().split(',')
            i = int(i)
            x = float(x)
            y = float(y)

            node2pos[i] = (x, y)
    return node2pos


def getEffectedRoads(ts, net_data, node2pos, anuha_pkl, img=False):
    top_offset = (0, 0)
    top_scale = (1, 1)
    road_offset = (0.05, 0.1)
    road_scale = (1, 1)
    # top_offset = (0.05, 0)
    # top_scale = (1, 1)


    [lon, lat, z] = anuha_pkl[b'topo_data']
    flooded_centroids = anuha_pkl[b'wcs'][ts]

    hull = ConvexHull(flooded_centroids)
    flood_extent = flooded_centroids[hull.vertices,:]

    road_mins = (float("inf"), float("inf"))
    road_maxs = (0, 0)
    for i, pt in node2pos.items():
        road_mins = [min(a,b) for a,b in zip(road_mins, pt)]
        road_maxs = [max(a,b) for a,b in zip(road_maxs, pt)]
    road_diffs = [b-s for b,s in zip(road_maxs, road_mins)]
    print("Node Mins", road_mins)
    print("Node Diff", road_diffs)

    top_mins = (float("inf"), float("inf"))
    top_maxes = (float("-inf"), float("-inf"))
    for pt in zip(lon, lat):
        top_mins = [min(a,b) for a,b in zip(top_mins, pt)]
        top_maxes = [max(a,b) for a,b in zip(top_maxes, pt)]
    top_diffs = [b-s for b,s in zip(top_maxes, top_mins)]
    print("Top. Mins", top_mins)
    print("Top. Diff", top_diffs)

    if img:
        height_min = min(z)
        height_max = max(z)
        height_diff = height_max - height_min
        print("Height Min:", height_min)
        print("Height Max:", height_diff)

    img_size = (1500, 1000)
    print("Img Size:", img_size)

    if img:
        im = Image.new('RGBA', img_size, (255, 255, 255, 255))
        draw = ImageDraw.Draw(im)

    def scale(pt, mins, diffs):
        return [(i-m)/d for i,m,d in zip(pt, mins, diffs)]

    def roadPt2Img(pt):
        # regular to 0-1
        r_pt = scale(pt, road_mins, road_diffs)
        r_pt = scale(r_pt, road_offset, road_scale)
        # 0-1 to img (flipped)
        i_pt = [i*min(img_size) for i in r_pt]
        # unflip
        i_pt[1] = img_size[1] - i_pt[1]
        return tuple(i_pt)

    def topPt2Img(pt):
        # regular to 0-1
        t_pt = scale(pt, top_mins, top_diffs)
        t_pt = scale(t_pt, top_offset, top_scale)
        # 0-1 to img (flipped)
        i_pt = [i*s for i,s in zip(t_pt, img_size)]
        # unflip
        i_pt[1] = img_size[1] - i_pt[1]
        return tuple(i_pt)

    if img:
        # topology data in image space
        img_top_data = np.zeros((len(lon), 3))
        for i, (x, y, z) in enumerate(zip(lon, lat, z)):
            x, y = topPt2Img((x,y))
            img_top_data[i] = (x, y, z)

        img_grid = np.zeros((img_size[0]*img_size[1], 2))
        it = 0
        for i in range(img_size[0]):
            for j in range(img_size[1]):
                img_grid[it][0] = i
                img_grid[it][1 ]= j
                it += 1

        interpolated_top = griddata(img_top_data[:, :2],
                                    img_top_data[:, 2],
                                    img_grid,
                                    method="linear")

        print("Drawing Topology")
        for (x, y), t in zip(img_grid, interpolated_top):
            # brown ground color
            start_h = 245 # green
            end_h = 0 # brown
            h_diff = end_h - start_h

            dist2max = height_max - t
            percent = 1 - (dist2max / height_diff)
            h = int(start_h + percent * h_diff)

            color = tuple(int(x*255) for x in
                          hsv_to_rgb(h/255, 65/255, 59/255) + (0,))

            draw.point((x, y), color)

    # draw flooding
    img_extent = [topPt2Img(pt) for pt in flood_extent]
    if img:
        print("Draw flooding")
        draw.polygon(img_extent, fill=(0,0,255,0))

    # draw edges
    dell = Delaunay(img_extent)
    effected_edges = []
    for (a, b) in net_data:
        pt_a = roadPt2Img(node2pos[a])
        pt_b = roadPt2Img(node2pos[b])
        if in_hull(pt_a, dell) or in_hull(pt_b, dell):
            color = (255, 0, 0, 0)
            effected_edges.append((a, b))
        else:
            color = (0, 0, 0, 0)
        if img:
            draw.line(pt_a + pt_b, fill=color, width=2)

    if img:
        im.show()
    return effected_edges


def getAvgTravelTime(net_data, flows):
    print("Building graph")
    graph = nk.graph.Graph(0, weighted=True, directed=True)
    for (t, h), d in net_data.items():
        fftime = d['fftime']
        b = d['b']
        edge_flow = flows[(t, h)]
        edge_cap = d['edge_cap']
        power = d['power']
        time = fftime * (1 + b * (edge_flow / edge_cap) ** power)

        while not graph.hasNode(t) or not graph.hasNode(h):
            graph.addNode()

        graph.addEdge(t, h, time)

    print("getting conn comp, removing disconnected nodes")
    conn = nk.components.StronglyConnectedComponents(graph)
    conn.run()
    part = conn.getPartition()
    print(part.subsetSizes())
    deleted = []
    for s in part.getSubsetIds():
        mem = part.getMembers(s)
        if(len(mem) == 1):
            for m in mem:
                graph.removeNode(m)
                deleted.append(m)
                print(m)

    print("Getting dists")
    sp = nk.distance.APSP(graph)
    sp.run()

    s, c = (0, 0)
    diam = 0
    for i, dl in enumerate(np.array(sp.getDistances(), dtype=np.float64)):
        if i in deleted:
            continue
        dl[deleted] = 0
        s += float(np.sum(dl))
        diam = max(diam, np.max(dl))
        if s == float('inf'):
            print(i)
            print(dl)
            break
        c += len(dl) - len(deleted) - 1
    return ((s / c), diam)


if __name__=="__main__":
    make_img = False
    write = True
    net_data = loadNetData()
    node2pos = loadNodePos()
    flows = loadFlows()

    trials = ['high', 'med3', 'low']
    for trial in trials:

        with open(ANUGA_DATA.format(trial), 'rb') as file:
            anuha_pkl = pickle.load(file, encoding='bytes')


        times = []
        # times.append(getAvgTravelTime(net_data, flows))

        max_ts = 99
        for i in range(max_ts+1):
            print(i)
            eff_edges = getEffectedRoads(i, net_data, node2pos, anuha_pkl, make_img)

            effected_net = deepcopy(net_data)
            for e in eff_edges:
                effected_net[e]["edge_cap"] *= 0.5

            times.append(getAvgTravelTime(effected_net, flows))

        if write:
            with open(DATA_OUT.format(trial), 'wb') as file:
                pickle.dump(times, file)



    # top = tk.Tk()

    # off_x = tk.DoubleVar()
    # off_y = tk.DoubleVar()
    # scale_x = tk.DoubleVar()
    # scale_y = tk.DoubleVar()

    # def callback():
        # top_off = (off_x.get(), off_y.get())
        # top_scale = (scale_x.get(), scale_y.get())
        # getEffectedRoads(top_off, top_scale)

    # s1 = tk.Scale(top, from_=-1, to=1, resolution=0.01, variable=off_x)
    # s2 = tk.Scale(top, from_=-1, to=1, resolution=0.01, variable=off_y)
    # s3 = tk.Scale(top, from_=-1, to=2, resolution=0.01, variable=scale_x)
    # s4 = tk.Scale(top, from_=-1, to=2, resolution=0.01, variable=scale_y)

    # off_x.set(top_off[0])
    # off_y.set(top_off[1])
    # scale_x.set(top_scale[0])
    # scale_y.set(top_scale[1])

    # s1.pack(side=tk.LEFT)
    # s2.pack(side=tk.LEFT)
    # s3.pack(side=tk.LEFT)
    # s4.pack(side=tk.LEFT)

    # butt = tk.Button(top, text="Render", command=callback)
    # butt.pack(anchor=tk.CENTER)
    # top.mainloop()
