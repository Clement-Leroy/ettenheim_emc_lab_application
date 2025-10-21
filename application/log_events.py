from application.models import History
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
import datetime
from application import server, db, mail

def log_event(action, session):
    history = History(
        # id = current_user.id if current_user.is_authenticated else None,
        timestamp = datetime.datetime.now(),
        username = current_user.username if action != 'User registered' else session['username'],
        action = action,
    )
    db.session.add(history)
    db.session.commit()