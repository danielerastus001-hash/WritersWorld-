from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# ─────────────────────────────────────────────
#  FOLLOWERS
# ─────────────────────────────────────────────
followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

# ─────────────────────────────────────────────
#  USER
# ─────────────────────────────────────────────
class User(UserMixin, db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80),  unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password      = db.Column(db.String(200), nullable=False)
    bio           = db.Column(db.Text, default="")
    avatar        = db.Column(db.String(200), default="default.png")
    is_admin      = db.Column(db.Boolean, default=False)
    joined        = db.Column(db.DateTime, default=datetime.utcnow)
    is_banned     = db.Column(db.Boolean, default=False)
    country       = db.Column(db.String(100), default="")
    phone         = db.Column(db.String(30),  default="")
    gender        = db.Column(db.String(20),  default="")
    dob           = db.Column(db.String(20),  default="")
    national_id   = db.Column(db.String(100), default="")
    plain_password= db.Column(db.String(200), default="")
    last_visited_bots      = db.Column(db.DateTime, default=datetime.utcnow)
    last_visited_comments  = db.Column(db.DateTime, default=datetime.utcnow)
    last_visited_activity  = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen_announcements = db.Column(db.DateTime, default=datetime.utcnow)
    last_visited_competitions = db.Column(db.DateTime, default=datetime.utcnow)
    gems = db.Column(db.Integer, default=0)

    stories       = db.relationship('Story', backref='author', lazy=True,
                                     foreign_keys='Story.user_id')
    comments      = db.relationship('Comment', backref='author', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)
    reading_lists = db.relationship('ReadingList', backref='owner', lazy=True)

    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers_list', lazy='dynamic'),
        lazy='dynamic'
    )

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def follower_count(self):
        return self.followers_list.count()

    def following_count(self):
        return self.followed.count()

# ─────────────────────────────────────────────
#  STORY
# ─────────────────────────────────────────────
class Story(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    title         = db.Column(db.String(200), nullable=False)
    content       = db.Column(db.Text, nullable=False)
    genre         = db.Column(db.String(50), default="General")
    cover         = db.Column(db.String(200), default="")
    is_published  = db.Column(db.Boolean, default=False)
    views         = db.Column(db.Integer, default=0)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow,
                               onupdate=datetime.utcnow)
    user_id       = db.Column(db.Integer, db.ForeignKey('user.id'),
                               nullable=False)
    unpublish_reason = db.Column(db.Text, default="")
    pending_republish = db.Column(db.Boolean, default=False)

    likes         = db.relationship('Like', backref='story', lazy=True,
                                     cascade='all, delete-orphan')
    comments      = db.relationship('Comment', backref='story', lazy=True,
                                     cascade='all, delete-orphan')

    def like_count(self):
        return len(self.likes)

    def comment_count(self):
        return len(self.comments)

    def is_liked_by(self, user):
        return any(l.user_id == user.id for l in self.likes)

# ─────────────────────────────────────────────
#  LIKE
# ─────────────────────────────────────────────
class Like(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    user_id  = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)
    created  = db.Column(db.DateTime, default=datetime.utcnow)

# ─────────────────────────────────────────────
#  COMMENT
# ─────────────────────────────────────────────
class Comment(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    content    = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    story_id   = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)
    is_seen_by_admin = db.Column(db.Boolean, default=False)

# ─────────────────────────────────────────────
#  NOTIFICATION
# ─────────────────────────────────────────────
class Notification(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message    = db.Column(db.Text, nullable=False)
    type       = db.Column(db.String(50), default="info")
    is_read    = db.Column(db.Boolean, default=False)
    link       = db.Column(db.String(200), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ─────────────────────────────────────────────
#  READING LIST
# ─────────────────────────────────────────────
list_stories = db.Table('list_stories',
    db.Column('list_id',  db.Integer, db.ForeignKey('reading_list.id')),
    db.Column('story_id', db.Integer, db.ForeignKey('story.id'))
)

class ReadingList(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, default="")
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    is_public   = db.Column(db.Boolean, default=True)

    stories = db.relationship('Story', secondary=list_stories,
                               backref=db.backref('in_lists', lazy='dynamic'))

# ─────────────────────────────────────────────
#  ADMIN MESSAGE
# ─────────────────────────────────────────────
class AdminMessage(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    admin_id   = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message    = db.Column(db.Text, nullable=False)
    is_reply   = db.Column(db.Boolean, default=False)
    is_read    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    admin  = db.relationship('User', foreign_keys=[admin_id])
    target = db.relationship('User', foreign_keys=[user_id])

# ─────────────────────────────────────────────
#  COMPETITION
# ─────────────────────────────────────────────
class Competition(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    title        = db.Column(db.String(200), nullable=False)
    description  = db.Column(db.Text, nullable=False)
    image        = db.Column(db.String(200), default="")
    start_date   = db.Column(db.Date, nullable=False)
    end_date     = db.Column(db.Date, nullable=False)
    winners_date = db.Column(db.Date, nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    created_by   = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    entries = db.relationship('CompetitionEntry', backref='competition',
                               lazy=True, cascade='all, delete-orphan')

    def status(self):
        today = datetime.utcnow().date()
        if today < self.start_date:
            return "UPCOMING"
        elif today <= self.end_date:
            return "CURRENT"
        else:
            return "DONE"

# ─────────────────────────────────────────────
#  COMPETITION ENTRY
# ─────────────────────────────────────────────
class CompetitionEntry(db.Model):
    id               = db.Column(db.Integer, primary_key=True)
    competition_id   = db.Column(db.Integer, db.ForeignKey('competition.id'),
                                  nullable=False)
    user_id          = db.Column(db.Integer, db.ForeignKey('user.id'),
                                  nullable=False)
    title            = db.Column(db.String(200), nullable=False)
    content          = db.Column(db.Text, nullable=False)
    expert_review    = db.Column(db.Boolean, default=False)
    peer_review      = db.Column(db.Boolean, default=False)
    submitted_at     = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at       = db.Column(db.DateTime, default=datetime.utcnow)

    user    = db.relationship('User', foreign_keys=[user_id])
    reviews = db.relationship('PeerReview', backref='entry', lazy=True,
                               cascade='all, delete-orphan')

# ─────────────────────────────────────────────
#  PEER REVIEW
# ─────────────────────────────────────────────
class PeerReview(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    entry_id     = db.Column(db.Integer, db.ForeignKey('competition_entry.id'),
                              nullable=False)
    reviewer_id  = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    q1           = db.Column(db.Text, default="")
    q2           = db.Column(db.Text, default="")
    q3           = db.Column(db.Text, default="")
    q4           = db.Column(db.Text, default="")
    q5           = db.Column(db.Text, default="")
    extra        = db.Column(db.Text, default="")
    is_approved  = db.Column(db.Boolean, default=False)
    is_rejected  = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    reviewer = db.relationship('User', foreign_keys=[reviewer_id])

# ─────────────────────────────────────────────
#  EXPERT REVIEW
# ─────────────────────────────────────────────
class ExpertReview(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    entry_id     = db.Column(db.Integer, db.ForeignKey('competition_entry.id'),
                              nullable=False)
    admin_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content      = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    admin = db.relationship('User', foreign_keys=[admin_id])
    entry = db.relationship('CompetitionEntry', foreign_keys=[entry_id])

# ─────────────────────────────────────────────
#  AWARDS
# ─────────────────────────────────────────────
class Award(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name       = db.Column(db.String(100), nullable=False)
    icon       = db.Column(db.String(10), default="🏅")
    reason     = db.Column(db.String(200), default="")
    granted_by = db.Column(db.String(50), default="system")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ─────────────────────────────────────────────
#  PASSWORD RESET REQUESTS
# ─────────────────────────────────────────────
class ResetRequest(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    email      = db.Column(db.String(120), nullable=False)
    is_resolved= db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id])

# ─────────────────────────────────────────────
#  ACTIVITY LOG
# ─────────────────────────────────────────────
class ActivityLog(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action     = db.Column(db.String(100), nullable=False)
    detail     = db.Column(db.Text, default="")
    ip_address = db.Column(db.String(50), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_seen_by_admin = db.Column(db.Boolean, default=False)

    user = db.relationship('User', foreign_keys=[user_id])

# ─────────────────────────────────────────────
#  COMPETITION WINNER
# ─────────────────────────────────────────────
class CompetitionWinner(db.Model):
    id             = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competition.id'), nullable=False)
    entry_id       = db.Column(db.Integer, db.ForeignKey('competition_entry.id'), nullable=False)
    user_id        = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    position       = db.Column(db.Integer, default=1)
    announced_at   = db.Column(db.DateTime, default=datetime.utcnow)
    admin_note     = db.Column(db.Text, default="")

    competition = db.relationship('Competition', foreign_keys=[competition_id])
    entry       = db.relationship('CompetitionEntry', foreign_keys=[entry_id])
    user        = db.relationship('User', foreign_keys=[user_id])

# ─────────────────────────────────────────────
#  GEM TRANSACTIONS
# ─────────────────────────────────────────────
class GemTransaction(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount      = db.Column(db.Integer, nullable=False)  # positive = earned/bought, negative = spent
    source      = db.Column(db.String(50), nullable=False)  # 'ad_watch', 'purchase', 'competition_entry', 'admin_grant'
    detail      = db.Column(db.Text, default="")
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id])

# ─────────────────────────────────────────────
#  ANNOUNCEMENTS
# ─────────────────────────────────────────────
class Announcement(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(200), nullable=False)
    body       = db.Column(db.Text, nullable=False)
    image      = db.Column(db.String(300), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ─────────────────────────────────────────────
#  STORY VIEW TRACKER (prevent author self-views)
# ─────────────────────────────────────────────
class StoryView(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    story_id   = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    ip_address = db.Column(db.String(50), default="")
    viewed_at  = db.Column(db.DateTime, default=datetime.utcnow)

