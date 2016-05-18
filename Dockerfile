FROM ubuntu:trusty

# https://arnesund.com/2015/09/21/spark-cluster-on-openstack-with-multi-user-jupyter-notebook/

#RUN apt-key adv --keyserver keyserver.ubuntu.com --recv E56151BF DISTRO=$(lsb_release -is | tr '[:upper:]' '[:lower:]') CODENAME=$(lsb_release -cs)

RUN apt-get clean && apt-get -q -y update

RUN DEBIAN_FRONTEND=noninteractive apt-get -q -y --fix-missing install \
    build-essential \
    curl \
    nano \
    openjdk-7-jdk \
    python-dev \
    python-pip \
    python3-dev \
    python3-pip \
    python-setuptools \
    screen \
    supervisor \
    wget 

RUN DEBIAN_FRONTEND=noninteractive apt-get -q -y --fix-missing install \
    libapr1-dev \
    libcurl4-nss-dev \
    libsasl2-dev \
    libsasl2-modules \
    libsvn-dev \
    maven    

# Packages needed to build Numpy, Sci-Kit Learn...        
RUN DEBIAN_FRONTEND=noninteractive apt-get -q -y --fix-missing install \                
        gfortran \
        gfortran-4.8 \
        libblas-dev \
        libblas3 \
        liblapack-dev \
        liblapack3 \
        libopenblas-base  
       
# Packages needed to build Matplotlib:        
RUN DEBIAN_FRONTEND=noninteractive apt-get -q -y --fix-missing install \
        libxft-dev \
        libpng-dev \
        libfreetype6-dev \
        pkg-config    
    
RUN curl -sL https://deb.nodesource.com/setup_6.x | sudo -E bash -    
RUN DEBIAN_FRONTEND=noninteractive apt-get -q -y install nodejs    
    
RUN npm install -g configurable-http-proxy    
   
RUN wget http://www.mirrorservice.org/sites/ftp.apache.org/spark/spark-1.6.1/spark-1.6.1-bin-hadoop2.6.tgz
RUN tar -xvzf spark-1.6.1-bin-hadoop2.6.tgz

RUN  wget http://www.apache.org/dist/mesos/0.28.1/mesos-0.28.1.tar.gz
RUN tar -zxf mesos-0.28.1.tar.gz
RUN rm mesos-0.28.1.tar.gz
RUN mkdir -p /mesos-0.28.1/build    
RUN cd /mesos-0.28.1/build && ../configure && make && make install

RUN wget http://mirror.catn.com/pub/apache/hadoop/common/hadoop-2.7.2/hadoop-2.7.2.tar.gz
RUN tar -zxf hadoop-2.7.2.tar.gz
RUN rm hadoop-2.7.2.tar.gz

RUN pip3 install jupyterhub
RUN pip3 install "ipython[notebook]"

RUN pip install py4j
RUN pip install "ipython[notebook]"

RUN pip3 install matplotlib
RUN pip3 install nltk
RUN pip3 install numpy
RUN pip3 install pandas        
RUN pip3 install scipy
RUN pip3 install scikit-learn        

#ADD kernals /usr/local/share/jupyter/kernels
#RUN python -m ipykernel.kernelspec

RUN ipython profile create pyspark
RUN jupyter notebook --generate-config

RUN DEBIAN_FRONTEND=noninteractive apt-get -q -y install libzmq3-dev

# https://github.com/Kronuz/pyScss/issues/308
ENV LC_CTYPE C.UTF-8

RUN pip3 install twisted
RUN pip3 install autobahn
RUN pip3 install PyZMQ
RUN pip3 install txZMQ
RUN pip3 install flask
RUN pip3 install requests

ADD scripts /usr/local/bin
ADD ananke /ananke

#ENV SPARK_HOME = /spark-1.6.1-bin-hadoop2.6

#Failed to load native Mesos library from /usr/java/packages/lib/amd64:/usr/lib/x86_64-linux-gnu/jni:/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu:/usr/lib/jni:/lib:/usr/lib
#/mesos-0.28.1/build/bin/mesos-slave.sh --master=172.17.0.2:5050 --launcher=posix
#export MESOS_NATIVE_JAVA_LIBRARY=/usr/local/lib/libmesos.so

# sudo docker run -ti --name jupyter --net=host -p 8888:8888 -p 5050:5050 ananke /bin/bash

CMD ["/bin/bash", "-c", "./spark_jupyter_standalone"]

# ./bin/mesos-master.sh --ip=127.0.0.1 --work_dir=/var/lib/mesos

