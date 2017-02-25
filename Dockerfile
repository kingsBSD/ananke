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
   
RUN wget http://apache.mirror.anlx.net/spark/spark-2.1.0/spark-2.1.0-bin-hadoop2.7.tgz
RUN tar -xvzf spark-2.1.0-bin-hadoop2.7.tgz
RUN rm spark-2.1.0-bin-hadoop2.7.tgz

RUN wget http://apache.mirrors.nublue.co.uk/hadoop/common/hadoop-2.7.3/hadoop-2.7.3.tar.gz
RUN tar -xvzf hadoop-2.7.3.tar.gz
RUN rm hadoop-2.7.3.tar.gz

RUN groupadd hadoop
RUN mkdir -p /home/hadoop
RUN useradd -g hadoop -d/home/hadoop hadoop
RUN echo "hadoop:hadoop" | chpasswd
RUN chown -R hadoop:hadoop /hadoop-2.7.3
RUN chmod -R g+rw /hadoop-2.7.3/
RUN chown hadoop /home/hadoop

RUN mkdir -p /home/hdfs
RUN useradd -g hadoop -d /home/hdfs hdfs
RUN echo "hdfs:hdfs" | chpasswd
RUN chown hdfs /home/hdfs

RUN DEBIAN_FRONTEND=noninteractive apt-get -q -y --fix-missing install openssh-client openssh-server

RUN pip3 install jupyter

RUN pip install py4j

RUN pip3 install matplotlib
RUN pip3 install nltk
RUN pip3 install spacy
RUN pip3 install numpy
RUN pip3 install pandas        
RUN pip3 install scipy
RUN pip3 install scikit-learn
RUN pip3 install pyldavis
RUN pip3 install lda
RUN pip3 install gensim
RUN pip3 install pyemd
RUN pip3 install folium
RUN pip3 install seaborn

RUN python3 -m nltk.downloader punkt

RUN DEBIAN_FRONTEND=noninteractive apt-get -q -y install libzmq3-dev \
    net-tools \
    nginx \
    pciutils
        
# https://github.com/Kronuz/pyScss/issues/308
ENV LC_CTYPE C.UTF-8

RUN apt-get clean && apt-get -q -y update
RUN DEBIAN_FRONTEND=noninteractive apt-get -q -y install libssl-dev sudo

RUN pip3 install twisted
RUN pip3 install autobahn
RUN pip3 install PyZMQ
RUN pip3 install txZMQ
RUN pip3 install klein
RUN pip3 install requests
RUN pip3 install bs4
RUN pip3 install treq

RUN mkdir -p /data

RUN sed -i s/Port\\s22/Port\ 8022/ etc/ssh/sshd_config
# http://linuxcommando.blogspot.co.uk/2008/10/how-to-disable-ssh-host-key-checking.html
# https://www.symantec.com/connect/articles/ssh-host-key-protection
RUN echo "    Port 8022" >> /etc/ssh/ssh_config
RUN echo "    StrictHostKeyChecking no" >> /etc/ssh/ssh_config
RUN echo "    UserKnownHostsFile=/dev/null" >> /etc/ssh/ssh_config

RUN chmod -R a+x /hadoop-2.7.3/bin
RUN chmod -R a+x /hadoop-2.7.3/sbin
ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64/jre/
ENV HADOOP_HOME /hadoop-2.7.3
ENV PATH $PATH:$HADOOP_HOME/bin:$HADOOP_HOME:/sbin
ADD hadoop_conf /hadoop-2.7.3/etc/hadoop

ADD scripts /usr/local/bin

COPY ananke /var/www/ananke
ADD conf /spark-2.1.0-bin-hadoop2.7/conf
ADD sites-available /etc/nginx/sites-available
RUN ln -s /etc/nginx/sites-available/ananke /etc/nginx/sites-enabled
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["/usr/bin/supervisord"]
