FROM python:3.9-alpine

WORKDIR /usr/src/app

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir /etc/cron.d
COPY crontab /etc/cron.d/crontab
RUN crontab /etc/cron.d/crontab

CMD ["crond", "-f"]