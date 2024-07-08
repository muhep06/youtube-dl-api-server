FROM python:3.11-slim

ADD . /data

WORKDIR /data

RUN apt-get -y update

RUN apt-get -y install ffmpeg

RUN pip3 install -r requirements.txt

EXPOSE 1998

CMD ["python3", "/data/main.py"]