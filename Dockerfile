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
COPY generate_bulletin.py .
COPY main.py .
COPY requirements.txt .
COPY .env.example .

RUN mkdir -p /data && chown gert:gert /data

USER gert
EXPOSE 8000

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
