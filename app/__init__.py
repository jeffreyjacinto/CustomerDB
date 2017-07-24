from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, static_folder='static')
app.config.from_object('config')
db = SQLAlchemy(app)

@app.template_filter('proto_fieldlist')
def prototype_fieldlist(fieldlist):
	fieldlist.append_entry()
	return fieldlist.pop_entry()

from app import views, models