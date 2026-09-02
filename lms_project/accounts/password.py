import bcrypt
def hash_password(password):
    salt=bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"),salt).decode("utf-8")
def check_password(password,db_pass):
    return bcrypt.checkpw(password.encode("utf-8"),db_pass.encode("utf-8"))

