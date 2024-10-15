from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


fake_users_db = {
    "admin": {
        "username": "admin",
        "password_hash": pwd_context.hash("admin"),
        "role": "admin"
    },
    "user": {
        "username": "user",
        "password_hash": pwd_context.hash("user"),
        "role": "user"
    },

    "manager": {
        "username": "manager",
        "password_hash": pwd_context.hash("manager"),
        "role": "manager"
    }
}