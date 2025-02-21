from peewee import *

from ..config import static
from .maimaidx_error import UserNotBindError

db = SqliteDatabase(static / 'user.db')


class UserModel(Model):
    
    class Meta:
        database = db


class User(UserModel):
    
    UserID = TextField(primary_key=True)
    QQID = BigIntegerField()
    
    class Meta:
        table_name = 'User'


db.create_tables([User])


def get_user(userid: str) -> User:
    record: Select = User.select().where(User.UserID == userid)
    if record:
        return record.get()
    else:
        raise UserNotBindError


def insert_user(userid: str, qqid: int) -> bool:
    try:
        User.insert(UserID=userid, QQID=qqid).execute()
        return True
    except:
        return False
    

def update_user(userid: str, qqid: int) -> bool:
    try:
        User.update(QQID=qqid).where(User.UserID == userid).execute()
        return True
    except:
        return False


def delete_user(userid: str) -> bool:
    try:
        User.delete().where(User.UserID == userid).execute()
        return True
    except:
        return False