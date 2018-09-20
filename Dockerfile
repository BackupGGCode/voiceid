FROM ubuntu:12.04

WORKDIR /usr/src/app

COPY . .

RUN apt-get update \
    && apt-get install -y python2.7 python-wxgtk2.8 openjdk-7-jdk \
       gstreamer0.10-plugins-base gstreamer0.10-plugins-good \
       gstreamer0.10-plugins-bad gstreamer0.10-plugins-ugly \
       gstreamer-tools sox mplayer python-setuptools python-pip \
    && pip install --index-url=https://pypi.python.org/simple/ MplayerCtrl \
    && python setup.py install
