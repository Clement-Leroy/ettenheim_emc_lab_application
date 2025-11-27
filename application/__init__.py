from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_ckeditor import CKEditor
from flask_migrate import Migrate
from celery import Celery, Task
from .extensions import celery_init_app

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        CELERY=dict(
            broker_url="redis://localhost",
            result_backend="redis://localhost",
            task_ignore_result=True,
        ),
    )
    app.config.from_prefixed_env()
    celery_init_app(app)
    return app

server = create_app()
ckeditor = CKEditor(server)
# server.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@database:3306/emc_lab_database'
server.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@localhost:3306/emc_lab_database'
server.config['SECRET_KEY'] = "my super secret key that no one is supposed to know"
server.config['SECRET_NAME'] = 'localhost:5000'
server.config['APPLICATION_ROOT'] = '/'
server.config['PREFERED_URL_SCHEME'] = 'http'

UPLOAD_FOLDER = 'static/images/'
server.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(server)
migrate = Migrate(server, db)

login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = 'login'

server.config['MAIL_SERVER'] = 'smtp.gmail.com'
server.config['MAIL_PORT'] = 587
server.config['MAIL_USE_TLS'] = True
server.config['MAIL_USE_SSL'] = False
server.config['MAIL_USERNAME'] = "mps.lab.efficiency.test@gmail.com"
server.config['MAIL_PASSWORD'] = "ufno uvbw cxys youh"

mail = Mail(server)

session = {}

from application import routes




