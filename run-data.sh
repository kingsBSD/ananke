docker rm ananke
docker run -ti --rm --name ananke -v ${1}:/data --net=host ananke

