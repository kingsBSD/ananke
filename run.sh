docker rm ananke

VBOX=true
if [ "$(lspci | grep -c VirtualBox)" -eq 0 ]; then
    VBOX=false;
fi

#docker run -ti --name ananke --net=host -e VBOX=$VBOX -p 5000:5000 -p 8888:8888 -p 4040:4040 -p 7077:7077 -p 7078:7078 -p 8080:8080 -p 8081:8081 -p 9000:9000 ananke
docker run -ti --name ananke --net=host --pid=host -e TINI_SUBREAPER=true -e VBOX=$VBOX ananke
