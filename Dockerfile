FROM registry.cloud-dog.net:443/cloud-dog/python-runtime@sha256:e23c4110eb0c8a2995635a97dee0fff83d5b729de611dfb1e31850c67b33ec60
ARG VCS_REF=unknown
ARG BUILD_DATE=unknown
# W28E-1863 fix-wave-d (WSC-014): build-identity provenance. SOURCE_COMMIT defaults
# to VCS_REF (git HEAD); docker-build.sh passes SOURCE_COMMIT/SOURCE_BRANCH/BUILD_DATE.
ARG SOURCE_COMMIT=unknown
ARG SOURCE_BRANCH=unknown
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.vendor="Cloud-Dog, Viewdeck Engineering Limited"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.ref.name="${SOURCE_BRANCH}"

# W28E-1863 fix-wave-d (WSC-014): surface build identity to the RUNTIME so the web
# tier's _build_identity() (read config-routed via cloud_dog_config, RULES §1.4.1)
# can populate /version for the shared About page.
ENV CLOUD_DOG__BUILD__SOURCE_COMMIT=${SOURCE_COMMIT}
ENV CLOUD_DOG__BUILD__SOURCE_BRANCH=${SOURCE_BRANCH}
ENV CLOUD_DOG__BUILD__BUILD_DATE=${BUILD_DATE}

WORKDIR /app
ENV PIP_NO_INPUT=1

# Install platform packages from internal PyPI via BuildKit-mounted pip.conf.
ARG PYPI_URL=https://pypi.cloud-dog.net/simple
RUN --mount=type=secret,id=pip_conf,target=/etc/pip.conf \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
      --trusted-host pypi.cloud-dog.net \
      "cloud-dog-config==0.3.4" \
      "cloud-dog-logging==0.4.1" \
      "cloud-dog-api-kit[change-stream-db]==0.14.0" \
      "cloud-dog-idam==0.5.4" \
      "cloud-dog-llm==0.4.1" \
      "cloud-dog-db[nosql,sql]==0.3.3" \
      "cloud-dog-jobs==0.4.2" \
      "cloud-dog-storage==0.1.8"

COPY . /app
RUN --mount=type=secret,id=pip_conf,target=/etc/pip.conf \
      pip install --no-cache-dir \
      --trusted-host pypi.cloud-dog.net \
      -e .

EXPOSE 8086 8087 8088 8089

RUN chmod +x /app/docker-entrypoint.sh
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["bash", "-lc", "./server_control.sh --env tests/env-ST start all && tail -f logs/api.log logs/web.log logs/mcp.log logs/a2a.log"]
