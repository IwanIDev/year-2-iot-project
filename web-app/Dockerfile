FROM docker.io/python:3.13.11-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD [ "gunicorn", "--workers", "2", "--threads", "1", "wsgi" ]

