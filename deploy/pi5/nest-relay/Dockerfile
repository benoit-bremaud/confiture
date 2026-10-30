# Relay from the Pi 5 satellite to the Nest Mini (benoit-bremaud/confiture#18).
FROM python:3.13.18-slim-trixie@sha256:76baad6037690d6e8c4397fbcaef17bca6f19eecef822b708fe8fa3417d30bb5
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY relay.py main.py ./
USER 1000:1000
ENV PYTHONUNBUFFERED=1
# The relay listens on nothing; the process being alive is the health signal.
HEALTHCHECK --interval=60s --timeout=5s CMD ["python", "-c", "import os; os.kill(1, 0)"]
CMD ["python", "main.py"]
