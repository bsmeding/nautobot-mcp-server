# Development image: a Nautobot install with this app mounted in editable mode.
ARG NAUTOBOT_VER="2.4"
ARG PYTHON_VER="3.12"
FROM ghcr.io/nautobot/nautobot-dev:${NAUTOBOT_VER}-py${PYTHON_VER}

ARG NAUTOBOT_ROOT=/opt/nautobot
WORKDIR $NAUTOBOT_ROOT

USER 0

# Install the app (and its dev/test deps) in editable mode.
COPY . /source
WORKDIR /source
RUN pip install --no-cache-dir -e ".[dev,nautobot]"

WORKDIR $NAUTOBOT_ROOT
USER nautobot

# nautobot_config.py is mounted at runtime via docker-compose.
COPY development/nautobot_config.py ${NAUTOBOT_ROOT}/nautobot_config.py
