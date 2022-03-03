FROM tensorflow/tensorflow:2.1.0-py3

ENV APP_HOME /src
COPY requirements.txt ${APP_HOME}/

RUN pip install --no-cache-dir -r ${APP_HOME}/requirements.txt

COPY . ${APP_HOME}
WORKDIR ${APP_HOME}

ENTRYPOINT ["python", ${APP_HOME} + "/tensorboard_display.py"]