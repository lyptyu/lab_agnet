import bcrypt


def hash_password(password) -> str:
    """哈希密码"""
    return bcrypt.hashpw(password.encode('utf-8'),
                         bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(password.encode('utf-8'),
                          hashed_password.encode('utf-8'))
