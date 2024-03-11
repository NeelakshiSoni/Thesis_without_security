import os

# Define the base directory of your Flask app
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Define the directory for your database volume relative to the app's base directory
DATAVOL = os.path.join(BASE_DIR, "accountsvol")

# Path to the DB file.
SQLALCHEMY_DATABASE_URI_SHORT = os.path.join(DATAVOL, 'users.db')

# SQLLite URI required by the Flask-SQLAlchemy extension.
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + SQLALCHEMY_DATABASE_URI_SHORT

# Path to the SQLAlchemy-migrate file


# To turn off the Flask-SQLAlchemy event system and disable the
# annoying warning (likely to be fixed in Flask-SQLAlchemy v3).
SQLALCHEMY_TRACK_MODIFICATIONS = False

