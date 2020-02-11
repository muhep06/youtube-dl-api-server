FROM python:3.7-slim

RUN pip3 install --upgrade aiofiles astroid bottle colorama isort \
    lazy-object-proxy mccabe multidict pylint six typed-ast websockets wrapt youtube-dl

ADD main.py /data/main.py
ADD public /data/public

WORKDIR /data

EXPOSE 1998

CMD ["python3", "/data/main.py"]