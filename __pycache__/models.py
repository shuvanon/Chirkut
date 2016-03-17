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
    
    def get_posts(self):
        return Post.select().where (
            (Post.user == self)
        )
    def get_stream(self):
        
        return Post.select().where(
            (Post.user == self)
        )

    @classmethod 
    def create_user(cls,user_name,email,password, admin=False):
        try:
            with DATABASE.transaction():
                cls.create(
                    user_name=user_name,
                    email=email,
                    password=generate_password_hash(password),
                    is_admin=admin)
        except IntegrityError:
            raise ValueError("User Already exists")

class Post(Model):
    timestamp = DateTimeField(default=datetime.datetime.now)
    
    user = ForeignKeyField(
        rel_model=User, 
        related_name='posts'
    )
    content = TextField()

    class Meta:
        database = DATABASE
        order_by = ('-timestamp',)

def initialize():
    DATABASE.connect()
    DATABASE.create_tables([User, Post],safe=True)
    DATABASE.close()
