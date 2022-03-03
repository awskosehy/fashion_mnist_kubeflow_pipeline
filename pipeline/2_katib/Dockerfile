FROM kosehy/pytorch_fashion_mnist:latest

ENV APP_HOME /src
ENV KATIB_HOME /katib
COPY requirements.txt ${APP_HOME}/

# Add folder for the logs.
RUN pip install --no-cache-dir -r ${APP_HOME}/requirements.txt \
  && mkdir ${KATIB_HOME} \
  && chgrp -R 0 ${APP_HOME} \
  && chmod -R g+rwX ${APP_HOME} \
  && chgrp -R 0 ${KATIB_HOME} \
  && chmod -R g+rwX ${KATIB_HOME}

COPY . ${APP_HOME}
WORKDIR ${APP_HOME}

ENTRYPOINT ["python3", ${APP_HOME} + "/launch_experiment.py"]
