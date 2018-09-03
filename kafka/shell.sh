#!/bin/bash

# Just run a quick kafka shell where you can access the command line utils
docker run -it --rm --entrypoint /bin/bash --net=host wurstmeister/kafka
