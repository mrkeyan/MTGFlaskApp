# app/admin.py
from flask import redirect, url_for, request
from flask_login import current_user
from flask_admin.contrib.sqla import ModelView
from app.models import (User, Player, Deck, ColorIdentity, GameSession, GameResult, DeckColor)
from flask_admin import AdminIndexView
from flask_admin.menu import MenuLink
from sqlalchemy import func

class SecureModelView(ModelView):
    def is_accessible(self):
        return (current_user.is_authenticated and current_user.is_admin)
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login', next=request.url))

class AdminOnlyView(SecureModelView):  # Same as SecureModelView
    pass

class MyAdminIndexView(AdminIndexView):
    def get_urls(self):
        return super(MyAdminIndexView, self).get_urls() + [
            ('/', self.index),
        ]
    
    # Add menu link directly
    def create_menu_links(self):
        links = super(MyAdminIndexView, self).create_menu_links()
        links.insert(0, MenuLink(
            name='<i class="fa fa-home"></i> Back to Site',
            category='Navigation',
            url=url_for('main.index')
        ))
        return links
    
class UserAdmin(SecureModelView):
    column_list = ['username', 'email', 'is_admin', 'player']
    column_editable_list = ['username', 'email', 'is_admin']   # Toggle admin flag
    column_filters = ['is_admin']
    column_hide_backrefs = True
    column_searchable_list = ['username', 'email']

class PlayerAdmin(SecureModelView):
    column_list = ['player_name', 'user', 'wins', 'total_games', 'win_rate']
    column_editable_list = ['player_name']
    column_searchable_list = ['player_name']

class DeckAdmin(SecureModelView):
    column_list = ['deck_name', 'color_identity_code', 'color_identity_rel', 
                   'deck_owner', 'total_games', 'wins', 'win_rate']
    column_filters = ['color_identity_code', 'color_identity_rel', 'deck_owner']
    column_searchable_list = ['deck_name', 'color_identity_code']
    
    column_default_sort = [('deck_name', True)]  # Database column only
    
    column_labels = {
        'color_identity_code': 'Color Code',
        'color_identity_rel': 'Identity',
        'deck_owner': 'Owner',
        'total_games': 'Games',
        'wins': 'Wins',
        'win_rate': 'Win Rate'
    }
    
    # ✅ FIXED: 4 args (view, context, model, name)
    column_formatters = {
        'color_identity_code': lambda v, ctx, model, name: 
            f'{model.color_identity_code}',
            
        'win_rate': lambda v, ctx, model, name: 
            f'{model.win_rate:.1%}' if model.win_rate else '0%',
            
        'color_identity_rel': lambda v, ctx, model, name: 
            model.color_identity_rel.identity_name if model.color_identity_rel else 'None',
            
        'deck_owner': lambda v, ctx, model, name: 
            model.deck_owner.player_name if model.deck_owner else 'None'
    }
    
    form_excluded_columns = ['wins', 'win_rate', 'total_games']

class GameSessionAdmin(SecureModelView):
    column_list = ['game_date', 'gs_wincon', 'results']
    column_searchable_list = ['game_date']

class GameResultAdmin(SecureModelView):
    column_list = ['gr_session', 'player', 'deck', 'finish', 'eliminated_by']
    column_filters = ['player', 'deck', 'finish', 'gr_session']
    
class ColorIdentityAdmin(SecureModelView):
    column_list = ['code', 'identity_name']
    column_filters = ['code']
    
    # Custom column added via scaffold_list_columns
    def scaffold_list_columns(self):
        return ['code', 'identity_name', 'deck_count']
    
    column_formatters = {
        'deck_count': lambda view, ctx, model, name: len(model.deck_colors)
    }
    column_labels = {
        'deck_count': 'Total Decks'
    }

class DeckColorAdmin(SecureModelView):
    column_list = ['id', 'deck.deck_name', 'color.identity_name', 'color.code']
    column_labels = {
        'deck.deck_name': 'Deck',
        'color.identity_name': 'Color Name', 
        'color.code': 'Color Code'
    }
    column_searchable_list = ['deck.deck_name', 'color.code']
    column_filters = ['color.code', 'deck.deck_name']
    column_sortable_list = ['id']
