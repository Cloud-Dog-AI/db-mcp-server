FROM python:3.10-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir hatchling && \
    pip install --no-cache-dir -e .

CMD ["bash", "-lc", "echo 'db-mcp-server is a planning skeleton only; runtime not implemented yet.' >&2; exit 1"]
