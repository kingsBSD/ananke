docker rm ananke
docker run -ti --name ananke -v ${1}:/data --net=host -p 8888:8888 -p 4040:4040 -p 7077:7077 -p 7078:7078 -p 8080:8080 -p 8081:8081 -p 9000:9000 ananke

