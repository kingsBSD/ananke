export SPARK_HOME=/spark-2.1.0-bin-hadoop2.7
export PYTHONPATH=$SPARK_HOME/python:$SPARK_HOME/python/lib/py4j-0.10.4-src.zip
export PYSPARK_PYTHON=/usr/bin/python3.5
export PYSPARK_DRIVER_PYTHON=jupyter
export PYSPARK_DRIVER_PYTHON_OPTS='notebook --port 8888 --ip=0.0.0.0 --no-browser --NotebookApp.token=""'
