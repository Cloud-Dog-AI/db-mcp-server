FROM python:3.10-slim
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.vendor="Cloud-Dog, Viewdeck Engineering Limited"

WORKDIR /app

# Install platform packages from Gitea PyPI (zero credentials — anonymous access)
ARG PYPI_URL=https://gitea.cloud-dog.net/api/packages/Cloud-Dog-External/pypi/simple
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
      --extra-index-url ${PYPI_URL} \
      --trusted-host gitea.cloud-dog.net \
      --trusted-host pypi.org \
      --trusted-host files.pythonhosted.org \
      cloud-dog-config \
      cloud-dog-logging \
      cloud-dog-api-kit>=0.2.4 \
      cloud-dog-idam \
      cloud-dog-db \
      cloud-dog-jobs

COPY . /app
RUN pip install --no-cache-dir -e ".[dev]"

EXPOSE 8086 8087 8088 8089

CMD ["bash", "-lc", "./server_control.sh --env tests/env-ST start all && tail -f logs/api.log logs/web.log logs/mcp.log logs/a2a.log"]
