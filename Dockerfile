FROM python:3.10-slim
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.vendor="Cloud-Dog, Viewdeck Engineering Limited"

WORKDIR /app

# Install platform packages from internal PyPI.
ARG PYPI_URL=https://pypi.cloud-dog.net/simple
RUN --mount=type=secret,id=pip_conf,target=/etc/pip.conf \
    apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
      --extra-index-url ${PYPI_URL} \
      --trusted-host pypi.cloud-dog.net \
      --trusted-host files.pythonhosted.org \
      cloud-dog-config \
      cloud-dog-logging \
      cloud-dog-api-kit==0.12.4 \
      cloud-dog-idam \
      cloud-dog-db \
      cloud-dog-jobs

COPY . /app
RUN --mount=type=secret,id=pip_conf,target=/etc/pip.conf \
      pip install --no-cache-dir \
      --extra-index-url ${PYPI_URL} \
      --trusted-host pypi.cloud-dog.net \
      --trusted-host files.pythonhosted.org \
      -e ".[dev]"

EXPOSE 8086 8087 8088 8089

CMD ["bash", "-lc", "./server_control.sh --env tests/env-ST start all && tail -f logs/api.log logs/web.log logs/mcp.log logs/a2a.log"]
