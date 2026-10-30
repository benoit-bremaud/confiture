# syntax=docker/dockerfile:1.19
# check=error=true
# Relay from the Pi 5 satellite to the Nest Mini (benoit-bremaud/confiture#18).
FROM python:3.15.0-slim-trixie@sha256:f5b92f2a669a4c347044f29367f31983280b648250ca94dea66f98c53bc87e58
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY relay.py main.py ./
USER 1000:1000
ENV PYTHONUNBUFFERED=1
# The relay listens on nothing: this only confirms the container is up; main.py logs reconnects.
HEALTHCHECK --interval=60s --timeout=5s CMD ["python", "-c", "import os; os.kill(1, 0)"]
CMD ["python", "main.py"]
