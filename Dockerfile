# this Dockerfile needed only for debugging spec-file configuration on Linux, not used in Jenkins
FROM ubuntu:20.04
SHELL ["/bin/bash", "-i", "-c"]
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install python3 pip python3.8-venv python3-tk -y
VOLUME /src/
WORKDIR /src/