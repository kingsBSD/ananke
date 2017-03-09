docker rm ananke

VBOX=true
if [ "$(lspci | grep -c VirtualBox)" -eq 0 ]; then
    VBOX=false;
fi

docker run -ti --name ananke --net=host --pid=host -e TINI_SUBREAPER=true -e VBOX=$VBOX ananke
