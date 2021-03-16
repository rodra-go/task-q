FROM python:3.8.5
LABEL MAINTAINER="Rodrigo Cunha <rodrigo.cunha@usp.br>"

RUN apt-get update && \
apt-get upgrade -y
RUN apt-get install bash
RUN apt-get install sudo
RUN apt-get install openssh-client
RUN apt-get install acl

ENV GROUP_ID=1000 \
    USER_ID=1000 \
    USER=taskq \
    PASS=pass

ENV GROUP_ID_2=1001 \
    USER_ID_2=1001 \
    USER_2=user01

ENV PATH="/home/$USER/.local/bin:${PATH}"

RUN addgroup --gid $GROUP_ID $USER
RUN adduser --uid $USER_ID --ingroup $USER --shell /bin/bash --disabled-password --gecos "" $USER
RUN usermod -aG 100 $USER
RUN usermod -aG sudo $USER
RUN echo "$USER:$PASS" | chpasswd

RUN addgroup --gid $GROUP_ID_2 $USER_2
RUN adduser --uid $USER_ID_2 --ingroup $USER_2 --shell /bin/bash --disabled-password --gecos "" $USER_2
RUN usermod -aG 100 $USER_2

ADD requirements.txt /var/$USER/
ADD setup.py /var/$USER/
RUN pip install --upgrade pip setuptools
RUN pip install -r /var/$USER/requirements.txt
RUN python /var/$USER/setup.py

USER $USER
WORKDIR /home/$USER/
