import os

os.environ["WISDOMTWIN_USE_FIXTURES"] = "1"
os.environ["WISDOMTWIN_AUTH_DISABLED"] = "1"
os.environ["SLACK_CLIENT_ID"] = "local-test-client"
os.environ["SLACK_CONNECTOR_ENABLED"] = "true"
os.environ["GMAIL_CONNECTOR_ENABLED"] = "false"
os.environ["DRIVE_CONNECTOR_ENABLED"] = "false"
os.environ.pop("REDIS_URL", None)
os.environ.pop("OPENAI_API_KEY", None)
os.environ.pop("DATABASE_URL", None)
os.environ.pop("PUBLIC_BASE_URL", None)
os.environ.pop("RAILWAY_PUBLIC_URL", None)
