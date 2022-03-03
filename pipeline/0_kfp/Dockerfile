FROM pytorch/pytorch:1.9.0-cuda10.2-cudnn7-runtime

ENV APP_HOME /src
COPY . ${APP_HOME}
WORKDIR ${APP_HOME}
RUN pip install --no-cache-dir -r 0_kfp/requirements.txt