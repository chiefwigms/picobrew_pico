FROM python:3.6.9

WORKDIR /picobrew

RUN pip3 install -U pip

COPY requirements.txt /picobrew/requirements.txt
RUN pip install -r requirements.txt

COPY . /picobrew

CMD python3 server.py
