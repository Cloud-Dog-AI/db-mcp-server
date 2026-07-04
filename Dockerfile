# syntax=docker/dockerfile:1
FROM python:3.12-slim
ARG VCS_REF=unknown
ARG BUILD_DATE=unknown
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.vendor="Cloud-Dog, Viewdeck Engineering Limited"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"

WORKDIR /app
ENV PIP_NO_INPUT=1

# Install platform packages from internal PyPI via BuildKit-mounted pip.conf.
ARG PYPI_URL=https://pypi.cloud-dog.net/simple
RUN --mount=type=secret,id=pip_conf,target=/etc/pip.conf \
    apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
      --trusted-host pypi.cloud-dog.net \
      --trusted-host files.pythonhosted.org \
      "cloud-dog-config==0.3.4" \
      cloud-dog-logging \
      cloud-dog-api-kit==0.13.0 \
      "cloud-dog-idam==0.5.3" \
      "cloud-dog-llm==0.4.0" \
      "cloud-dog-db[nosql,sql]" \
      cloud-dog-jobs \
      cloud-dog-storage==0.1.4

COPY . /app
RUN --mount=type=secret,id=pip_conf,target=/etc/pip.conf \
      pip install --no-cache-dir \
      --trusted-host pypi.cloud-dog.net \
      --trusted-host files.pythonhosted.org \
      -e ".[dev]"

EXPOSE 8086 8087 8088 8089

CMD ["bash", "-lc", "./server_control.sh --env tests/env-ST start all && tail -f logs/api.log logs/web.log logs/mcp.log logs/a2a.log"]
