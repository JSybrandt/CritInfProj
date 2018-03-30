#!/usr/bin/env python2
import os
import sys
import numpy as np
import scipy
import scipy.spatial
import scipy.interpolate
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors
import pickle

def flood_fill(i,j,f0):
  f1 = np.zeros(f0.shape,dtype='bool')
  stack = set(((i, j),))
  while stack:
    i,j = stack.pop()
    if f0[i,j]:
      f1[i,j]=True
      neighbors = [ [i+1,j+1],
                    [i+1,j+0],
                    [i+1,j-1],
                    [i+0,j-1],
                    [i-1,j-1],
                    [i-1,j+0],
                    [i-1,j+1],
                    [i+0,j+1] ]
      for ni,nj in neighbors:
        if ni>0 and ni<f0.shape[0]:
          if nj>0 and nj<f0.shape[1]:
            if f1[ni,nj]==False:
              stack.add((ni,nj))
  return f1

output = pickle.load(open('../data/anuga_output.pkl','rb'))

[lon,lat,z]  = output['topo_data']		# lon and lat are in degrees, z is elevation in meters
xy           = output['xy']			# x,y locations (in meters) for the verticces
wcs          = output['wcs']			# list of arrays, one per timestep,
						# showing centroids of wet triangles
z0 = 597.0 / 3.28084

X = np.reshape(lon, [len(np.unique(lat)),len(np.unique(lon))])
Y = np.reshape(lat, [len(np.unique(lat)),len(np.unique(lon))])
Z = np.reshape(z,   [len(np.unique(lat)),len(np.unique(lon))])

f0 = (z0+0)>Z
f1 = flood_fill(30,130,f0)

for i in range(len(wcs)):

  print 'Plotting timestep %i of %i' % (i+1,len(wcs))

  hull = scipy.spatial.ConvexHull(wcs[i])
  flood_extent = wcs[i][hull.vertices,:]

  plt.figure()
  sc=plt.scatter(lon,lat,s=10,c=z,cmap='terrain',edgecolor='none')
  cl=plt.contour(X,Y,f1, [0.5], zorder=1)
  plt.scatter(wcs[i][:,0],wcs[i][:,1],s=10,c='b',edgecolor='none')
  plt.colorbar(sc)
  plt.savefig('../data/flood_img/chicago_flood_ts%02i.png'%i,format='png',bbox_inches='tight')
  plt.close()
