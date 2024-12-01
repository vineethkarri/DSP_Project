from app import db
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken
from flask_login import UserMixin


key = Fernet.generate_key()
cipher_suite = Fernet(key)


def encrypt_data(data):
    data_str = str(data)
    encrypted_data = cipher_suite.encrypt(data_str.encode())
    return encrypted_data


def decrypt_data(data):
    try:
        decrypted_data = cipher_suite.decrypt(data)
        return decrypted_data.decode('utf-8')  # Assuming your data is stored as utf-8
    except (InvalidToken, UnicodeDecodeError):
        return None


class HealthRecord(db.Model):
    __tablename__ = 'HealthRecord'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    weight = db.Column(db.Float)
    height = db.Column(db.Float)
    health_history = db.Column(db.String(100))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.LargeBinary)  # Change the column type to LargeBinary for storing encrypted data
    group = db.Column(db.String(1))  # Assuming 'H' or 'R' as the group values

    def set_password(self, password):
        encrypted_password = encrypt_data(password)
        self.password = encrypted_password

    def check_password(self, password):
        decrypted_password = decrypt_data(self.password)
        return password == decrypted_password
