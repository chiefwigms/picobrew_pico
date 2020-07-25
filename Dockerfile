FROM python:3.6.9

ENV HOST=0.0.0.0
ENV PORT=80

WORKDIR /picobrew_pico

RUN pip3 install -U pip

COPY requirements.txt /picobrew_pico/requirements.txt
RUN pip install -r requirements.txt

COPY . /picobrew_pico
RUN cd /picobrew_pico && git init && git remote add origin https://github.com/chiefwigms/picobrew_pico.git

CMD python3 server.py ${HOST} ${PORT}
