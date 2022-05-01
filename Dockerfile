FROM python:3.11-rc-alpine

ENV cloud_name raincloud

COPY . /tmp/raincloud

RUN python -m venv /opt/venv
RUN . /opt/venv/bin/activate && cd /tmp/raincloud && python -m pip install .
RUN . /opt/venv/bin/activate && python -m pip install gunicorn

RUN rm -rf /tmp/raincloud

EXPOSE 8000/tcp

ENTRYPOINT . /opt/venv/bin/activate && gunicorn --bind=0.0.0.0:8000 "raincloud:create_app(base_path='/var/www/raincloud',cloud_name='${cloud_name}')"