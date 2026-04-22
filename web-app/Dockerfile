FROM docker.io/python:3.13.11-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
	CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthcheck/live', timeout=3)"

CMD [ "gunicorn", "--workers", "2", "--threads", "1", "wsgi" ]

