# syntax=docker/dockerfile:1
FROM 2000cubits/raspbian:bullseye.latest

RUN apt update; \
    apt install -y sudo git wget curl g++ make gawk jq libsqlite3-dev zip cron; \
    mkdir /data

WORKDIR /data
RUN git clone https://github.com/EdNekebno/DGTCentaurMods

COPY .ci.conf /root
COPY cronjob/root /var/spool/cron/crontabs/
RUN chown root.crontab /var/spool/cron/crontabs/root; chmod 600 /var/spool/cron/crontabs/root

CMD ["cron", "-f"]
