# Imports
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os 
from flask import Flask, request, current_app, url_for
from flask_scss import Scss
from flask_admin import Admin
from flask_admin.menu import MenuLink
from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
#scss = Scss()
csrf = CSRFProtect()
mail = Mail()
my_admin = Admin(name='MTG Stats Admin')

# My App
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    my_admin.init_app(app)
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    # Lazy import Admin views AFTER blueprints/models are ready
    def register_admin_views():
        try:
            from app.models import (User, Player, Deck, GameSession, GameResult, ColorIdentity, DeckColor)
            from app.admin import (SecureModelView, UserAdmin, PlayerAdmin, DeckAdmin, 
                                GameSessionAdmin, GameResultAdmin, ColorIdentityAdmin,MyAdminIndexView,DeckColorAdmin)
            from flask_admin import AdminIndexView
            
            my_admin.add_link(MenuLink(
                name='🏠 Back to MTG Stats',
                category='',  # Top level
                url='/'
            ))
            
            my_admin.add_view(UserAdmin(User, db.session))
            my_admin.add_view(PlayerAdmin(Player, db.session))
            my_admin.add_view(DeckAdmin(Deck, db.session))
            my_admin.add_view(GameSessionAdmin(GameSession, db.session))
            my_admin.add_view(GameResultAdmin(GameResult, db.session))
            my_admin.add_view(ColorIdentityAdmin(ColorIdentity, db.session))
            my_admin.add_view(DeckColorAdmin(DeckColor, db.session))

            #print("✅ Admin views registered successfully")
            
        except ImportError as e:
            print(f"⚠️  Admin views skipped: {e}")
            print("Create app/admin.py with SecureModelView classes")
        
    register_admin_views()
    #print(f"Admin views registered: {len(my_admin._views)}")
    
    if not app.debug and not app.testing:
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'],
                        app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                toaddrs=app.config['ADMINS'], subject='Microblog Failure',
                credentials=auth, secure=secure)
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)
            
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/keymtg.log',
                                          maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('KeyMTG statup')
    return app

from app import models  # This runs AFTER create_app() completes
