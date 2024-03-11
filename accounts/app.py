from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('db_config')
db = SQLAlchemy(app)


# Additional app configuration and extensions go here
