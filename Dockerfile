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

RUN pip3 install jupyter

RUN pip install py4j

RUN pip3 install matplotlib
RUN pip3 install nltk
RUN pip3 install numpy
RUN pip3 install pandas        
RUN pip3 install scipy
RUN pip3 install scikit-learn
RUN pip3 install pyldavis
RUN pip3 install lda
RUN pip3 install gensim
RUN pip3 install pyemd
RUN pip3 install folium
RUN pip3 installseaborn

RUN python3 -m nltk.downloader punkt

RUN DEBIAN_FRONTEND=noninteractive apt-get -q -y install libzmq3-dev \
    net-tools \
    nginx \
    pciutils

# https://github.com/Kronuz/pyScss/issues/308
ENV LC_CTYPE C.UTF-8

RUN pip3 install twisted
RUN pip3 install autobahn
RUN pip3 install PyZMQ
RUN pip3 install txZMQ
RUN pip3 install flask
RUN pip3 install requests
RUN pip3 install bs4
RUN pip3 install uwsgi

RUN mkdir -p /data

ADD scripts /usr/local/bin
ADD ananke /var/www/ananke
ADD conf /spark-2.1.0-bin-hadoop2.7/conf
ADD sites-available /etc/nginx/sites-available
RUN ln -s /etc/nginx/sites-available/ananke /etc/nginx/sites-enabled
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["/usr/bin/supervisord"]
