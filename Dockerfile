FROM python:3.11-rc-alpine

ENV cloud_name raincloud
ENV num_workers 5
ENV worker_timeout 300

COPY . /tmp/raincloud

RUN apk add redis
RUN python -m venv /opt/venv
RUN . /opt/venv/bin/activate && cd /tmp/raincloud && python -m pip install .
RUN . /opt/venv/bin/activate && python -m pip install gunicorn

RUN rm -rf /tmp/raincloud

EXPOSE 8000/tcp

ENTRYPOINT redis-server & echo $RANDOM$RANDOM | base64 > /var/raincloud_secret_key && . /opt/venv/bin/activate && gunicorn --bind=0.0.0.0:8000 --workers ${num_workers} --timeout ${worker_timeout} "raincloud:create_app(base_path='/var/www/raincloud', secret_key_path='/var/raincloud_secret_key', cloud_name='${cloud_name}')"