# Ananke

Ananke is a containerized web appliction wrapper that allows complete novices to experiment with ad-hoc Apache Spark clusters without
access to commercial cloud services. It's based on Klein, the implementation of Flask for Twisted. (Twisted flask, Klein Bottle, geddit?)
It also relies on websockets via Twisted/Autobahn.

The idea is that users launch the container, one of them presses the button to start a cluster and become the Spark Master. The application
returns an IP address that other users can use to join the cluster as Spark Workers. All nodes are informed of how many others are in the
cluster, and anyone can start a PySpark Jupyter Notebook against it. The owner of the Spark Master also has the option of starting HDFS.

[Here's an early video](https://youtu.be/9xsiV9dUlgI) of Ananke in action:
[![early pre-HDFS demo](https://img.youtube.com/vi/9xsiV9dUlgI/0.jpg)](https://youtu.be/9xsiV9dUlgI)



