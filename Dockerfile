FROM alpine:3.22.1

ARG VERSION=1.0.2

WORKDIR /app
RUN wget https://github.com/dgongut/ha-mqtt-ucgmax/archive/refs/tags/v${VERSION}.tar.gz -P /tmp
RUN tar -xf /tmp/v${VERSION}.tar.gz
RUN mv ha-mqtt-ucgmax-${VERSION}/mqtt-bridge.py /app
RUN mv ha-mqtt-ucgmax-${VERSION}/config.py /app
RUN mv ha-mqtt-ucgmax-${VERSION}/requirements.txt /app
RUN rm /tmp/v${VERSION}.tar.gz
RUN rm -rf ha-mqtt-ucgmax-${VERSION}/
RUN apk add --no-cache python3 py3-pip tzdata
RUN export PIP_BREAK_SYSTEM_PACKAGES=1; pip3 install --no-cache-dir -Ur /app/requirements.txt

ENTRYPOINT ["python3", "mqtt-bridge.py"]