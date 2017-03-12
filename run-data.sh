docker rm ananke
docker run -ti --name ananke -v ${1}:/data --net=host ananke

