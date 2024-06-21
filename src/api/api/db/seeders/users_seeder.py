from models.user import User
from sqlalchemy import Table
from sqlalchemy.event import listens_for


@listens_for(User.__table__, "after_create")
def insert_rows(target: Table, connection, **kw):
    user = User(email="admin@test.nl")
    user.set_password("passpass")

    connection.execute(
        target.insert(), {"email": user.email, "password_digest": user.password_digest}
    )
