dockerfile

FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    python3-dev \
    build-essential

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "app:app"]

