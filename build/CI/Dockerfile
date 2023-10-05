# syntax=docker/dockerfile:1
FROM microdeb/bullseye

RUN apt update; \
    apt install -y sudo git wget curl g++ make gawk jq libsqlite3-dev zip cron ca-certificates; \
    mkdir /data

WORKDIR /data
RUN git clone http://github.com/EdNekebno/DGTCentaurMods

COPY .ci.conf /root
COPY .gitconfig /root
COPY .git-credentials /root

COPY cronjob/root /var/spool/cron/crontabs/
RUN chown root.crontab /var/spool/cron/crontabs/root; chmod 600 /var/spool/cron/crontabs/root

CMD ["cron", "-f"]
