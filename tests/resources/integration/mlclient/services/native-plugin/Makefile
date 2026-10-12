MARKLOGIC ?= /opt/MarkLogic

all: mlclient-test-aggregates.zip

libmlclient-test-aggregates.so: Aggregates.cpp
	$(CXX) -std=c++11 -m64 -fPIC -O2 -Woverloaded-virtual -I$(MARKLOGIC)/include -shared -o $@ $<

mlclient-test-aggregates.zip: libmlclient-test-aggregates.so manifest.xml
	zip $@ $^
