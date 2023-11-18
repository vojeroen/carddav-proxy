FROM registry.acacia0.com/base-python:1.0-3.10
LABEL authors="jeroen@acacia0.com"

#RUN apt-get update &&\
#    apt-get install -y postgresql-common libpq-dev gcc &&\
#    rm -rf /var/lib/apt/lists/* /var/cache/apt/*

COPY build/requirements.txt /install/requirements.txt
RUN pip install -r /install/requirements.txt

COPY build/init.sh /init.sh

USER acacia0

COPY src /app
