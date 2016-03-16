import datetime
from flask.ext.bcrypt import *
from flask.ext.login import UserMixin
from peewee import *

DATABASE = SqliteDatabase('social.db')

class User(UserMixin, Model):
    username = CharField(unique=True)
    email = CharField(unique=True)
    password = CharField(max_length=100)
    joined_at = DateTimeField(default=datetime.datetime.now)
    is_admin = BooleanField(default=False)

    class Meta:
        database = DATABASE
        order_by = ('-joined_at',)

    @classmethod 
    def create_user(cls,user_name,email,password, admin=False):
        try:
            cls.create(
                user_name=user_name,
                email=email,
                password=generate_password_hash(password),
                is_admin=admin)
        except IntegrityError:
            raise ValueError("User Already exists")

def initialize():
    DATABASE.connect()
    DATABASE.create_tables([User],safe=True)
    DATABASE.close()
