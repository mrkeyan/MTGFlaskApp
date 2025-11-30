from datetime import date, datetime, timezone
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy import Table
from flask_login import UserMixin
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from time import time
import jwt
from app import db, login


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))

    is_admin: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False, nullable=True)
    # One-to-one relation to Player
    player_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('player.id'), nullable=True, unique=True)
    player: so.Mapped["Player"] = so.relationship("Player", back_populates="user", uselist=False)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)
    
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return db.session.get(User, id)

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))


class Player(db.Model):
    __tablename__ = 'player'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    player_name: so.Mapped[str] = so.mapped_column(sa.String(100), nullable=False, unique=True, index=True)

    # Connect back to User profile
    user: so.Mapped["User"] = so.relationship("User", back_populates="player", uselist=False)
    
    # Games played by this player
    games: so.Mapped[list["GameResult"]] = so.relationship(
        "GameResult", 
        back_populates="player", 
        foreign_keys="[GameResult.player_id]"  # String → Column reference
    )
    
    #one-to-many relationship to decks owned by this player
    decks: so.Mapped[list["Deck"]] = so.relationship("Deck", back_populates="deck_owner", cascade="all, delete-orphan")
    
    __table_args__ = (sa.Index('ix_player_player_name', 'player_name'),)
    
    @property
    def wins(self):
        #return sum(1 for game in self.games if game.finish == 1)
        # Only count games won (finish == 1) where total players in the session >= 4
        return sum(
            1
            for game in self.games
            if (
                game.finish == 1 and
                game.gr_session is not None and
                len(game.gr_session.results) >= 4
            )
        )
    
    @property
    def total_games(self):
        return len(self.games)
    
    @property
    def total_valid_games(self):
        return sum(
            1
            for game in self.games
            if (
                game.gr_session is not None and
                len(game.gr_session.results) >= 4
            )
        )
    
    @property
    def win_rate(self):
        return (self.wins / self.total_valid_games) if self.total_valid_games > 10 else 0

    def __repr__(self):
        return f"<Player {self.player_name}>"

class ColorIdentity(db.Model):
    __tablename__ = 'color_identity'
    code: so.Mapped[str] = so.mapped_column(sa.String(5), primary_key=True)
    identity_name: so.Mapped[str] = so.mapped_column(sa.String(20), nullable=False)
    
    deck_colors: so.Mapped[list["DeckColor"]] = so.relationship(
        "DeckColor", back_populates="color"
    )

class DeckColor(db.Model):
    __tablename__ = 'deck_colors'
    
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    deck_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('deck.id'), nullable=False, index=True)
    color_id: so.Mapped[str] = so.mapped_column(sa.ForeignKey('color_identity.code'), nullable=False, index=True)
    
    __table_args__ = (sa.UniqueConstraint('deck_id', 'color_id', name='uq_deck_color'),)
    
    deck: so.Mapped["Deck"] = so.relationship("Deck", back_populates="deck_colors")
    color: so.Mapped["ColorIdentity"] = so.relationship("ColorIdentity", back_populates="deck_colors")

class Deck(db.Model):
    __tablename__ = 'deck'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    deck_name: so.Mapped[str] = so.mapped_column(sa.String(100), nullable=False, unique=True)
    color_identity_code: so.Mapped[str] = so.mapped_column(sa.ForeignKey('color_identity.code'), nullable=False)
    color_identity_rel: so.Mapped[ColorIdentity] = so.relationship("ColorIdentity")
    
    # Owner foreign key
    owner_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('player.id'), nullable=True)
    deck_owner: so.Mapped["Player"] = so.relationship("Player", back_populates="decks")
    
    # NEW: DeckColor relationships
    deck_colors: so.Mapped[list["DeckColor"]] = so.relationship(
        "DeckColor", back_populates="deck", cascade="all, delete-orphan",overlaps="decks"
    )
    
    # SIMPLIFIED - no primaryjoin/secondaryjoin
    colors: so.Mapped[list["ColorIdentity"]] = so.relationship(
        "ColorIdentity",
        secondary="deck_colors",
        viewonly=True  # Read-only, no writes needed
    )   
    
    games: so.Mapped[list["GameResult"]] = so.relationship("GameResult", back_populates="deck")
        
    @property
    def color_count(self) -> int:
        """Number of colors in this deck (1-5)"""
        return len(self.colors)
    
    @property
    def is_five_color(self) -> bool:
        """True if deck uses all 5 colors"""
        return self.color_count == 5
    
    @property
    def wins(self):    
        return sum(
                1
                for game in self.games
                if (
                    game.finish == 1 and
                    game.gr_session is not None and
                    len(game.gr_session.results) >= 4
                )
            )
    
    @property
    def total_games(self):
        return len(self.games)
    
    @property
    def total_valid_games(self):
        return sum(
            1
            for game in self.games
            if (
                game.gr_session is not None and
                len(game.gr_session.results) >= 4
            )
        )
    
    @property
    def win_rate(self):
        return (self.wins / self.total_valid_games) if self.total_valid_games > 0 else 0

    def __repr__(self):
        return f"<Deck {self.deck_name} ({self.color_identity_rel})>"

class GameSession(db.Model):
    __tablename__ = 'game_session'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    game_date: so.Mapped[date] = so.mapped_column(sa.Date, nullable=False, default=lambda: date.today())
    gs_wincon: so.Mapped[str] = so.mapped_column(sa.Text, nullable=True)
    comments: so.Mapped[str] = so.mapped_column(sa.Text, nullable=True)
    
    results: so.Mapped[list["GameResult"]] = so.relationship("GameResult", back_populates="gr_session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<GameSession {self.id} on {self.game_date}>"

class GameResult(db.Model):
    __tablename__ = 'game_result'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    gr_session_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('game_session.id'), nullable=False, index=True)
    player_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('player.id'), nullable=False, index=True)
    deck_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('deck.id'), nullable=False, index=True)
    finish: so.Mapped[int] = so.mapped_column(nullable=False)
    eliminated_by_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('player.id'), nullable=True)
    eliminated_by: so.Mapped['Player'] = so.relationship('Player', foreign_keys=[eliminated_by_id])
    
    gr_session: so.Mapped["GameSession"] = so.relationship("GameSession", back_populates="results")
    player: so.Mapped["Player"] = so.relationship("Player", back_populates="games", foreign_keys=[player_id])
    deck: so.Mapped["Deck"] = so.relationship("Deck", back_populates="games")

    def __repr__(self):
        return (f"<GameResult {self.id} | Session: {self.gr_session_id} | Player: {self.player.player_name} | "
                f"Deck: {self.deck.deck_name} | Placement: {self.finish} | Eliminated By: "
                f"{self.eliminated_by.player_name if self.eliminated_by else 'N/A'}>")