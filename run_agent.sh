docker run -it --rm --net=host --privileged   -v /dev:/dev   microros/micro-ros-agent:jazzy   serial --dev /dev/ttyACM0 -b 115200 -v6
