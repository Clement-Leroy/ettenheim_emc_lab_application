from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from celery import Celery, Task

class FlaskTask(Task):
    abstract = True
    def __call__(self, *args: object, **kwargs: object) -> object:
        app = self.app.flask_app
        with app.app_context():
            return super().__call__(*args, **kwargs)

def celery_init_app(app: Flask) -> Celery:
    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.flask_app = app
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app