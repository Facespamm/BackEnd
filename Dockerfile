FROM python:3.12-slim
WORKDIR /app
EXPOSE 5000

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python","app.py"]