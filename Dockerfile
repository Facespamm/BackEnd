FROM python:3.12-slim
WORKDIR /app
EXPOSE 5000

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

CMD ["python","app.py"]