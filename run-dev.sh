docker run -ti --name ananke --net=host --pid=host -e TINI_SUBREAPER=true -p 8888:8888 -p 4040:4040 -p 7077:7077 -p 8080:8080 -p 9000:9000 ananke /bin/bash

