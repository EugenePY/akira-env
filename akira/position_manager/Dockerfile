FROM rocksdb as runtime


RUN apt-get update \
    && apt-get install -y --no-install-recommends apt-utils \
    && apt-get install git gcc make g++ libgflags-dev libsnappy-dev zlib1g-dev libbz2-dev liblz4-dev libzstd-dev -y \
    && apt-get autoremove -y && apt-get clean

# install dependency
ARG POSITION_MANGER=/position_manager
ARG REQUIREMENTS_PATH=.

WORKDIR ${POSITION_MANGER}
ADD ${REQUIREMENTS_PATH}/requirements.txt .
RUN pip install -r requirements.txt

# cleanup
COPY . ${POSITION_MANGER}
RUN python setup.py develop