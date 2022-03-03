FROM python:3.6.10-slim

ENV APP_HOME /src

COPY . ${APP_HOME}
WORKDIR ${APP_HOME}

ENTRYPOINT ["python", ${APP_HOME} + "/model_path.py"]