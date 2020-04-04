FROM python:3.7.6-slim-buster as rocksdb


RUN echo 'deb [check-valid-until=no] http://archive.debian.org/debian jessie-backports main' >> /etc/apt/sources.list
RUN apt-get update \
    && apt-get install -y --no-install-recommends apt-utils \
    && apt-get install git gcc make g++ libgflags-dev libsnappy-dev zlib1g-dev libbz2-dev liblz4-dev libzstd-dev -y \
    && apt-get autoremove -y && apt-get clean

WORKDIR /tmp/rocksdb

RUN git clone https://github.com/facebook/rocksdb.git /tmp/rocksdb \
    && pip install git+https://github.com/EugenePY/marshmallow-mongoengine.git@master#egg=marshmallow_mongoengine \
    && make install-shared INSTALL_PATH=/usr \
    && rm -rf /tmp/rocksdb

FROM rocksdb as builder
# install dependency

ARG AKIRA_DATA_HOME=/akira_data
WORKDIR ${AKIRA_DATA_HOME}

ARG REQUIREMENTS_PATH=data_pipeline
ADD ${REQUIREMENTS_PATH}/requirements.txt .

RUN pip install -r requirements.txt

RUN yes Y | apt-get remove --purge git libgflags-dev libsnappy-dev zlib1g-dev libbz2-dev liblz4-dev libzstd-dev

FROM builder as runtime
# copy source code, building the package
ARG AKIRA_DATA_HOME=/akira_data
WORKDIR ${AKIRA_DATA_HOME}
# copy source code
# install 
COPY . ${AKIRA_DATA_HOME}
RUN python setup.py develop

# cleanup
CMD ["python", "-m", "akira_data", "variable-task", "list-variable-pool"]