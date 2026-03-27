FROM python:3.10-slim

WORKDIR /workspace
COPY db-mcp-server /workspace/db-mcp-server
COPY cloud-dog-ai-platform-standards /workspace/cloud-dog-ai-platform-standards
WORKDIR /workspace/db-mcp-server

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e ".[dev]"

EXPOSE 8086 8087 8088 8089

CMD ["bash", "-lc", "./server_control.sh --env tests/env-ST start all && tail -f logs/api.log logs/web.log logs/mcp.log logs/a2a.log"]
