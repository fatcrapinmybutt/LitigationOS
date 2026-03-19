
from flask import Flask
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Register routes and logic
# (Omitted for brevity)
