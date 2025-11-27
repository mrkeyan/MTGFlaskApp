from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, SelectField, TextAreaField, FieldList, FormField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Optional, NumberRange, Length
from wtforms.fields import DateField
from datetime import date
import sqlalchemy as sa
from app import db
from app.models import User, ColorIdentity, Player
        
class PlayerAddForm(FlaskForm):
    player_name = StringField('Player Name', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Add Player')
    

class GameResultForm(FlaskForm):
    deck_id = SelectField('Deck', coerce=int, validators=[DataRequired(),NumberRange(min=1)])
    player_id = SelectField('Player', coerce=int, validators=[DataRequired(),NumberRange(min=1)] )
    finish = IntegerField('Finish (Place)', validators=[DataRequired(),NumberRange(min=1, max=4)])
    eliminated_by_id = SelectField('Eliminated By', coerce=int, validators=[Optional()])
    
class CombinedGameEntryForm(FlaskForm):
    # GameSession fields
    game_date = DateField('Game Date', format='%Y-%m-%d', default=date.today)
    gs_wincon = StringField('Win Condition', validators=[Optional()])
    comments = TextAreaField('Comments', validators=[Optional()])
    # Nested multiple game result forms
    
    results = FieldList(FormField(GameResultForm), min_entries=4, max_entries=4)
    submit = SubmitField('Submit Game Session and Results')

class GameSessionEditForm(FlaskForm):
    game_date = DateField('Game Date', format='%Y-%m-%d', validators=[DataRequired()])
    gs_wincon = StringField('Win Condition', validators=[Optional()])
    comments = TextAreaField('Comments', validators=[Optional()])
    results = FieldList(FormField(GameResultForm), min_entries=4, max_entries=4)
    submit = SubmitField('Save Changes')    
    
class DeckForm(FlaskForm):
    deck_name = StringField('Deck Name', validators=[DataRequired(), Length(max=100)])
    color_identity_code = SelectField('Color Identity', coerce=str, validators=[DataRequired()])
    owner_id = SelectField('Owner (Player)', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Add Deck')

    def populate_choices(self):
        # Populate color identity choices dynamically from DB
        color_identities = db.session.query(ColorIdentity).all()
        self.color_identity_code.choices = [(ci.code, ci.identity_name) for ci in color_identities]
        
        # Populate player choices dynamically
        players = db.session.query(Player).all()
        self.owner_id.choices = [(player.id, player.player_name) for player in players]
        
        

class DeckEditForm(FlaskForm):
    deck_name = StringField('Deck Name', validators=[DataRequired(), Length(max=100)])
    color_identity_code = SelectField('Color Identity', coerce=str, validators=[DataRequired()])
    owner_id = SelectField('Owner (Player)', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Changes')
    
    def populate_choices(self):
        color_identities = db.session.query(ColorIdentity).all()
        self.color_identity_code.choices = [(ci.code, ci.identity_name) for ci in color_identities]
        players = db.session.query(Player).all()
        self.owner_id.choices = [(player.id, player.player_name) for player in players]
        
class PlayerEditForm(FlaskForm):
    player_name = StringField('Player Name', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Save Changes')
    