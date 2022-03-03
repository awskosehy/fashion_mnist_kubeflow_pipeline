FROM pytorch/pytorch:1.9.0-cuda10.2-cudnn7-runtime AS build

ENV APP_HOME /src
COPY requirements.txt ${APP_HOME}/

RUN pip install --no-cache-dir -r ${APP_HOME}/requirements.txt

COPY . ${APP_HOME}
WORKDIR ${APP_HOME}

ENTRYPOINT ["python3", ${APP_HOME} + "/fashion_mnist.py"]