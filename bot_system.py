#!/usr/bin/env python3
# ============================================================
#  WRITERSWORLD BOT SYSTEM
#  Realistic bot users that behave like real writers
#  Runs as background service when server starts
# ============================================================

import os, sys, time, random, threading, json
from datetime import datetime, timedelta

sys.path.insert(0, os.path.expanduser("~/writersworld"))
os.chdir(os.path.expanduser("~/writersworld"))

# ─────────────────────────────────────────────
#  BOT PERSONALITIES
# ─────────────────────────────────────────────
BOT_PERSONALITIES = {
    "Amara":   {"genre": "Romance",   "style": "emotional, warm, deeply personal",       "group": "morning"},
    "Chidi":   {"genre": "Thriller",  "style": "tense, fast-paced, full of suspense",    "group": "morning"},
    "Fatima":  {"genre": "Fantasy",   "style": "vivid, imaginative, world-building",     "group": "morning"},
    "Emeka":   {"genre": "Action",    "style": "bold, energetic, high stakes",           "group": "morning"},
    "Ngozi":   {"genre": "Drama",     "style": "character-driven, raw, emotional",       "group": "morning"},
    "Kwame":   {"genre": "Mystery",   "style": "clever, layered, full of clues",         "group": "morning"},
    "Aisha":   {"genre": "Sci-Fi",    "style": "cerebral, futuristic, philosophical",    "group": "morning"},
    "Tobias":  {"genre": "Horror",    "style": "dark, atmospheric, deeply unsettling",   "group": "afternoon"},
    "Yemi":    {"genre": "Comedy",    "style": "witty, sharp, observational humor",      "group": "afternoon"},
    "Sade":    {"genre": "Romance",   "style": "slow burn, tender, bittersweet",         "group": "afternoon"},
    "Malik":   {"genre": "Adventure", "style": "sweeping, cinematic, full of wonder",    "group": "afternoon"},
    "Zara":    {"genre": "Drama",     "style": "minimalist, precise, emotionally heavy", "group": "afternoon"},
    "Kofi":    {"genre": "Thriller",  "style": "psychological, dark, morally complex",   "group": "afternoon"},
    "Chisom":  {"genre": "Fantasy",   "style": "mythological, lyrical, deeply cultural", "group": "afternoon"},
    "Adaeze":  {"genre": "Poetry",    "style": "evocative, rhythmic, image-heavy",       "group": "night"},
    "Tunde":   {"genre": "Mystery",   "style": "gritty, street-level, noir-influenced",  "group": "night"},
    "Halima":  {"genre": "Sci-Fi",    "style": "intimate, human-focused, near-future",   "group": "night"},
    "Seun":    {"genre": "Horror",    "style": "slow dread, psychological, paranoid",    "group": "night"},
    "Nneka":   {"genre": "Drama",     "style": "multigenerational, family-focused, rich","group": "night"},
    "Jide":    {"genre": "Action",    "style": "gritty, street-smart, high energy",      "group": "night"},
}

GROUP_HOURS = {
    "morning":   (6,  11),
    "afternoon": (12, 17),
    "night":     (18, 23),
}

# Comment styles per personality
COMMENT_TEMPLATES = [
    "This hit differently. The way you built the tension was masterful.",
    "I could not stop reading. Every line pulled me deeper.",
    "The ending completely blindsided me. Brilliant work.",
    "Your writing has such a distinct voice. This is memorable.",
    "I felt every emotion in this piece. Really powerful.",
    "The imagery here is stunning. I kept rereading certain lines.",
    "This deserves so many more readers. Sharing immediately.",
    "The character felt so real. I was genuinely invested.",
    "You captured something true here. This stayed with me.",
    "The pacing was perfect. Not a single wasted word.",
    "I loved the twist. Did not see it coming at all.",
    "This reminded me why I love reading. Thank you for writing it.",
    "The opening line alone is worth everything.",
    "I felt seen reading this. That does not happen often.",
    "The dialogue felt completely natural. Incredible craft.",
]

def get_groq_key():
    try:
        with open('config.json') as f:
            return json.load(f).get('groq_api_key', '')
    except:
        return ''

def ask_groq(prompt, max_tokens=800):
    import urllib.request as ur
    key = get_groq_key()
    if not key:
        return None
    payload = json.dumps({
        "model": "openrouter/free",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.85
    }).encode()
    req = ur.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"})
    try:
        with ur.urlopen(req, timeout=20) as r:
            return json.load(r)["choices"][0]["message"]["content"].strip()
    except:
        return None

def generate_story(bot_name, genre, style):
    seeds = [
        "a stranger who arrives at the wrong time",
        "a letter that was never meant to be found",
        "a decision that cannot be undone",
        "two people who should never have met",
        "a secret kept for too long",
        "the last night before everything changes",
        "a place that holds too many memories",
        "someone who discovers they have been lied to",
        "a moment of unexpected kindness",
        "the thing left unsaid",
    ]
    seed  = random.choice(seeds)
    salt  = random.randint(100, 999)
    prompt = (
        f"Write a complete short story in the {genre} genre. "
        f"Style: {style}. Central concept: {seed}. ID: {salt}. "
        f"STRICT FORMAT RULES — follow exactly: "
        f"Line 1: A proper story title (2-5 words, creative, specific — NOT a description or theme). "
        f"Line 2: Empty line. "
        f"Line 3 onwards: The story itself, minimum 400 words. "
        f"The story must be pure prose — no chapter headings, no labels, no metadata, "
        f"no prompts, no instructions visible in the output. "
        f"Start the story immediately after the title. "
        f"Example of good title: The Last Train Home "
        f"Example of bad title: A Story About Loss and Redemption "
        f"Output nothing except the title and story."
    )
    result = ask_groq(prompt, max_tokens=1000)
    if not result:
        return None, None
    lines = result.strip().split('\n')
    # Clean title — remove any markdown, quotes, labels
    title = lines[0].strip()
    for prefix in ['Title:', 'TITLE:', '**', '__', '#']:
        title = title.replace(prefix, '').strip()
    title = title.strip('"').strip("'").strip()
    # Get story content — skip empty lines after title
    story_lines = []
    found_story = False
    for line in lines[1:]:
        if not found_story and not line.strip():
            continue
        found_story = True
        story_lines.append(line)
    story_content = '\n'.join(story_lines).strip()
    # Validate — reject if content looks like prompts
    bad_signs = ['write a', 'in the genre', 'style:', 'central concept',
                 'strict format', 'requirements:', 'minimum 400']
    for bad in bad_signs:
        if bad.lower() in story_content.lower()[:200]:
            return None, None
    if len(story_content) < 200 or not title:
        return None, None
    return title, story_content

def generate_comment(story_title, story_excerpt, commenter_style):
    # 60% use template, 40% AI generated
    if random.random() < 0.6:
        return random.choice(COMMENT_TEMPLATES)
    prompt = (
        f"Write a short, genuine reader comment (1-2 sentences) "
        f"for a story called '{story_title}'. "
        f"Story excerpt: '{story_excerpt[:200]}'. "
        f"The commenter writes in a {commenter_style} style. "
        f"Comment should feel natural, not generic. "
        f"Output only the comment, nothing else."
    )
    result = ask_groq(prompt, max_tokens=80)
    return result if result else random.choice(COMMENT_TEMPLATES)

# ─────────────────────────────────────────────
#  BOT SERVICE CLASS
# ─────────────────────────────────────────────

import json as _json
import os as _os

BOT_STATE_FILE = _os.path.join(_os.path.dirname(__file__), 'bot_state.json')

def load_bot_state():
    try:
        with open(BOT_STATE_FILE) as f:
            return _json.load(f)
    except:
        return {
            "global_active": True,
            "bots": {name: {"active": True, "activity": "medium"}
                     for name in BOT_PERSONALITIES}
        }

def save_bot_state(state):
    with open(BOT_STATE_FILE, 'w') as f:
        _json.dump(state, f, indent=2)

def is_bot_active(bot_name):
    state = load_bot_state()
    if not state.get("global_active", True):
        return False
    return state.get("bots", {}).get(bot_name, {}).get("active", True)

def get_bot_activity(bot_name):
    state = load_bot_state()
    return state.get("bots", {}).get(bot_name, {}).get("activity", "medium")

class BotService:
    def __init__(self, app):
        self.app          = app
        self.running      = True
        self.post_log     = {}  # story_id -> posted_time
        self.comment_log  = {}  # story_id -> list of bot usernames who commented
        self.like_log     = {}  # story_id -> list of bot usernames who liked
        self.daily_posts  = {}  # date -> {bot_name -> count}

    def log(self, msg):
        print(f"[BOT {datetime.now().strftime('%H:%M:%S')}] {msg}")

    def get_bot_user(self, name):
        from database import User
        return User.query.filter_by(username=name).first()

    def should_post_now(self, bot_name):
        """Check if bot should post based on group and daily quota"""
        personality = BOT_PERSONALITIES.get(bot_name)
        if not personality:
            return False
        group = personality["group"]
        h_start, h_end = GROUP_HOURS[group]
        hour = datetime.now().hour
        if not (h_start <= hour <= h_end):
            return False
        today     = str(datetime.now().date())
        day_posts = self.daily_posts.get(today, {})
        bot_posts = day_posts.get(bot_name, 0)
        # Each bot posts 2 times per day minimum
        if bot_posts >= 3:
            return False
        # Random chance to post (not every check)
        return random.random() < 0.08  # ~8% chance each check

    def should_post_random(self, bot_name):
        """Second daily post at random time"""
        today     = str(datetime.now().date())
        day_posts = self.daily_posts.get(today, {})
        bot_posts = day_posts.get(bot_name, 0)
        if bot_posts >= 3:
            return False
        if bot_posts < 1:
            return False  # Must have at least 1 post first
        return random.random() < 0.03

    def record_post(self, bot_name):
        today = str(datetime.now().date())
        if today not in self.daily_posts:
            self.daily_posts[today] = {}
        self.daily_posts[today][bot_name] = \
            self.daily_posts[today].get(bot_name, 0) + 1

    def can_engage(self, story_id, story_posted_time):
        """Check if enough time has passed (1-3 hours)"""
        if story_id not in self.post_log:
            self.post_log[story_id] = story_posted_time
        wait_hours = random.uniform(1, 3)
        elapsed    = (datetime.utcnow() - story_posted_time).total_seconds() / 3600
        return elapsed >= wait_hours

    def can_comment(self, story_id, bot_name):
        """Max 3 bots can comment per story"""
        commenters = self.comment_log.get(story_id, [])
        if bot_name in commenters:
            return False
        return len(commenters) < 3

    def can_like(self, story_id, bot_name):
        """Bot can only like once"""
        return bot_name not in self.like_log.get(story_id, [])

    def run_posting(self):
        """Background thread for bot posting"""
        from database import User, Story, db
        time.sleep(30)  # Wait for server to fully start
        self.log("Bot posting service started")

        while self.running:
            try:
                with self.app.app_context():
                    for bot_name, personality in BOT_PERSONALITIES.items():
                        bot_user = self.get_bot_user(bot_name)
                        if not bot_user:
                            continue

                        should_post = (
                            self.should_post_now(bot_name) or
                            self.should_post_random(bot_name)
                        )

                        if should_post and is_bot_active(bot_name):
                            self.log(f"{bot_name} is writing a story...")
                            title, content = generate_story(
                                bot_name,
                                personality["genre"],
                                personality["style"]
                            )
                            if title and content and len(content) > 200:
                                # Save as DRAFT — requires admin approval
                                story = Story(
                                    title=title,
                                    content=content,
                                    genre=personality["genre"],
                                    is_published=False,
                                    user_id=bot_user.id,
                                    created_at=datetime.utcnow()
                                )
                                db.session.add(story)
                                db.session.commit()
                                self.record_post(bot_name)
                                self.post_log[story.id] = datetime.utcnow()
                                from database import ActivityLog
                                al = ActivityLog(
                                    user_id=bot_user.id,
                                    action='bot_post',
                                    detail=f"{bot_name} wrote '{title}' — awaiting admin approval",
                                    ip_address='bot')
                                db.session.add(al)
                                db.session.commit()
                                self.log(f"{bot_name} drafted: {title} (awaiting approval)")
                                # Notify admin
                                try:
                                    from database import User, Notification
                                    admin = User.query.filter_by(is_admin=True).first()
                                    if admin:
                                        n = Notification(
                                            user_id=admin.id,
                                            message=f"Bot story pending approval: '{title}' by {bot_name}",
                                            type='info',
                                            link='/admin/bots'
                                        )
                                        db.session.add(n)
                                        db.session.commit()
                                except:
                                    pass
                                time.sleep(random.uniform(60, 300))

            except Exception as e:
                self.log(f"Posting error: {e}")

            time.sleep(600)  # Check every 10 minutes

    def run_engagement(self):
        """Background thread for likes and comments"""
        from database import User, Story, Like, Comment, StoryView, db
        from werkzeug.security import generate_password_hash
        time.sleep(60)
        self.log("Bot engagement service started")

        while self.running:
            try:
                with self.app.app_context():
                    # Get recent published stories (last 24 hours)
                    cutoff  = datetime.utcnow() - timedelta(hours=24)
                    stories = Story.query.filter(
                        Story.is_published == True,
                        Story.created_at >= cutoff
                    ).order_by(Story.created_at.desc()).all()

                    for story in stories:
                        if not self.can_engage(story.id, story.created_at):
                            continue

                        # Shuffle bots for natural order
                        bot_names = list(BOT_PERSONALITIES.keys())
                        random.shuffle(bot_names)

                        for bot_name in bot_names:
                            bot_user = self.get_bot_user(bot_name)
                            if not bot_user:
                                continue

                            # Skip if bot is the author
                            if story.user_id == bot_user.id:
                                continue

                            # LIKE — random chance, spread out
                            if self.can_like(story.id, bot_name) and is_bot_active(bot_name):
                                if random.random() < 0.4:  # 40% chance to like
                                    existing = Like.query.filter_by(
                                        user_id=bot_user.id,
                                        story_id=story.id).first()
                                    if not existing:
                                        # Ensure a view exists before the like (bots must "see" a story to like it)
                                        existing_view = StoryView.query.filter_by(
                                            user_id=bot_user.id, story_id=story.id).first()
                                        if not existing_view:
                                            sv = StoryView(
                                                story_id=story.id,
                                                user_id=bot_user.id,
                                                ip_address='bot')
                                            db.session.add(sv)
                                            story.views = (story.views or 0) + 1

                                        like = Like(
                                            user_id=bot_user.id,
                                            story_id=story.id)
                                        db.session.add(like)
                                        # Log activity
                                        from database import ActivityLog
                                        al = ActivityLog(
                                            user_id=bot_user.id,
                                            action='like',
                                            detail=f"{bot_name} liked '{story.title}'",
                                            ip_address='bot')
                                        db.session.add(al)
                                        db.session.commit()
                                        if story.id not in self.like_log:
                                            self.like_log[story.id] = []
                                        self.like_log[story.id].append(bot_name)
                                        self.log(f"{bot_name} liked '{story.title}'")
                                        time.sleep(random.uniform(30, 120))

                            # COMMENT — max 3 per story, staggered
                            if self.can_comment(story.id, bot_name) and is_bot_active(bot_name):
                                if random.random() < 0.2:  # 20% chance to comment
                                    personality = BOT_PERSONALITIES[bot_name]
                                    comment_text = generate_comment(
                                        story.title,
                                        story.content[:300],
                                        personality["style"]
                                    )
                                    if comment_text:
                                        existing_view = StoryView.query.filter_by(
                                            user_id=bot_user.id, story_id=story.id).first()
                                        if not existing_view:
                                            sv = StoryView(
                                                story_id=story.id,
                                                user_id=bot_user.id,
                                                ip_address='bot')
                                            db.session.add(sv)
                                            story.views = (story.views or 0) + 1

                                        comment = Comment(
                                            content=comment_text,
                                            user_id=bot_user.id,
                                            story_id=story.id,
                                            created_at=datetime.utcnow()
                                        )
                                        db.session.add(comment)
                                        from database import ActivityLog
                                        al = ActivityLog(
                                            user_id=bot_user.id,
                                            action='comment',
                                            detail=f"{bot_name} commented on '{story.title}'",
                                            ip_address='bot')
                                        db.session.add(al)
                                        db.session.commit()
                                        if story.id not in self.comment_log:
                                            self.comment_log[story.id] = []
                                        self.comment_log[story.id].append(bot_name)
                                        self.log(f"{bot_name} commented on '{story.title}'")
                                        # Stagger comments — bots never comment at same time
                                        time.sleep(random.uniform(120, 600))

            except Exception as e:
                self.log(f"Engagement error: {e}")

            time.sleep(900)  # Check every 15 minutes

    def run_following(self):
        """Bots follow real users who have 3+ stories"""
        from database import User, Story, followers, db
        time.sleep(120)
        self.log("Bot following service started")

        while self.running:
            try:
                with self.app.app_context():
                    # Get real users with 3+ published stories
                    real_users = User.query.filter_by(is_admin=False).all()
                    for user in real_users:
                        # Skip bots
                        if user.username in BOT_PERSONALITIES:
                            continue
                        pub_count = Story.query.filter_by(
                            user_id=user.id, is_published=True).count()
                        if pub_count < 3:
                            continue

                        # Random bots follow this user
                        bot_names = list(BOT_PERSONALITIES.keys())
                        random.shuffle(bot_names)
                        followers_to_add = random.sample(
                            bot_names, min(random.randint(2, 5), len(bot_names)))

                        for bot_name in followers_to_add:
                            bot_user = self.get_bot_user(bot_name)
                            if not bot_user:
                                continue
                            if not bot_user.is_following(user):
                                bot_user.follow(user)
                                from database import ActivityLog
                                al = ActivityLog(
                                    user_id=bot_user.id,
                                    action='follow',
                                    detail=f"{bot_name} followed {user.username}",
                                    ip_address='bot')
                                db.session.add(al)
                                db.session.commit()
                                self.log(f"{bot_name} followed {user.username}")
                                time.sleep(random.uniform(5, 30))

            except Exception as e:
                self.log(f"Following error: {e}")

            time.sleep(3600)  # Check every hour

    def start(self):
        """Start all bot services as daemon threads"""
        threading.Thread(target=self.run_posting,    daemon=True).start()
        threading.Thread(target=self.run_engagement, daemon=True).start()
        threading.Thread(target=self.run_following,  daemon=True).start()
        print("[BOT SYSTEM] All bot services started")


# ─────────────────────────────────────────────
#  INTEGRATION — called from app.py
# ─────────────────────────────────────────────
def start_bots(app):
    """Call this from app.py to start the bot system"""
    service = BotService(app)
    service.start()
