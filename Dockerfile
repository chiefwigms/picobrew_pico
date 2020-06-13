FROM python:3.6.9

WORKDIR /app

RUN pip3 install -U pip

COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

COPY . /app

CMD python3 server.py