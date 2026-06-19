from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

bcrypt = Bcrypt()
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])

def get_by_id(model, id):
    return model.query.get(id)
