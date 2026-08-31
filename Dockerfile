# GERT Backend — production container
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim
RUN groupadd -r gert && useradd -r -g gert -d /app -s /sbin/nologin gert

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Application source
COPY api/ api/
COPY models/ models/
COPY services/ services/
COPY risk/ risk/
COPY features/ features/
COPY data/ data/
COPY db/ db/
COPY domain/ domain/
COPY alerts/ alerts/
COPY bulletin/ bulletin/
COPY evidence/ evidence/
COPY generate_bulletin.py .
COPY main.py .
COPY requirements.txt .
COPY .env.example .

RUN mkdir -p /data && chown gert:gert /data

USER gert
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:' + __import__('os').environ.get('PORT', '8000') + '/ready', timeout=3)"

CMD ["sh", "-c", "exec uvicorn api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
