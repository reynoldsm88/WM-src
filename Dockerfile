FROM centos:7

ENV LANG en_US.utf8
ENV LC_ALL en_US.utf8
ENV CORENLP_HOME /opt/app/pkg/corenlp

RUN yum upgrade -y

RUN yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm && \
    yum install -y net-tools which python3 enchant java-1.8.0-openjdk && \
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python3 get-pip.py && \
    rm get-pip.py && \
    yum clean all && \
    rm -r -f /var/cache/yum && \
    mkdir -p /opt/app/{bin,conf,data,pkg,tmp}


COPY . /opt/app/bin

RUN chmod -R u+x /opt/app/bin && \
    cd /opt/app/bin && \
    pip3 install -r requirements.txt

COPY distro/stanford-corenlp-4.2.0.zip /opt/app/pkg
COPY distro/nltk_data /root/nltk_data

RUN yum install -y unzip && \
    unzip /opt/app/pkg/stanford-corenlp-4.2.0.zip -d /opt/app/pkg/ && \
    mv /opt/app/pkg/stanford-corenlp-4.2.0 $CORENLP_HOME && \
    rm /opt/app/pkg/*.zip && \
    chmod -R u+x $CORENLP_HOME

ENTRYPOINT /opt/app/bin/sofia-stream.py worker
