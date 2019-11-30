from flaskblog import login_manager
from flaskblog import mongo
from flask_login import UserMixin
from flaskblog import bcrypt

class User:
    def __init__(self, username):
        self.username = username
    @staticmethod
    def is_authenticated():
        return True

    @staticmethod
    def is_active():
        return True

    @staticmethod
    def is_anonymous():
        return False

    def get_id(self):
        return self.username

    @staticmethod
    def check_password(password_hash, password):
        return bcrypt.check_password_hash(password_hash, password)


@login_manager.user_loader
def load_user(username):
    u = mongo.db.regUser.find_one({"email_id": username})
    if not u:
        return None
    return User(username=u['email_id'])

