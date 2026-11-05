# Sovereign Agent Logbook — one container, no network calls out.
# Build:  docker build -t sovereign-agent-logbook .
# Run:    docker run --rm -p 127.0.0.1:8765:8765 -v logbook-data:/data sovereign-agent-logbook

FROM python:3.13-slim

# Run as an unprivileged user; the data volume is the only writable place.
RUN useradd --create-home --uid 10001 logbook
WORKDIR /app

COPY pyproject.toml README.md LICENSE SPEC.md ./
COPY src ./src
RUN pip install --no-cache-dir . && rm -rf /root/.cache

USER logbook
VOLUME ["/data"]
ENV LOGBOOK_PATH=/data/logbook.jsonl \
    LOGBOOK_TRANSPORT=http \
    LOGBOOK_HOST=0.0.0.0 \
    LOGBOOK_PORT=8765

# Inside the container 0.0.0.0 is required to be reachable at all; the
# `-p 127.0.0.1:8765:8765` in the run command keeps it off the public
# interface of the host. Put a reverse proxy with TLS in front for anything
# beyond localhost.
EXPOSE 8765
CMD ["sovereign-agent-logbook"]
