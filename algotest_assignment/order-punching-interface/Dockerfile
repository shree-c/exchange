FROM python:3.9.19-slim-bullseye

RUN apt-get update && apt-get upgrade -y

WORKDIR /app

COPY . /app/

ADD /home/shree/algotest_assignment/sql_crud /app/sql_crud

RUN pip install -r requirement.txt

RUN pip install -e ./sql_crud