FROM registry.screamtrumpet.csie.ncku.edu.tw/pros_images/pros_base_image:latest

RUN apt-get update && apt-get install -y ros-humble-joy
