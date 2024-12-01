from flask import Blueprint, render_template, request, redirect, url_for, session, Flask, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_principal import Principal, Permission
from app.models import db, HealthRecord, encrypt_data
from config import Config
import pandas as pd

bp = Blueprint('main', __name__)
login_manager = LoginManager()
login_manager.login_view = 'main.login'

principal = Principal()

# Define roles
admin_permission = Permission('admin')
readonly_permission = Permission('readonly')

from .models import User


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize the SQLAlchemy instance with the app
    db.init_app(app)

    # Initialize login manager and principal
    login_manager.init_app(app)
    principal.init_app(app)

    # Register blueprints or other configurations
    from .routes import bp as main_bp  # Import route definitions
    app.register_blueprint(main_bp)

    return app


# authentication and authorization decorators
@admin_permission.require(http_exception=403)
def admin_route():
    pass


@readonly_permission.require(http_exception=403)
def readonly_route():
    pass


# Helper functions to fetch data based on user group
def get_data_for_group_H():
    # Fetch health records excluding first_name and last_name
    records = HealthRecord.query.all()

    data = []
    for record in records:
        data.append({
            'first_name': record.first_name,
            'last_name': record.last_name,
            'age': record.age,
            'gender': record.gender,
            'weight': record.weight,
            'height': record.height,
            'health_history': record.health_history,
        })

    return data


def get_data_for_group_R():
    # Fetch health records excluding first_name and last_name
    records = HealthRecord.query.all()

    data = []
    for record in records:
        data.append({
            'age': record.age,
            'gender': record.gender,
            'weight': record.weight,
            'height': record.height,
            'health_history': record.health_history,
        })

    return data


@bp.route('/insert_data')
def insert_data():
    file_path = r"C:\Users\karri\PycharmProjects\pythonProject4\userdetials.xlsx"
    df = pd.read_excel(file_path)

    for index, row in df.iterrows():
        if row['gender'] not in ['Male', 'Female']:
            row['gender'] = 'Male'  # or 'Female' based on your choice for non-standard values

        age_encrypted = encrypt_data(row['age'])
        gender_encrypted = encrypt_data(row['gender'])
        health_history_encrypted = encrypt_data(row['health_history'])

        new_record = HealthRecord(
            first_name=row['first_name'],
            last_name=row['last_name'],
            age=row['age'],
            gender=row['gender'],
            weight=row['weight'],
            height=row['height'],
            health_history=row['health_history']
        )
        db.session.add(new_record)

    db.session.commit()
    return 'Data inserted successfully!'


@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        group = request.form['group']  # Add this line to get the group from the form

        new_user = User(username=username, group=group)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        # Log the user in after signup
        login_user(new_user)

        return redirect(url_for('main.dashboard'))

    return render_template('signup.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            # Log the user in after successful login
            login_user(user)

            return redirect(url_for('main.dashboard'))

        else:
            return render_template('login.html', message='Invalid username or password')

    return render_template('login.html')


@bp.route('/home')
def home():
    # Render your home page, which may contain signup and login forms
    return render_template('home.html')

@bp.route('/')
def redirect_home():
    return redirect(url_for('main.home'))


@bp.route('/dashboard')
@login_required
def dashboard():
    # Assuming you have a function to fetch data based on user group
    if current_user.group == 'H':
        health_data = get_data_for_group_H()
    elif current_user.group == 'R':
        health_data = get_data_for_group_R()
    else:
        # Handle the case where user group is not set
        flash('Invalid user group', 'error')
        return redirect(url_for('main.login'))

    return render_template('dashboard.html', health_data=health_data)


@bp.route('/add_patient', methods=['GET', 'POST'])
@login_required
def add_patient():
    if current_user.group == 'H':
        if request.method == 'POST':
            # Get form data
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            age = request.form['age']
            gender = request.form['gender']
            weight = request.form['weight']
            height = request.form['height']
            health_history = request.form['health_history']

            # Create a new HealthRecord object
            new_record = HealthRecord(
                first_name=first_name,
                last_name=last_name,
                age=age,
                gender=gender,
                weight=weight,
                height=height,
                health_history=health_history
            )

            # Add the new record to the database
            db.session.add(new_record)
            db.session.commit()

            flash('New patient added successfully!', 'success')

            return redirect(url_for('main.dashboard'))

        return render_template('add_patient.html')

    else:
        flash('Invalid user group.', 'error')
        return redirect(url_for('main.dashboard'))


@bp.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('main.login'))

