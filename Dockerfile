FROM ubuntu:xenial

RUN apt-get clean && apt-get -q -y update

RUN DEBIAN_FRONTEND=noninteractive apt-get -q -y --fix-missing install \
    build-essential \
    curl \
    nano \
    openjdk-8-jdk \
    python-dev \
    python-pip \
    python3-dev \
    python3-pip \
    python-setuptools \
    screen \
    supervisor \
    wget 

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
    
RUN curl -sL https://deb.nodesource.com/setup_6.x | bash -    
RUN DEBIAN_FRONTEND=noninteractive apt-get -q -y install nodejs    
    
RUN npm install -g configurable-http-proxy    
            
RUN wget http://www.mirrorservice.org/sites/ftp.apache.org/spark/spark-2.2.1/spark-2.2.1-bin-hadoop2.7.tgz \
    && tar -xvzf spark-2.2.1-bin-hadoop2.7.tgz && rm spark-2.2.1-bin-hadoop2.7.tgz 

RUN wget http://mirror.vorboss.net/apache/hadoop/common/hadoop-2.7.5/hadoop-2.7.5.tar.gz \
    && tar -xvzf hadoop-2.7.5.tar.gz && rm hadoop-2.7.5.tar.gz

RUN groupadd hadoop && mkdir -p /home/hadoop && useradd -g hadoop -d/home/hadoop hadoop && echo "hadoop:hadoop" | chpasswd \
    && chown -R hadoop:hadoop /hadoop-2.7.5 && chmod -R g+rw /hadoop-2.7.5/ && chown hadoop /home/hadoop

RUN mkdir -p /home/hdfs && useradd -g hadoop -d /home/hdfs hdfs && echo "hdfs:hdfs" | chpasswd && chown hdfs /home/hdfs

RUN DEBIAN_FRONTEND=noninteractive apt-get -q -y --fix-missing install openssh-client openssh-server

RUN pip3 install jupyter py4j matplotlib nltk spacy numpy pandas scipy scikit-learn pyldavis lda gensim pyemd folium seaborn

RUN python3 -m nltk.downloader punkt

RUN DEBIAN_FRONTEND=noninteractive apt-get -q -y install libzmq3-dev \
    net-tools \
    pciutils
                
# https://github.com/Kronuz/pyScss/issues/308
ENV LC_CTYPE C.UTF-8

RUN apt-get clean && apt-get -q -y update
RUN DEBIAN_FRONTEND=noninteractive apt-get -q -y install libssl-dev sudo

RUN pip3 install twisted autobahn PyZMQ txZMQ klein requests bs4 treq

RUN mkdir -p /data

RUN sed -i s/Port\\s22/Port\ 8022/ etc/ssh/sshd_config
RUN sed -i s/#ListenAddress\\s0.0.0.0/ListenAddress\ 0.0.0.0/ etc/ssh/sshd_config
RUN sed -i s/StrictModes\\syes/StrictModes\ no/ etc/ssh/sshd_config

# http://linuxcommando.blogspot.co.uk/2008/10/how-to-disable-ssh-host-key-checking.html
# https://www.symantec.com/connect/articles/ssh-host-key-protection
RUN echo "    Port 8022" >> /etc/ssh/ssh_config && echo "    StrictHostKeyChecking no" >> /etc/ssh/ssh_config \
    && echo "    UserKnownHostsFile=/dev/null" >> /etc/ssh/ssh_config 

RUN chmod -R a+x /hadoop-2.7.5/bin && chmod -R a+x /hadoop-2.7.5/sbin
ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64/jre/
ENV HADOOP_HOME /hadoop-2.7.5
ENV PATH $PATH:$HADOOP_HOME/bin:$HADOOP_HOME:/sbin
ADD hadoop_conf /hadoop-2.7.5/etc/hadoop

ADD scripts /usr/local/bin

COPY ananke /var/www/ananke
ADD conf /spark-2.2.1-bin-hadoop2.7/conf

RUN mkdir -p /root/.jupyter
COPY jupyter_conf /root/.jupyter
RUN mkdir -p /var/run/sshd
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["/usr/bin/supervisord"]
