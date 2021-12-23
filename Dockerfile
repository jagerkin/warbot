FROM python:3.10-buster AS warbase
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN groupadd -g 10000 warbot && \
    useradd -u 10000 -g warbot warbot -m && \
    chown -R warbot.warbot /usr/src/app && \
    pip install --no-cache-dir -r ./requirements.txt && \
    rm ./requirements.txt

FROM warbase
WORKDIR /usr/src/app
COPY *.py run.sh ./
CMD exec /bin/sh /usr/src/app/run.sh
