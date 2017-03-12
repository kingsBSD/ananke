docker rm ananke
docker run -ti --name ananke --net=host --pid=host -e TINI_SUBREAPER=true ananke
