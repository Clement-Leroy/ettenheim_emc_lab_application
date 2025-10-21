from datetime import datetime
from itsdangerous import URLSafeTimedSerializer as Serializer
from application import db, login_manager, server
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# Create Model
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    admin = db.Column(db.Boolean(), default=False, nullable=False)

    # Do some password stuff!
    password_hash = db.Column(db.String(128))

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(server.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(server.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return Users.query.get(user_id)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute!')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Create A String
    def __repr__(self):
        return '<Username %r>' % self.username


class History(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    username = db.Column(db.String(20), nullable=False, unique=True)
    action = db.Column(db.String(120), nullable=False, unique=True)

class Instrument(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(120), nullable=False)
    brand = db.Column(db.String(120), nullable=False)
    model = db.Column(db.String(120), nullable=False)
    ip = db.Column(db.Text, nullable=False, unique=True)
    port = db.Column(db.Integer)

class Energy(db.Model, UserMixin):
    date = db.Column(db.DateTime, default=datetime.utcnow, primary_key=True, unique=True, nullable=False)
    consumption = db.Column(db.Double, nullable=True)
    price = db.Column(db.Float, nullable=True)

class emc_emission_with_bands_limits(db.Model, UserMixin):
    limit_name = db.Column(db.String(120), nullable=False, primary_key=True)
    group_name = db.Column(db.String(120), nullable=False)
    band_name = db.Column(db.String(120), nullable=False)
    f_start = db.Column(db.Float, nullable=True)
    f_stop = db.Column(db.Float, nullable=True)
    level_start = db.Column(db.Float, nullable=True)
    level_stop = db.Column(db.Float, nullable=True)
    detector = db.Column(db.String(120), nullable=False)
    rbw = db.Column(db.Float, nullable=True)
    interpolation = db.Column(db.String(120), nullable=False)
    measurement_time = db.Column(db.Float)
    frequency_step = db.Column(db.Float)

