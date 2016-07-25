docker rm ananke

VBOX=true
if [ "$(lspci | grep -c VirtualBox)" -eq 0 ]; then
    VBOX=false;
fi

docker run -ti --name ananke -v ${1}:/data -e VBOX=$VBOX --net=host ananke

