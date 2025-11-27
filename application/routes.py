from flask import Flask, render_template, flash, request, redirect, url_for
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from application.webforms import LoginForm, PostForm, UserForm, PasswordForm, NamerForm, RequestResetForm, ResetPasswordForm
from flask_mail import Message, Mail
from application import server, db, mail, session
from application.models import Users, History, Instrument
from itsdangerous import URLSafeTimedSerializer as Serializer
from application.dash_apps import instrument_app, energy_app, emc_emission_with_bands, emc_projects_dashboard, motor_driver_report
from application.log_events import log_event

from application import server

with server.app_context():
    # data_visualization.init_app(server)

    energy_app.init_app(server)

    emc_emission_with_bands.init_app(server)

    emc_projects_dashboard.init_app(server)

    instrument_app.init_app(server)

    # data_file.init_app(server)

    motor_driver_report.init_app(server)


@server.route('/')
def index():
    return render_template('index.html')

# Create Login Page
@server.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user:
            # Check the hash
            if check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                log_event('Logged in', session)
                flash("Login Succesfull!!")
                return redirect(url_for('home'))
            else:
                flash("Wrong Password - Try Again!")
        else:
            flash("That User Doesn't Exist! Try Again...")

    return render_template('login.html', form=form)


# Create Logout Page
@server.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    log_event('Logged out', session)
    logout_user()
    flash("You Have Been Logged Out!  Thanks For Stopping By...")
    return redirect(url_for('index'))


# Create Dashboard Page
@server.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UserForm()
    id = current_user.id
    name_to_update = Users.query.get_or_404(id)
    if request.method == "POST":

        name_to_update.email = request.form['email']
        name_to_update.username = request.form['username']

        try:
            db.session.commit()
            log_event('Updated profile', session)
            flash("User Updated Successfully!")
            return render_template("profile.html",
                                   form=form,
                                   name_to_update=name_to_update)
        except:
            flash("Error!  Looks like there was a problem...try again!")
            return render_template("profile.html",
                                   form=form,
                                   name_to_update=name_to_update)
    else:
        return render_template("profile.html",
                               form=form,
                               name_to_update=name_to_update,
                               id=id)

@server.route('/delete/<int:id>')
@login_required
def delete(id):
    # Check logged in id vs. id to delete
    if id == current_user.id:
        user_to_delete = Users.query.get_or_404(id)
        name = None
        form = UserForm()

        try:
            db.session.delete(user_to_delete)
            db.session.commit()
            log_event('Profile deleted', session)
            flash("User Deleted Successfully!!")

            our_users = Users.query.order_by(Users.date_added)
            return render_template("register.html",
                                   form=form,
                                   name=name,
                                   our_users=our_users)

        except:
            flash("Whoops! There was a problem deleting user, try again...")
            return render_template("register.html",
                                   form=form, name=name, our_users=our_users)
    else:
        flash("Sorry, you can't delete that user! ")
        return redirect(url_for('home'))


# Update Database Record
@server.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    form = UserForm()
    name_to_update = Users.query.get_or_404(id)
    if request.method == "POST":
        # name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        # name_to_update.favorite_color = request.form['favorite_color']
        name_to_update.username = request.form['username']
        try:
            db.session.commit()
            flash("User Updated Successfully!")
            return render_template("update.html",
                                   form=form,
                                   name_to_update=name_to_update, id=id)
        except:
            flash("Error!  Looks like there was a problem...try again!")
            return render_template("update.html",
                                   form=form,
                                   name_to_update=name_to_update,
                                   id=id)
    else:
        return render_template("update.html",
                               form=form,
                               name_to_update=name_to_update,
                               id=id)


@server.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    name = None
    form = UserForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user is None:
            # Hash the password!!!

            session['username'] = form.username.data
            session['password'] = form.password_hash.data
            session['email'] = form.email.data

            token = generate_verification_token(form.email.data)
            verify_url = url_for('verify_email', token=token, _external = True)
            html = render_template('verify_email.html', verify_url=verify_url)
            msg = Message(subject='Email verification',
                          sender="mps.lab.efficiency.test@gmail.com",
                          recipients=[form.email.data],
                          body=f"Please verify your email address",
                          html=html
                          )

            mail.send(msg)
            flash("A verification email has been sent to your email adress.")

    our_users = Users.query.order_by(Users.date_added)

    return render_template("register.html",
                           form=form,
                           name=name,
                           our_users=our_users)




@server.route('/verify/<token>')
def verify_email(token):
    email = confirm_verification_token(token)
    if not email:
        flash('The verification link is invalid or has expired.')
        return redirect(url_for('register'))

    form = UserForm()

    hashed_pw = generate_password_hash(session['password'], 'pbkdf2:sha256')
    user = Users(username=session['username'], email=session['email'], password_hash=hashed_pw)
    db.session.add(user)
    db.session.commit()

    name = form.username.data
    form.username.data = ''
    form.email.data = ''
    form.password_hash.data = ''

    log_event('User registered', session)
    flash("User Added Successfully!")

    our_users = Users.query.order_by(Users.date_added)

    return render_template("register.html",
                           form=form,
                           name=name,
                           our_users=our_users)

s = Serializer(server.config['SECRET_KEY'])
def generate_verification_token(email):

    return s.dumps(email, salt='email-confirm')

def confirm_verification_token(token, expiration=3600):
    try:
        return s.loads(token, salt='email-confirm', max_age=expiration)
    except:
        print('q')

# Create a route decorator
@server.route('/home')
@login_required
def home():
    categories = {
        'Test_Automatization': {
            'image': 'test_automatization.jpg',
            'subcategories': {

            }
        },
        'Data_Visualization': {
            'image': 'data_visualization.avif',
            'subcategories': {
                'EMC Lab | Emission With Bands': 'emc_emission_with_bands_interface',
                'EMC Lab | Data File': 'data_file_interface',
                'EMC Lab | Data Visualization': 'data_visualization_interface',
                'Motor Driver | Motor Driver Report': 'motor_driver_report_interface'
            }
        },
        'Lab_Management': {
            'image': 'lab_management.webp',
            'subcategories': {
                'EMC Lab | Inventory': 'http://10.10.150.118:8888',
                'EMC Lab | Project Management': 'emc_project_dashboard_interface',
                'EMC Lab | Energy': url_for('energy_interface'),
            }
        }
    }
    return render_template('home.html', categories=categories)


# Create Custom Error Pages

# Invalid URL
@server.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


# Internal Server Error
@server.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500


# Create Password Test Page
@server.route('/test_pw', methods=['GET', 'POST'])
def test_pw():
    email = None
    password = None
    pw_to_check = None
    passed = None
    form = PasswordForm()

    # Validate Form
    if form.validate_on_submit():
        email = form.email.data
        password = form.password_hash.data
        # Clear the form
        form.email.data = ''
        form.password_hash.data = ''

        # Lookup User By Email Address
        pw_to_check = Users.query.filter_by(email=email).first()

        # Check Hashed Password
        passed = check_password_hash(pw_to_check.password_hash, password)

    return render_template("test_pw.html",
                           email=email,
                           password=password,
                           pw_to_check=pw_to_check,
                           passed=passed,
                           form=form)

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender="mps.lab.efficiency.test@gmail.com",
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_password_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)

@server.route("/reset_password_request", methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html', title='Reset Password', form=form)


@server.route("/reset_password_token/<token>", methods=['GET', 'POST'])
def reset_password_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = Users.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_password_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, 'pbkdf2:sha256')
        user.password_hash = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password_token.html', title='Reset Password', form=form)

admin = Admin(server, name='MyApp')
admin.add_view(ModelView(Users, db.session))

# def log_event(action):
#     history = History(
#         # id = current_user.id if current_user.is_authenticated else None,
#         timestamp = datetime.datetime.now(),
#         username = current_user.username if action != 'User registered' else session['username'],
#         action = action,
#     )
#     db.session.add(history)
#     db.session.commit()

@server.route('/history')
@login_required
def history():
    events = History.query.order_by(History.timestamp.desc()).limit(42)
    return render_template('history.html', events=events)

@server.route('/instrument', methods=['GET', 'POST'])
@login_required
def instrument():
    return render_template('instrument.html')

@server.route('/energy_interface', methods=['GET', 'POST'])
@login_required
def energy_interface():
    return render_template('energy_interface.html')

@server.route('/emc_emission_with_bands_interface', methods=['GET', 'POST'])
@login_required
def emc_emission_with_bands():
    return render_template('emc_emission_with_bands_interface.html')

@server.route('/emc_project_dashboard_interface', methods=['GET', 'POST'])
@login_required
def emc_project_dashboard_interface():
    return render_template('emc_project_dashboard_interface.html')

# @server.route('/data_file_interface', methods=['GET', 'POST'])
# @login_required
# def data_file_interface():
#     return render_template('data_file_interface.html')

# @server.route('/data_visualization_interface', methods=['GET', 'POST'])
# @login_required
# def data_visualization_interface():
#     return render_template('data_visualization_interface.html')

@server.route('/motor_driver_report_interface', methods=['GET', 'POST'])
@login_required
def motor_driver_report_interface():
    return render_template('motor_driver_report_interface.html')


