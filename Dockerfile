FROM python:3.7.6-slim-buster as build 

# build dependency
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y git

ENV AKIRA_ENV_HOME=/akira_test
WORKDIR ${AKIRA_ENV_HOME}
ADD requirements.txt .
RUN pip install -r requirements.txt

COPY . ${AKIRA_ENV_HOME}
RUN python setup.py develop

ENTRYPOINT ["python", "-m", "akira_env.server"]