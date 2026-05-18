import os
import secrets
from datetime import date
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from models import db, User, Strategy, Comment, Like, Tag
from forms import (RegistrationForm, LoginForm, StrategyForm, CommentForm, DeleteForm,
                   DiceForm, RouletteForm, SlotsForm, GuessForm, MinesStartForm)
from casino import DiceGame, RouletteGame, SlotGame, GuessNumberGame, MinesGame
from clicker import ClickerGame
from flask_migrate import Migrate
from sqlalchemy import or_

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///tdhub.db')
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'

clicker_game = ClickerGame()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '')
    if search_query:
        if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI']:
            strategies = Strategy.query.filter(
                Strategy.__ts_vector__.match(search_query)
            ).order_by(Strategy.created_at.desc()).paginate(page=page, per_page=6)
        else:
            strategies = Strategy.query.filter(
                or_(Strategy.title.ilike(f'%{search_query}%'),
                    Strategy.description.ilike(f'%{search_query}%'))
            ).order_by(Strategy.created_at.desc()).paginate(page=page, per_page=6)
    else:
        strategies = Strategy.query.order_by(Strategy.created_at.desc()).paginate(page=page, per_page=6)
    return render_template('index.html', strategies=strategies, search_query=search_query)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash('Вы успешно вошли!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Неверный email или пароль.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))

@app.route('/strategy/add', methods=['GET', 'POST'])
@login_required
def add_strategy():
    today = date.today()
    if current_user.last_strategy_date == today:
        flash('Вы уже опубликовали стратегию сегодня. Приходите завтра!', 'danger')
        return redirect(url_for('index'))
    form = StrategyForm()
    form.tags.choices = [(t.id, t.name) for t in Tag.query.order_by('name')]
    if form.validate_on_submit():
        strategy = Strategy(
            title=form.title.data,
            game=form.game.data,
            description=form.description.data,
            author=current_user
        )
        if form.image.data:
            image_file = form.image.data
            filename = secrets.token_hex(8) + '_' + secure_filename(image_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(filepath)
            strategy.image_filename = filename

        selected_tags = Tag.query.filter(Tag.id.in_(form.tags.data)).all()
        strategy.tags.extend(selected_tags)

        current_user.last_strategy_date = today
        db.session.add(strategy)
        db.session.commit()
        flash('Стратегия успешно добавлена!', 'success')
        return redirect(url_for('index'))
    return render_template('add_strategy.html', form=form)

@app.route('/strategy/<int:id>', methods=['GET', 'POST'])
def strategy_detail(id):
    strategy = Strategy.query.get_or_404(id)
    comment_form = CommentForm()
    delete_form = DeleteForm()
    if comment_form.validate_on_submit() and current_user.is_authenticated:
        today = date.today()
        if current_user.last_comment_date == today and current_user.last_comment_strategy_id == strategy.id:
            flash('Вы уже оставили комментарий к этой стратегии сегодня.', 'danger')
        else:
            comment = Comment(text=comment_form.text.data, author=current_user, strategy=strategy)
            current_user.last_comment_date = today
            current_user.last_comment_strategy_id = strategy.id
            db.session.add(comment)
            db.session.commit()
            flash('Комментарий добавлен.', 'success')
        return redirect(url_for('strategy_detail', id=strategy.id))
    comments = strategy.comments.order_by(Comment.created_at.desc()).all()
    user_liked = False
    if current_user.is_authenticated:
        user_liked = Like.query.filter_by(user_id=current_user.id, strategy_id=strategy.id).first() is not None
    return render_template('strategy_detail.html', strategy=strategy,
                           comment_form=comment_form, comments=comments,
                           delete_form=delete_form, user_liked=user_liked)

@app.route('/strategy/<int:id>/delete', methods=['POST'])
@login_required
def delete_strategy(id):
    strategy = Strategy.query.get_or_404(id)
    if strategy.user_id != current_user.id:
        flash('Вы не можете удалить чужую стратегию.', 'danger')
        return redirect(url_for('strategy_detail', id=id))
    if strategy.image_filename:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], strategy.image_filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    db.session.delete(strategy)
    db.session.commit()
    flash('Стратегия удалена.', 'success')
    return redirect(url_for('index'))

@app.route('/like/<int:strategy_id>', methods=['POST'])
@login_required
def like_strategy(strategy_id):
    strategy = Strategy.query.get_or_404(strategy_id)
    existing = Like.query.filter_by(user_id=current_user.id, strategy_id=strategy.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        if strategy.author.id != current_user.id:
            strategy.author.points = max(strategy.author.points - 1, 0)
            db.session.commit()
        liked = False
    else:
        like = Like(user_id=current_user.id, strategy_id=strategy.id)
        db.session.add(like)
        db.session.commit()
        if strategy.author.id != current_user.id:
            strategy.author.points += 1
            db.session.commit()
        liked = True
    return jsonify({'liked': liked, 'likes_count': strategy.likes.count()})

@app.route('/clicker')
@login_required
def clicker():
    return render_template('clicker.html', points=current_user.points)

@app.route('/clicker/state')
@login_required
def clicker_state():
    clicker_game.auto_click(current_user)
    db.session.commit()
    return jsonify(clicker_game.get_state(current_user))

@app.route('/clicker/click', methods=['POST'])
@login_required
def clicker_click():
    state = clicker_game.click(current_user)
    db.session.commit()
    return jsonify(state)

@app.route('/clicker/upgrade', methods=['POST'])
@login_required
def clicker_upgrade():
    data = request.get_json()
    upgrade_type = data.get('upgrade_type')
    result = clicker_game.buy_upgrade(current_user, upgrade_type)
    if 'error' in result:
        return jsonify(result), 400
    db.session.commit()
    return jsonify(result)

@app.route('/clicker/convert', methods=['POST'])
@login_required
def clicker_convert():
    result = clicker_game.convert(current_user)
    if 'error' in result:
        return jsonify(result), 400
    db.session.commit()
    return jsonify(result)

@app.route('/casino')
@login_required
def casino():
    return render_template('casino.html')

@app.route('/casino/dice', methods=['GET', 'POST'])
@login_required
def casino_dice():
    form = DiceForm()
    result = None
    if form.validate_on_submit():
        bet_amount = form.bet_amount.data
        if bet_amount > current_user.points:
            flash('Недостаточно баллов для такой ставки.', 'danger')
            return redirect(url_for('casino_dice'))
        current_user.points -= bet_amount
        db.session.commit()
        game = DiceGame()
        bet = {'amount': bet_amount, 'number': form.bet_number.data}
        result = game.play(bet)
        current_user.points += result['payout']
        db.session.commit()
    return render_template('dice.html', form=form, result=result, points=current_user.points)

@app.route('/casino/roulette', methods=['GET', 'POST'])
@login_required
def casino_roulette():
    form = RouletteForm()
    result = None
    if form.validate_on_submit():
        bet_amount = form.bet_amount.data
        if bet_amount > current_user.points:
            flash('Недостаточно баллов.', 'danger')
            return redirect(url_for('casino_roulette'))
        current_user.points -= bet_amount
        db.session.commit()
        game = RouletteGame()
        bet = {'amount': bet_amount, 'number': form.bet_number.data}
        result = game.play(bet)
        current_user.points += result['payout']
        db.session.commit()
    return render_template('roulette.html', form=form, result=result, points=current_user.points)

@app.route('/casino/slots', methods=['GET', 'POST'])
@login_required
def casino_slots():
    form = SlotsForm()
    result = None
    if form.validate_on_submit():
        bet_amount = form.bet_amount.data
        if bet_amount > current_user.points:
            flash('Недостаточно баллов.', 'danger')
            return redirect(url_for('casino_slots'))
        current_user.points -= bet_amount
        db.session.commit()
        game = SlotGame()
        bet = {'amount': bet_amount}
        result = game.play(bet)
        current_user.points += result['payout']
        db.session.commit()
    return render_template('slots.html', form=form, result=result, points=current_user.points)

@app.route('/casino/guess', methods=['GET', 'POST'])
@login_required
def casino_guess():
    form = GuessForm()
    result = None
    if form.validate_on_submit():
        bet_amount = form.bet_amount.data
        if bet_amount > current_user.points:
            flash('Недостаточно баллов.', 'danger')
            return redirect(url_for('casino_guess'))
        current_user.points -= bet_amount
        db.session.commit()
        game = GuessNumberGame()
        bet = {'amount': bet_amount, 'number': form.bet_number.data}
        result = game.play(bet)
        current_user.points += result['payout']
        db.session.commit()
    return render_template('guess.html', form=form, result=result, points=current_user.points)

@app.route('/casino/mines', methods=['GET', 'POST'])
@login_required
def casino_mines():
    form = MinesStartForm()
    game = None
    if 'mines_state' in session:
        state = session['mines_state']
        game = MinesGame()
        game.mines = set(state['mines'])
        game.opened = set(state['opened'])
        game.bet_amount = state['bet_amount']
        game.finished = state['finished']
        game.multiplier = state['multiplier']
        game.mine_count = state['mine_count']
        game.current_payout = state['current_payout']
    else:
        game = None

    if form.validate_on_submit():
        bet_amount = form.bet_amount.data
        if bet_amount > current_user.points:
            flash('Недостаточно баллов для такой ставки.', 'danger')
            return redirect(url_for('casino_mines'))
        mine_count = form.mine_count.data
        if mine_count >= 25:
            flash('Слишком много мин.', 'danger')
            return redirect(url_for('casino_mines'))
        if mine_count < 1:
            mine_count = 1
        current_user.points -= bet_amount
        db.session.commit()
        game = MinesGame()
        game.init_game(mine_count, bet_amount)
        save_mines_state(game)
        flash('Игра началась! Открывайте ячейки.', 'info')
        return redirect(url_for('casino_mines'))

    game_active = game is not None and not game.finished if game else False
    return render_template('mines.html', form=form, game=game, game_active=game_active, points=current_user.points)

@app.route('/casino/mines/reveal', methods=['POST'])
@login_required
def mines_reveal():
    if 'mines_state' not in session:
        return jsonify({'error': 'Нет активной игры.'}), 400
    data = request.get_json()
    cell = data.get('cell')
    if cell is None:
        return jsonify({'error': 'Не указана ячейка.'}), 400
    game = MinesGame()
    state = session['mines_state']
    game.mines = set(state['mines'])
    game.opened = set(state['opened'])
    game.bet_amount = state['bet_amount']
    game.finished = state['finished']
    game.multiplier = state['multiplier']
    game.mine_count = state['mine_count']
    game.current_payout = state['current_payout']

    result = game.reveal_cell(cell)
    if 'error' in result:
        return jsonify(result), 400

    save_mines_state(game)
    if result.get('win') is False:
        session.pop('mines_state', None)
        db.session.commit()
    elif result.get('win') is True:
        current_user.points += result['payout']
        session.pop('mines_state', None)
        db.session.commit()
    response = {'cell': cell, 'result': result}
    if result.get('mine'):
        response['mines'] = list(game.mines)
    return jsonify(response)

@app.route('/casino/mines/cashout', methods=['POST'])
@login_required
def mines_cashout():
    if 'mines_state' not in session:
        return jsonify({'error': 'Нет активной игры.'}), 400
    game = MinesGame()
    state = session['mines_state']
    game.mines = set(state['mines'])
    game.opened = set(state['opened'])
    game.bet_amount = state['bet_amount']
    game.finished = state['finished']
    game.multiplier = state['multiplier']
    game.mine_count = state['mine_count']
    game.current_payout = state['current_payout']

    result = game.cash_out()
    if 'error' in result:
        return jsonify(result), 400

    current_user.points += result['payout']
    db.session.commit()
    session.pop('mines_state', None)
    return jsonify(result)

def save_mines_state(game):
    session['mines_state'] = {
        'mines': list(game.mines),
        'opened': list(game.opened),
        'bet_amount': game.bet_amount,
        'finished': game.finished,
        'multiplier': game.multiplier,
        'mine_count': game.mine_count,
        'current_payout': game.current_payout
    }

@app.route('/profile')
@login_required
def profile():
    strategies = Strategy.query.filter_by(author=current_user).order_by(Strategy.created_at.desc()).all()
    return render_template('profile.html', user=current_user, strategies=strategies)

@app.route('/api/strategies', methods=['GET'])
def api_strategies():
    strategies = Strategy.query.order_by(Strategy.created_at.desc()).all()
    return jsonify([s.to_dict() for s in strategies])

@app.route('/api/strategy/<int:id>', methods=['GET'])
def api_strategy(id):
    strategy = Strategy.query.get_or_404(id)
    return jsonify(strategy.to_dict())

@app.route('/api/search', methods=['GET'])
def api_search():
    q = request.args.get('q', '')
    if not q:
        return jsonify([])
    if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI']:
        results = Strategy.query.filter(Strategy.__ts_vector__.match(q)).all()
    else:
        results = Strategy.query.filter(
            or_(Strategy.title.ilike(f'%{q}%'),
                Strategy.description.ilike(f'%{q}%'))
        ).all()
    return jsonify([s.to_dict() for s in results])

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)