FROM python:2.7

#RUN printf "deb http://archive.debian.org/debian/ jessie main\ndeb-src http://archive.debian.org/debian/ jessie main\ndeb http://security.debian.org jessie/updates main\ndeb-src http://security.debian.org jessie/updates main" > /etc/apt/sources.list


RUN apt-get update -y && \
    apt-get install -y python-dev && \
    apt-get install -y mysql-client && \
    rm -rf /var/lib/apt/lists/*

ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt

ADD ./ /src/django_proxysql_demo
WORKDIR /src/django_proxysql_demo

CMD ["./manage.py", "runserver"]
