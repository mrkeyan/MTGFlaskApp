from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required
import sqlalchemy as sa
from sqlalchemy.orm import joinedload
from app import db
from app.main.forms import CombinedGameEntryForm, DeckForm, DeckEditForm, PlayerEditForm, GameSessionEditForm, PlayerAddForm
from app.models import User, Player, Deck, GameResult, GameSession, ColorIdentity,DeckColor
from collections import defaultdict
from app.main import bp


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    total_games = db.session.query(sa.func.count(GameResult.id)).scalar() or 0
    total_decks = Deck.query.count() or 0
    
    return render_template('index.html', 
                         title='MTG Commander Dashboard',
                         total_games=total_games,
                         total_decks=total_decks)


#Route for player data
@bp.route('/player/<int:id>')
def player_stats(id):
    player = Player.query.get_or_404(id)
    return render_template('player.html', player=player)
    
#Route for all player stats
@bp.route('/players')
def all_player_stats():
    players = Player.query.order_by(Player.player_name).all()
    return render_template('player_stats.html', players=players)

#Route for adding a player
@bp.route('/add_player', methods=['GET', 'POST'])
@login_required
def add_player():
    form = PlayerAddForm()
    if form.validate_on_submit():
        new_player = Player(player_name=form.player_name.data)
        db.session.add(new_player)
        db.session.commit()
        flash(f'Player "{new_player.player_name}" added successfully!', 'success')
        return redirect(url_for('main.all_player_stats'))
    return render_template('add_player.html', form=form)

    
#Route for add game
@bp.route('/add_game',methods=['GET','POST'])
@login_required
def add_game():
    form = CombinedGameEntryForm()

    # Populate choices for nested game result forms
    decks = Deck.query.all()
    players = Player.query.all()
    deck_choices = [(0, '--- Select Deck ---')] + [(deck.id, deck.deck_name) for deck in decks]
    player_choices = [(0, '--- Select Player ---')] + [(player.id, player.player_name) for player in players]
    eliminated_by_choices = [(0, '')] + [(player.id, player.player_name) for player in players]

    for subform in form.results:
        subform.deck_id.choices = deck_choices
        subform.player_id.choices = player_choices
        subform.eliminated_by_id.choices = eliminated_by_choices
    
    
    if form.validate_on_submit():
        new_session = GameSession(
            game_date=form.game_date.data,
            gs_wincon=form.gs_wincon.data,
            comments=form.comments.data
        )
        db.session.add(new_session)
        db.session.flush()
        
        for entry in form.results.entries:
            data = entry.data
            if not data['player_id'] or data['player_id'] == 0:
                continue
            gameresult = GameResult(
                gr_session_id=new_session.id,
                deck_id=data['deck_id'],
                player_id=data['player_id'],
                finish=data['finish'],
                eliminated_by_id=data['eliminated_by_id'] if data['eliminated_by_id']!= 0 else None
            )
            db.session.add(gameresult)

        db.session.commit()
        flash('Game session and results added successfully!')
        return redirect(url_for('main.game_results'))
    else:
        print(form.errors)

    # For GET or failed POST, fetch game results and render template with form
    flash('did not work')
    return render_template('add_game_entry.html', form=form)



#Route for all game results
@bp.route('/game_results')
def game_results():
    # For GET or failed POST, fetch game results and render template with form
    results = GameResult.query.order_by(GameResult.gr_session_id.desc(), GameResult.finish).all()
    
    sessions = defaultdict(list)
    for r in results:
        sessions[r.gr_session_id].append(r)
    return render_template('game_log.html', sessions=sessions)

@bp.route('/decks')
def all_deck_stats():
    #decks = Deck.query.order_by(Deck.owner_id).all()
    decks = (
        db.session.query(Deck)
        .options(joinedload(Deck.deck_owner))
        .join(Player, Deck.owner_id == Player.id)
        .order_by(Player.player_name)
        .all()
    )
    return render_template('deck_stats.html', decks=decks)

@bp.route('/get_decks_for_player/<int:player_id>')
@login_required
def get_decks_for_player(player_id):
    decks = Deck.query.filter_by(owner_id=player_id).all()
    deck_list = [{'id': deck.id, 'name': deck.deck_name} for deck in decks]
    return jsonify(deck_list)

@bp.route('/add_deck', methods=['GET', 'POST'])
@login_required
def add_deck():
    form = DeckForm()
    form.populate_choices()

    if form.validate_on_submit():
        new_deck = Deck(
            deck_name=form.deck_name.data,
            color_identity_code=form.color_identity_code.data,
            owner_id=form.owner_id.data
        )
        db.session.add(new_deck)
        db.session.commit()
        flash(f'Deck "{new_deck.deck_name}" added successfully!', 'success')
        return redirect(url_for('main.all_deck_stats'))  # or wherever you want to go next

    return render_template('add_deck.html', form=form)

@bp.route('/deck/edit/<int:deck_id>', methods=['GET', 'POST'])
@login_required
def edit_deck(deck_id):
    deck = Deck.query.get_or_404(deck_id)
    form = DeckEditForm(obj=deck)
    form.populate_choices()

    if form.validate_on_submit():
        deck.deck_name = form.deck_name.data
        deck.color_identity_code = form.color_identity_code.data
        deck.owner_id = form.owner_id.data
        db.session.commit()
        flash('Deck updated successfully!')
        return redirect(url_for('main.all_deck_stats'))
    return render_template('edit_deck.html', form=form, deck=deck)

@bp.route('/player/edit/<int:player_id>', methods=['GET', 'POST'])
@login_required
def edit_player(player_id):
    player = Player.query.get_or_404(player_id)
    form = PlayerEditForm(obj=player)  # pre-fill form with player data

    if form.validate_on_submit():
        player.player_name = form.player_name.data
        db.session.commit()
        flash('Player updated successfully!', 'success')
        return redirect(url_for('main.all_player_stats'))

    return render_template('edit_player.html', form=form, player=player)


@bp.route('/game_session/edit/<int:session_id>', methods=['GET', 'POST'])
@login_required
def edit_game_session(session_id):
    session = GameSession.query.get_or_404(session_id)
    form = GameSessionEditForm()

    # Prepare choices for nested forms
    decks = Deck.query.all()
    players = Player.query.all()
    deck_choices = [(0, '--- Select Deck ---')] + [(deck.id, deck.deck_name) for deck in decks]
    player_choices = [(0, '--- Select Player ---')] + [(player.id, player.player_name) for player in players]
    eliminated_choices = [(0, '')] + player_choices[1:]

    # Populate choices for each nested game result form in the form field list
    for subform in form.results:
        subform.deck_id.choices = deck_choices
        subform.player_id.choices = player_choices
        subform.eliminated_by_id.choices = eliminated_choices

    if request.method == 'GET':
        # Pre-fill form fields from session and its game results
        form.game_date.data = session.game_date
        form.gs_wincon.data = session.gs_wincon
        form.comments.data = session.comments

        # Populate each nested form with existing game result data
        game_results = sorted(session.results, key=lambda r: r.finish)  # or some stable order
        for i, gameresult in enumerate(game_results):
            if i < len(form.results):
                form.results[i].deck_id.data = gameresult.deck_id
                form.results[i].player_id.data = gameresult.player_id
                form.results[i].finish.data = gameresult.finish
                form.results[i].eliminated_by_id.data = gameresult.eliminated_by_id or 0  # handle None
            else:
                break

    elif form.validate_on_submit():
        # Update session fields
        session.game_date = form.game_date.data
        session.gs_wincon = form.gs_wincon.data
        session.comments = form.comments.data

        # Update each game result
        game_results = sorted(session.results, key=lambda r: r.finish)
        for i, entry in enumerate(form.results.entries):
            data = entry.data
            if i < len(game_results):
                gr = game_results[i]
                gr.deck_id = data['deck_id']
                gr.player_id = data['player_id']
                gr.finish = data['finish']
                gr.eliminated_by_id = data['eliminated_by_id'] if data['eliminated_by_id'] != 0 else None
            else:
                # Optional: handle case where more results submitted than exist
                pass

        db.session.commit()
        flash('Game session and results updated successfully!')
        return redirect(url_for('main.game_results'))

    return render_template('edit_game_session.html', form=form, session=session)



#API routes
@bp.route('/api/players')
def api_players():
    """JSON endpoint for player stats table"""
    players = Player.query.order_by(Player.player_name).all()
    return jsonify([{
        'id': p.id,
        'player_name': p.player_name,
        'wins': p.wins,  # Uses @property
        'total_games': p.total_games,
        'win_rate': float(p.win_rate)  # ✅ Raw decimal 0.42, NOT formatted string
    } for p in players])

@bp.route('/api/decks')
def api_decks():
    decks = Deck.query.options(joinedload(Deck.deck_owner)).all()
    
    deck_data = []
    for deck in decks:
        # Calculate win_rate from GameResult
        total_games = db.session.query(GameResult).filter_by(deck_id=deck.id).count()
        wins = db.session.query(GameResult).filter_by(deck_id=deck.id, finish=1).count()
        win_rate = wins / total_games if total_games > 0 else 0
        
        deck_data.append({
            'id': deck.id,
            'deck_name': deck.deck_name,
            'color_identity': getattr(deck.color_identity_rel, 'identity_name', deck.color_identity_code or ''),
            'deck_owner': deck.deck_owner.player_name if deck.deck_owner else 'N/A',
            'win_rate': win_rate,  # ← Raw number (0.42), not percentage string
            'edit_url': url_for('main.edit_deck', deck_id=deck.id)
        })
    return jsonify(deck_data)

@bp.route('/api/game_sessions')
def api_game_sessions():
    """JSON endpoint for game results/sessions"""
    results = GameResult.query.options(
        joinedload(GameResult.gr_session),
        joinedload(GameResult.player),
        joinedload(GameResult.deck),
        joinedload(GameResult.eliminated_by)
    ).order_by(GameResult.gr_session_id.desc(), GameResult.finish).all()
    
    sessions = {}
    for r in results:
        session_id = r.gr_session_id
        if session_id not in sessions:
            sessions[session_id] = {
                'session_id': session_id,
                'date': r.gr_session.game_date.strftime('%Y-%m-%d') if r.gr_session else '',
                'wincon': r.gr_session.gs_wincon or '',
                'results': []
            }
        sessions[session_id]['results'].append({
            'finish': r.finish,
            'player': r.player.player_name if r.player else '',
            'deck': r.deck.deck_name if r.deck else '',
            'eliminated_by': r.eliminated_by.player_name if r.eliminated_by else ''
        })
    
    return jsonify(list(sessions.values()))


@bp.route('/api/dashboard/kpis')
def api_dashboard_kpis():
    """Single endpoint for all dashboard KPIs"""
    # Total games
    total_games = db.session.query(sa.func.count(GameResult.id)).scalar() or 0
    
    # Unique players with games
    player_count = db.session.query(sa.func.count(sa.distinct(GameResult.player_id))).scalar() or 0
    
    # Average winrate
    avg_winrate = db.session.query(
        sa.func.avg((GameResult.finish == 1).cast(sa.Float))
    ).filter(GameResult.finish.isnot(None)).scalar() or 0
    
    # ✅ FIXED: Group by both ID and name
    top_deck_result = db.session.query(
        Deck.id,
        Deck.deck_name, 
        sa.func.count(GameResult.id).label('wins')
    ).join(GameResult, Deck.id == GameResult.deck_id)\
     .filter(GameResult.finish == 1)\
     .group_by(Deck.id, Deck.deck_name)\
     .order_by(sa.desc('wins')).first()
    
    top_deck_wins = top_deck_result.wins if top_deck_result else 0
    top_deck_name = top_deck_result.deck_name if top_deck_result else 'None'
    
    # Total decks
    total_decks = Deck.query.count() or 0
    
    return jsonify({
        'total_games': total_games,
        'player_count': player_count,
        'avg_winrate': float(avg_winrate),
        'top_deck_wins': top_deck_wins,
        'top_deck_name': top_deck_name,
        'total_decks': total_decks
    })

# 1st Chart: WUBRG from DeckColor (SINGLE COLORS)
@bp.route('/api/dashboard/colors')
def api_dashboard_colors():
    """WUBRG from Deck → DeckColor → ColorIdentity (SINGLE COLORS)"""
    color_data = db.session.query(
        ColorIdentity.code,
        ColorIdentity.identity_name,
        sa.func.count(DeckColor.id).label('count')
    ).join(DeckColor, ColorIdentity.code == DeckColor.color_id)\
     .join(Deck, DeckColor.deck_id == Deck.id)\
     .filter(ColorIdentity.code.in_(['W', 'U', 'B', 'R', 'G', 'C']))\
     .group_by(ColorIdentity.code, ColorIdentity.identity_name)\
     .order_by(sa.desc('count')).all()
    
    return jsonify([{
        'color': c.code,
        'name': c.identity_name,
        'count': c.count  # Remove int() wrapper
    } for c in color_data])

@bp.route('/api/dashboard/commander-identities')
def api_dashboard_commander_identities():
    """Commander identities from Deck.color_identity_code (with fallback)"""
    identity_data = db.session.query(
        Deck.color_identity_code.label('code'),
        sa.func.coalesce(ColorIdentity.identity_name, Deck.color_identity_code).label('name'),
        sa.func.count(Deck.id).label('count')
    ).outerjoin(ColorIdentity, Deck.color_identity_code == ColorIdentity.code)\
     .filter(Deck.color_identity_code.isnot(None))\
     .group_by(Deck.color_identity_code, ColorIdentity.identity_name)\
     .order_by(sa.desc('count')).all()
    
    return jsonify([{
        'color': row.code,
        'name': row.name,
        'count': row.count  # No int() needed
    } for row in identity_data])
