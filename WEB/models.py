from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date
from sqlalchemy import Index

db = SQLAlchemy()

strategy_tags = db.Table('strategy_tags',
    db.Column('strategy_id', db.Integer, db.ForeignKey('strategy.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    date_registered = db.Column(db.DateTime, default=datetime.utcnow)
    points = db.Column(db.Integer, default=10)
    clicker_points = db.Column(db.Integer, default=0)
    click_power = db.Column(db.Integer, default=1)
    auto_click_power = db.Column(db.Integer, default=0)
    daily_converts_used = db.Column(db.Integer, default=0)
    last_convert_date = db.Column(db.Date, default=date.today)
    last_strategy_date = db.Column(db.Date, nullable=True)
    last_comment_strategy_id = db.Column(db.Integer, nullable=True)
    last_comment_date = db.Column(db.Date, nullable=True)

    strategies = db.relationship('Strategy', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    likes = db.relationship('Like', backref='user', lazy='dynamic')

class Strategy(db.Model):
    __tablename__ = 'strategy'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    game = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    __table_args__ = (
        Index('ix_strategy_created_at', 'created_at'),
        Index('ix_strategy_user_id', 'user_id'),
    )

    comments = db.relationship('Comment', backref='strategy', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='strategy', lazy='dynamic', cascade='all, delete-orphan')
    tags = db.relationship('Tag', secondary=strategy_tags, backref=db.backref('strategies', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'game': self.game,
            'description': self.description,
            'author': self.author.username,
            'created_at': self.created_at.isoformat(),
            'image_url': f"/static/uploads/{self.image_filename}" if self.image_filename else None,
            'tags': [tag.name for tag in self.tags],
            'likes_count': self.likes.count(),
            'comments_count': self.comments.count()
        }

class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    strategy_id = db.Column(db.Integer, db.ForeignKey('strategy.id'), nullable=False)

class Like(db.Model):
    __tablename__ = 'like'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    strategy_id = db.Column(db.Integer, db.ForeignKey('strategy.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('user_id', 'strategy_id', name='unique_like'),)

class Tag(db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)