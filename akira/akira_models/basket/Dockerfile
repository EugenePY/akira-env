####### stage 1: build
FROM rpy2/rpy2 AS builder

ARG AKIRA_HOME=/basket_home 

WORKDIR ${AKIRA_HOME}

COPY r_setup.R ${AKIRA_HOME}/r_setup.R

RUN Rscript r_setup.R

# copy source code

####### stage 2: copy the binary and libs
FROM rpy2/rpy2 AS runtime-image 

RUN mkdir -p /usr/lib/R \
             /usr/local/lib/R/site-library
COPY --from=builder /usr/bin/R /usr/bin/R
COPY --from=builder /usr/bin/Rscript /usr/bin/Rscript
COPY --from=builder /usr/lib/R /usr/lib/R
COPY --from=builder /usr/local/lib/R/site-library /usr/local/lib/R/site-library

# packing
# ARG AKIRA_HOME=/AKIRA_HOME
WORKDIR ${AKIRA_HOME}

# Copy the whole project into container
COPY . ${AKIRA_HOME} 
# install 
RUN python3 setup.py develop

# ENTRYPOINT ["python3", "-m", "baskets"]