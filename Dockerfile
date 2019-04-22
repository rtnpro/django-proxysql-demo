FROM python:2.7

RUN apt-get update -y && \
    apt-get install -y python-dev && \
    apt-get install -y mysqlclient && \
    rm -rf /var/lib/apt/lists/*

RUN pip install -r requirements.txt

ADD ./ /src/django_proxysql_demo
WORKDIR /src/django_proxysql_demo
