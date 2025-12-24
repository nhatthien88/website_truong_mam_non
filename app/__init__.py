from flask import Flask
from dotenv import load_dotenv

from .config import Config
from .extensions import db, login_manager
from .models import User

def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .main.routes import bp as main_bp
    from .auth.routes import bp as auth_bp
    from .admin.routes import bp as admin_bp
    from .teacher.routes import bp as teacher_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(teacher_bp)

    from .utils import register_error_handlers
    register_error_handlers(app)

    return app
