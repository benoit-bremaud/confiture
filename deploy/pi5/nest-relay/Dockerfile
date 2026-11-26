# syntax=docker/dockerfile:1.19
# check=error=true
# Relay from the Pi 5 satellite to the Nest Mini (benoit-bremaud/confiture#18).
FROM python:3.15.1-slim-trixie@sha256:533b0b2f9b5d46fd097091cf826f27902f1d6c3bca714b6dc74551356aa97a51
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY relay.py main.py ./
USER 1000:1000
ENV PYTHONUNBUFFERED=1
# The relay listens on nothing: this only confirms the container is up; main.py logs reconnects.
HEALTHCHECK --interval=60s --timeout=5s CMD ["python", "-c", "import os; os.kill(1, 0)"]
CMD ["python", "main.py"]
