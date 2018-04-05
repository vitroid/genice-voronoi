.DELETE_ON_ERROR:
OS=$(shell uname)
ifeq ($(OS), Darwin)
	DEST=~/Library/Application\ Support/GenIce
else
	DEST=~/.genice
endif

test: CS1.voro.yap 6.voro.stat
%.voro.yap: formats/voronoi.py Makefile
	genice $*     -f voronoi[test.db] > $@
%.voro.stat: formats/voronoi_analysis.py Makefile
	genice $* -r 2 2 2 -f voronoi_analysis > $@
prepare: # might require root privilege.
	pip install genice yaplotlib mysqlclient # graphstat
install:
	install -d $(DEST)
	install -d $(DEST)/formats
	install formats/*py $(DEST)/formats
clean:
	-rm $(ALL) *.so *~ */*~ */*/*~ *.o *.yap *stat test.db
	-rm -rf */__pycache__
