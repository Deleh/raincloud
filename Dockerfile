FROM python:3.11-rc-alpine

ENV cloud_name raincloud

RUN apk update && apk add git
RUN python -m venv /opt/venv
RUN . /opt/venv/bin/activate && python -m pip install git+https://github.com/Deleh/raincloud
RUN . /opt/venv/bin/activate && python -m pip install gunicorn

EXPOSE 8000/tcp

ENTRYPOINT . /opt/venv/bin/activate && gunicorn --bind=0.0.0.0:8000 "raincloud:create_app(base_path='/var/www/raincloud',cloud_name='${cloud_name}')"