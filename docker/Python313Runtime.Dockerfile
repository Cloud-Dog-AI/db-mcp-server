# syntax=docker/dockerfile:1
# Bootstrap-only definition for the Cloud-Dog-controlled Python 3.13 runtime.
# Service images consume the resulting immutable internal-registry digest and
# never contact a public image or Debian package boundary during their build.
FROM python:3.13-slim

ARG CUSTOM_CA_CERT=custom-ca.crt
COPY ${CUSTOM_CA_CERT} /usr/local/share/ca-certificates/cloud-dog-corporate-ca.crt
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends ca-certificates curl && \
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/*

LABEL org.opencontainers.image.vendor="Cloud-Dog, Viewdeck Engineering Limited"
LABEL org.opencontainers.image.title="Cloud-Dog Python 3.13 service runtime"
