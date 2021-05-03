FROM centos:7

ENV LANG en_US.utf8
ENV LC_ALL en_US.utf8

RUN yum upgrade -y

RUN yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm && \
    yum install -y net-tools which python3 enchant && \
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python3 get-pip.py && \
    rm get-pip.py && \
    yum clean all && \
    rm -r -f /var/cache/yum && \
    mkdir -p /opt/app/{bin,conf,data,pkg,tmp}


COPY . /opt/app/pkg

RUN chmod -R u+x /opt/app/pkg && \
    cd /opt/app/pkg && \
    pip3 install -r requirements.txt

ENTRYPOINT /bin/bash
