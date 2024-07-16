# First stage: build image with dependencies
FROM python:3.11.2-slim-bullseye AS builder
WORKDIR /app
COPY ./Pipfile* ./


RUN apt-get update && apt-get install -y git && \
    apt-get install -y wait-for-it
RUN pip3 install pipenv && \
    pipenv install --system --deploy --ignore-pipfile



# Second stage: copy only necessary files and remove unnecessary packages
FROM python:3.11.2-slim-bullseye
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY . .
RUN apt-get update && apt-get install -y libpq-dev python3-dev gcc
RUN pip3 install psycopg2==2.9.7
RUN apt-get update && apt-get install -y wait-for-it && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
ENV PYTHONPATH=/app
ENTRYPOINT [ "/bin/bash", "-c" ]
