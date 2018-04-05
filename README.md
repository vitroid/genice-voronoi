# genice-rdf

A [GenIce](https://github.com/vitroid/GenIce) plugin for Voronoi analysis.

## Requirements

* [GenIce](https://github.com/vitroid/GenIce) >=0.16.
* [graphstat](https://github.com/vitroid/graphstat) >=0.1. (Not PIP-ready.)
* [yaplotlib](https://github.com/vitroid/yaplotlib) >=0.1.
* mysqlclient

You have to setup MySQL database if you want to give a unique ID for graphs.

## Installation

### System-wide installation

Not supported.



### Private installation

    % make install
or copy the files in genice/formats into your local formats folder of GenIce.

## Usage

	% genice 1c -r 3 3 3 -f voronoi_analysis > 1c.voro
uses the temporary DB.

	% genice 1c -r 3 3 3 -f voronoi_analysis[voronoi.db] > 1c.voro
uses the local voronoi.db file via sqlite3.

	% genice 1c -r 3 3 3 -f voronoi_analysis[http://...] > 1c.voro
uses the global MySQL DB.

## Test in place

    % make test
