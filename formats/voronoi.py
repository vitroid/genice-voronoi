# coding: utf-8
"""
Pyvoro (voro++) testing

1. Obtain the source files for python3 from github.

    git clone ....

2. Install it with special command. (I do not know the meaning.)
   ( https://github.com/joe-jordan/pyvoro/issues/13 )

    python setup.py build_ext -i

3. Prepare the link to pyvoro at the root folder of GenIce source.

	cd ~/github/GenIce; ln -s github/pyvoro/pyvoro .

4. Use genice.x at ~/github/GenIce.
"""

# system library
import sys
from collections import defaultdict
import colorsys
import logging
import pickle

# public library
import numpy as np
import pyvoro  # optional for genice.
import networkx as nx

# private library
import yaplotlib as yp
import graphstat
from graphstat import graphstat_sqlite3, graphstat_mysql
        

        

    
class myGraph(nx.Graph):
    def fromVoronoi(self, cell):
        voro_vertices = cell['vertices']
        origin        = cell['original']
        for f in cell['faces']:
            f_vertices = f['vertices']
            for i in range(len(f_vertices)):
                v1 = f_vertices[i]
                v2 = f_vertices[i-1]
                p1 = voro_vertices[v1]
                p2 = voro_vertices[v2]
                d = p1 - p2
                self.add_edge(v1,v2,length=np.linalg.norm(d))
        return self


def draw_cell(voro_cell, box, kind=0):
    layer = kind+2
    if layer > 30:
        layer = 30
    # draw frame
    s = yp.Layer(layer)
    s += yp.Color(0)
    origin     = voro_cell['original']
    voro_vertices = voro_cell['vertices']
    voro_faces    = voro_cell['faces']
    g = voro_cell['graph']
    for i,j in g.edges():
        di = voro_vertices[i] - origin
        dj = voro_vertices[j] - origin
        s += yp.Line(origin+di*0.9, origin+dj*0.9)
    # draw faces
    s += yp.Color(kind+10)
    for face in voro_faces:
        points = []
        for point in face['vertices']:
            d = voro_vertices[point] - origin
            points.append(d*0.89 + origin)
        s += yp.Polygon(points)
    return s

def progress(num,den):
    if int(num*10/den) != int((num+1)*10/den):
        logging.getLogger().info("{0}0%".format(int((num+1)*10/den)))

def cell_index(voro_cell):
    stat = defaultdict(int)
    for face in voro_cell['faces']:
        cyc = len(face['vertices'])
        stat[cyc] += 1
    return stat


def hook1(lattice):
    lattice.logger.info("Hook1: Voronoi tessellation test using pyvoro and voro++.")
    cellmat = lattice.repcell.mat * 10
    # simulation box must be orthogonal.
    assert cellmat[1,0] == 0 and cellmat[2,0] == 0 and cellmat[2,1] == 0
    positions = lattice.reppositions - np.floor(lattice.reppositions)
    cells = pyvoro.compute_voronoi(np.dot(positions, cellmat),
                                   [[0.0, cellmat[0,0]], [0.0, cellmat[1,1]], [0.0, cellmat[2,2]]],
                                   6.0, #block size, what is this?
                                   periodic=[True, True, True])
    # # how to specify that the lattice is periodic?

    #for c in cells:
    #    print(len(c['faces']))
    # Prepare the Voronoi vertex list from the cells

    box = np.diag(cellmat)
    if database is None:
        lattice.logger.info("  Using temporary database. (volatile)")
        gc = graphstat.GraphStat()
    elif database[:4] == "http":
        lattice.logger.info("  Using MySQL: {0}".format(database))
        gc = graphstat_mysql.GraphStat(database)
    else:
        lattice.logger.info("  Using local Sqlite3: {0}".format(database))
        import os.path
        create = not os.path.isfile(database)
        if create:
            lattice.logger.info("  Create new DB.")
        gc = graphstat_sqlite3.GraphStat(database, create=create)
    s = ""
    ncolors = 0
    colors = dict()
    count = defaultdict(int)
    ind   = dict()
    for cnt, cell in enumerate(cells):
        progress(cnt, len(cells))
        g = myGraph().fromVoronoi(cell)
        cell['graph'] = g
        id = gc.query_id(g)
        if id < 0:
            id = gc.register()
            lattice.logger.info("New polyhedron {0}".format(id))
        count[id] += 1
        if count[id] == 1:
            colors[id] = ncolors
            ncolors += 1
        ind[id]   = cell_index(cell)
        s += draw_cell(cell, box, kind=colors[id])

    ss = yp.RandomPalettes(ncolors,offset=10)
    s += "#\tcounts\tid\t"+"\t".join(["{0}".format(x) for x in range(3,11)])+"\n"
    for id in sorted(count, key=lambda x:count[x]):
        s += "#\t{0}\t{1}\t".format(count[id], id)
        cyc = ["{0}".format(ind[id][j]) for j in range(3,max(ind[id])+1)]
        s += "\t".join(cyc)+"\n"
    print(ss + s)
    # graphcollection
    # with open("graphdb", "wb") as file:
    #     pickle.dump(gc, file)
    lattice.logger.info("Hook1: end.")

def argparser(arg):
    global database
    database=arg
    # simplify = float(arg)
    
simplify = 0.0
database = None

hooks = {1:hook1}
