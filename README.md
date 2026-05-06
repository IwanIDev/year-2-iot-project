# BinBuddy
## Folder and File Structure
```text
├── bin-date-scheduler - Cron job to refetch bin collection dates
├── classifier - BinBuddy AI classifier
├── modes - BinBuddy device modes
├── web-app - Website hosted on OpenShift
│   ├── api - API endpoints for the web app
│   ├── bin_lookup - List of each council's bin types and colours
│   ├── council - Handles council data
│   ├── notify - Notification service
│   │   └── email - Email notification service
│   ├── static - Static files on the web app
│   │   └── js - Static JavaScript files
│   ├── telemetry - Handles fetching and storing telemetry data from BinBuddy devices
│   ├── templates - HTML templates for the web app
│   │   └── email - HTML and plaintext templates for email notifications
│   ├── tests - Unit tests for the web app
│   └── users - Handles user data
└── wiki - Internal development documentation
```
## Setup Instructions
### BinBuddy Device
#### Prerequisites
The Pi must be running a 64-bit version of Raspberry Pi OS. The following modules must be connected to the Pi:
- Camera Module
- Grove Shield, with:
    - PIR Motion Sensor - Pin D2
    - Light Sensor - Pin A0
    - LCD Display - I2C Port
    - Button - Pin D3

#### Installation

The following libraries should be installed:
- picamera2 version 0.3.12
- grovepi version 1.4.1
- tensorflow version 2.20.0
- cv2 version 4.5.1
- numpy version 1.26.4
- paho-mqtt version 2.1.0

### Web App
#### Prerequisites
You must have Python 3.13 or newer installed.

#### Installation
You can install the required Python packages using the requirements.txt file:
```bash
pip install -r requirements.txt
```

The following packages and their dependencies should be installed:
```text
Package          Version
---------------- -------
Flask-Bootstrap  3.3.7.1
Flask-Login      0.6.3
Flask-Minify     0.50
Flask-SQLAlchemy 3.1.1
gevent           26.4.0
gunicorn         25.3.0
httpx            0.28.1
matplotlib       3.10.8
pip_system_certs 5.3
psycopg2-binary  2.9.11
python-dotenv    1.2.2
requests         2.33.1
ruff             0.15.11
truststore       0.10.4
websocket-client 1.9.0
whitenoise       6.12.0
```

#### Configuration
The following environment variables must be set for the web app to run:
```text
THINGSBOARD_URL - The URL of the Thingsboard instance
THINGSBOARD_USERNAME - Username for the account used to access the Thingsboard API (tested with a Tenant Admin account)
THINGSBOARD_PASSWORD - Password for the account used to access the Thingsboard API
BIN_COLLECTION_API - URL of the API being used to fetch bin collection dates
MAIL_URL - Mailgun domain for email notifications
MAIL_SENDER - Email address to send notifications from
MAIL_API_KEY - Mailgun API key for email notifications
```
## Running the Project
### BinBuddy Device
To start the BinBuddy device code, open the `modes` directory and run this command:
```bash
python entry.py
```

### Web App
The web app can be run using the following command from within the `web-app` directory:
```bash
python main.py
```
This starts a Flask development server. You can start a production server with gunicorn using the following command:
```bash
gunicorn wsgi
```
You can also build and run the app using Docker:
```bash
docker build -t binbuddy-web-app .
docker run -d -p 8080:8080 --env-file .env binbuddy-web-app
```

## Third-party Software and Frameworks
### BinBuddy Device
- Tensorflow - Runs AI model - [Documentation](https://www.tensorflow.org/)
- Picamera2 - Controls Pi Camera - [Documentation](https://pip-assets.raspberrypi.com/categories/652-raspberry-pi-camera-module-2/documents/RP-008156-DS-2-picamera2-manual.pdf?disposition=inline)
- CV2 - Image Pre-processing - [Documentation](https://docs.opencv.org/4.x/)
- Numpy - Supplements Tensorflow - [Documentation](https://numpy.org/doc/)
- Paho MQTT - Communication between Pi and Cloud - [Documentation](https://pypi.org/project/paho-mqtt/)
- GrovePi - For the GrovePi shield, LCD, and sensors - [Documentation](https://github.com/DexterInd/GrovePi)

### Web App
The web app uses these third-party software and frameworks:
- Flask - Web framework for the web app - [Documentation](https://flask.palletsprojects.com/en/stable/)
- Flask-Bootstrap - Bootstrap CSS integration for Flask - [Documentation](https://pythonhosted.org/Flask-Bootstrap/)
- Flask-Login - User authentication for the web app - [Documentation](https://flask-login.readthedocs.io/en/latest/)
- SQLAlchemy - Object-relational mapper for the web app's database - [Documentation](https://docs.sqlalchemy.org/en/20/)
- Gunicorn - WSGI HTTP server for running the web app in production - [Documentation](https://gunicorn.org/)
- Websocket-client - Used for receiving real-time updates from the Thingsboard API - [Documentation](https://websocket-client.readthedocs.io/en/latest/)
- Plotly - Used for displaying graphs on the web app - [Documentation](https://docs.plotly.com/)
- Whitenoise - Used for serving static files in production - [Documentation](https://whitenoise.readthedocs.io/en/latest/)
- HTTPX - Used for making HTTP requests to the Thingsboard API and bin collection date API - [Documentation](https://www.python-httpx.org/)
- PostgreSQL - Production database for the web app - [Documentation](https://www.postgresql.org/docs/)
- SQLite - Development database for the web app - [Documentation](https://sqlite.org/docs.html)
- Mailgun - Used for sending email notifications to users - [Documentation](https://documentation.mailgun.com/)

## Troubleshooting
- Invalid device IDs set when registering on the web app can cause issues with retrieving telemetry data. As there is no way to edit device IDs after registration, users must make sure their device IDs are correct.

## Development Docs
- [Thingsboard API Docs](./docs/Thingsboard-API-Integration.md)
