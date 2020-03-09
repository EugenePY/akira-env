FROM python:3.7.6-slim-buster as build 

# build dependency
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y git

ENV AKIRA_TEST_HOME=/akira_test

WORKDIR ${AKIRA_TEST_HOME}
COPY . ${AKIRA_TEST_HOME}
RUN python setup.py develop

ENTRYPOINT ["python", "-m", "akira_env.server"]