import os

DD_URL = os.environ.get("DD_URL", "https://defectdojo.example.com").rstrip("/")
DD_API_KEY = os.environ.get("DD_API_KEY", "")
DD_TIMEOUT = int(os.environ.get("DD_TIMEOUT", "30"))
LOG_FILE = os.environ.get("LOG_FILE", "logs/triage.log")
SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
