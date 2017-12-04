# Ananke

Ananke is a containerized web appliction wrapper that allows complete novices to experiment with ad-hoc
[Apache Spark](https://spark.apache.org/) clusters without
access to commercial cloud services. It's based on [Klein](http://klein.readthedocs.io/en/latest/), the implementation
of [Flask](http://flask.pocoo.org/) for [Twisted](https://twistedmatrix.com/trac/).
([Twisted Flask](http://www.kleinbottle.com/top_mouth_erlen_klein.htm), [Klein Bottle](http://www.kleinbottle.com/), geddit?)
It also relies on websockets via [Twisted](https://twistedmatrix.com/trac/)/[Autobahn](https://crossbar.io/autobahn/).

The idea is that users launch the container, one of them presses the button to start a cluster and become the Spark Master. The application
returns an IP address that other users can use to join the cluster as Spark Workers. All nodes are informed of how many others are in the
cluster, and anyone can start a PySpark Python3 Jupyter Notebook against it. The owner of the Spark Master also has the option of starting HDFS.

[Here's an early video](https://youtu.be/9xsiV9dUlgI) of Ananke in action:

[![early pre-HDFS demo](https://img.youtube.com/vi/9xsiV9dUlgI/0.jpg)](https://youtu.be/9xsiV9dUlgI)

You can either build the container with the `build.sh` script, or just do:

```
docker build -t ananke ./ananke
```

Then use `run.sh` which does:

```
docker run -ti --name ananke --net=host --pid=host -e TINI_SUBREAPER=true ananke

```

The app will be running at `http://localhost:5000`. Note that the container can be shipped in a VirtualBox appliance for the
hard-of-Docker, but this requires bridged networking mode, which won't work with eduroam, the spoil-sports.

Ananke was called into being to allow students on the
[Big Data in Practice](https://www.kcl.ac.uk/artshums/depts/ddh/study/pgt/modules-2017-18/core-modules/7AAVBCS3.aspx) module
at King's College London's [Department of Digital Humanities](https://www.kcl.ac.uk/artshums/depts/ddh/index.aspx) to play
with the
([amusingly](https://research.neustar.biz/2014/09/15/riding-with-the-stars-passenger-privacy-in-the-nyc-taxicab-dataset/)
[controversial](https://blogs.harvard.edu/infolaw/2014/11/21/the-antidote-for-anecdata-a-little-science-can-separate-data-privacy-facts-from-folklore/))
[New York taxi FOI data](http://www.nyc.gov/html/tlc/html/about/trip_record_data.shtml). A not-particularly small .gzipped sub-set of
the data and some tutorial notebooks are available [here](https://github.com/kingsBSD/NYC-Green-Cab-Data/blob/master/README.md).

The kitchen sink has been thrown in terms of the data science Python packages included:

- matplotlib
- nltk
- spacy
- numpy
- pandas
- scipy
- scikit-learn
- pyldavis
- lda
- gensim
- pyemd
- folium
- seaborn

NB: Ananke is also the [goddess](https://en.wikipedia.org/wiki/Ananke_(mythology)) of
necessity, see also: [constraint](https://en.wikipedia.org/wiki/Naudiz)