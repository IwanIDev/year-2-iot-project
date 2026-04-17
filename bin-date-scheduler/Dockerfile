FROM python:3.12-alpine

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY update_bins.py .

CMD ["python", "/app/update_bins.py"]
