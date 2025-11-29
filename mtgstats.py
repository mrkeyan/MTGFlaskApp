import sqlalchemy as sa
import sqlalchemy.orm as so
from app import create_app, db
from app.models import User, Player, Deck, GameSession, GameResult, ColorIdentity
from app.admin import (  # Import your admin views
    SecureModelView, UserAdmin, PlayerAdmin, DeckAdmin, 
    GameSessionAdmin, GameResultAdmin
)
app = create_app()

from app import my_admin

@app.shell_context_processor
def make_shell_context():
    return {
        'sa': sa, 
        'so': so, 
        'db': db, 
        'User': User, 
        'Player': Player, 
        'Deck': Deck, 
        'GameSession': GameSession, 
        'GameResult': GameResult, 
        'ColorIdentity': ColorIdentity,
        # Admin objects for testing
        'my_admin': my_admin,
        'SecureModelView': SecureModelView,
        'UserAdmin': UserAdmin,
        'PlayerAdmin': PlayerAdmin,
        'DeckAdmin': DeckAdmin,
        'GameSessionAdmin': GameSessionAdmin,
        'GameResultAdmin': GameResultAdmin
    }