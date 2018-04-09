# coding: utf-8

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
import graphstat
from graphstat import graphstat_mysql
from graphstat import graphstat_sqlite3
        

        

    
class myGraph(nx.Graph):
    def remove_short_edges(self, minL):
        while True:
            processed = False
            for i,j,d in self.edges(data=True):
                if d['length'] < minL:
                    # print("merge",i,j,d)
                    new_node = self.merge_nodes([i,j])
                    processed = True
                    break
            if not processed:
                break
                    
    def merge_nodes(self,nodes):
        """
        from https://gist.github.com/Zulko/7629206
        Merges the selected `nodes` of the graph G into one `new_node`,
        meaning that all the edges that pointed to or from one of these
        `nodes` will point to or from the `new_node`.
        attr_dict and **attr are defined as in `G.add_node`.
        """
        i,j = nodes  # assume they are integers starting from zero.

        ni = self.neighbors(i)
        
        for k in ni:
            L = self[k][i]['length']
            if k != j:
                self.add_edge(j,k,length=L)
    
        self.remove_node(i)
        return j
    
    def fromVoronoi(self, cell, simplify=None):
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
        if simplify is not None:
            #print(voro_vertices - origin)
            rad = np.max(np.linalg.norm(voro_vertices - origin, axis=1))
            #print("rad",rad)
            thres = rad*simplify
            self.remove_short_edges(thres)
        return self



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
    global simplify, database
    lattice.logger.info("Hook1: Voronoi tessellation test using pyvoro and voro++.")
    cellmat = lattice.repcell.mat * 10
    # simulation box must be orthogonal.
    assert cellmat[1,0] == 0 and cellmat[2,0] == 0 and cellmat[2,1] == 0
    positions = lattice.reppositions - np.floor(lattice.reppositions)
    cells = pyvoro.compute_voronoi(np.dot(positions, cellmat),
                                   [[0.0, cellmat[0,0]], [0.0, cellmat[1,1]], [0.0, cellmat[2,2]]],
                                   6.0, #block size, what is this?
                                   periodic=[True, True, True])
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
        g = myGraph().fromVoronoi(cell, simplify=simplify)
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
        lattice.logger.debug("{0}:{1}".format(cnt,id))

    s += "#\tcounts\t%\tid\t"+"\t".join(["{0}".format(x) for x in range(3,11)])+"\n"
    for id in sorted(count, key=lambda x:count[x]):
        s += "#\t{0}\t{1:.03f}\t{2}\t".format(count[id],count[id]*100/len(cells),id)
        cyc = ["{0}".format(ind[id][j]) for j in range(3,max(ind[id])+1)]
        s += "\t".join(cyc)+"\n"
    print(s)
    lattice.logger.info("Hook1: end.")


def argparser(arg):
    global database
    database=arg
    # simplify = float(arg)
    
simplify = 0.0
database = None

hooks = {1:hook1}


if __name__ == "__main__":
    print("Unit test")
