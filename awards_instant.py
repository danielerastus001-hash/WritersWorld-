#!/usr/bin/env python3
# ─────────────────────────────────────────────
#  AWARDS INSTANT FIX
#  Awards given immediately after action
# ─────────────────────────────────────────────

import os

APP = os.path.expanduser("~/writersworld/app.py")

with open(APP) as f:
    app = f.read()

patches = 0

# Fix check_awards to commit and notify immediately
old = '''def check_awards(user):
    existing = [a.name for a in Award.query.filter_by(user_id=user.id).all()]
    stories  = Story.query.filter_by(user_id=user.id, is_published=True).all()
    pub      = len(stories)
    total_likes    = sum(s.like_count() for s in stories)
    total_comments = sum(s.comment_count() for s in stories)
    followers      = user.follower_count()

    candidates = []

    # Story count awards
    if pub >= 1:  candidates.append(("First Story",       "🌱", "Published first story"))
    if pub >= 5:  candidates.append(("Prolific Writer",   "✍️",  "Published 5 stories"))
    if pub >= 10: candidates.append(("Storyteller",       "📖", "Published 10 stories"))
    if pub >= 20: candidates.append(("Master Wordsmith",  "👑", "Published 20 stories"))

    # Likes awards
    if any(s.like_count() >= 10 for s in stories):
        candidates.append(("Rising Star",    "⭐", "10+ likes on a single story"))
    if total_likes >= 50:
        candidates.append(("Popular Author", "🔥", "50+ total likes"))
    if total_likes >= 100:
        candidates.append(("Bestseller",     "🏆", "100+ total likes"))
    if total_likes >= 500:
        candidates.append(("Legend",         "🌟", "500+ total likes"))

    # Comment awards
    if total_comments >= 1:
        candidates.append(("First Comment",     "💬", "Received first comment"))
    if total_comments >= 25:
        candidates.append(("Engaging Writer",   "🗣️",  "25+ comments received"))

    # Follower awards
    if followers >= 50:
        candidates.append(("Follower Magnet",    "📣", "50+ followers"))
    if followers >= 100:
        candidates.append(("Community Builder",  "🤝", "100+ followers"))
    if followers >= 500:
        candidates.append(("Influencer",         "💫", "500+ followers"))

    for name, icon, reason in candidates:
        if name not in existing:
            award = Award(user_id=user.id, name=name,
                          icon=icon, reason=reason)
            db.session.add(award)
            add_notification(user.id,
                f"You earned a new award: {icon} {name}!",
                "success")
    db.session.commit()'''

new = '''def check_awards(user):
    """Check and grant awards immediately — called after every qualifying action"""
    try:
        existing = [a.name for a in Award.query.filter_by(user_id=user.id).all()]
        stories  = Story.query.filter_by(user_id=user.id, is_published=True).all()
        pub             = len(stories)
        total_likes     = sum(s.like_count() for s in stories)
        total_comments  = sum(s.comment_count() for s in stories)
        followers       = user.follower_count()

        candidates = []

        # Story count awards
        if pub >= 1:  candidates.append(("First Story",      "🌱", "Published first story"))
        if pub >= 5:  candidates.append(("Prolific Writer",  "✍️",  "Published 5 stories"))
        if pub >= 10: candidates.append(("Storyteller",      "📖", "Published 10 stories"))
        if pub >= 20: candidates.append(("Master Wordsmith", "👑", "Published 20 stories"))

        # Likes awards
        if any(s.like_count() >= 10 for s in stories):
            candidates.append(("Rising Star",    "⭐", "10+ likes on a single story"))
        if total_likes >= 50:
            candidates.append(("Popular Author", "🔥", "50+ total likes"))
        if total_likes >= 100:
            candidates.append(("Bestseller",     "🏆", "100+ total likes"))
        if total_likes >= 500:
            candidates.append(("Legend",         "🌟", "500+ total likes"))

        # Comment awards
        if total_comments >= 1:
            candidates.append(("First Comment",   "💬", "Received first comment"))
        if total_comments >= 25:
            candidates.append(("Engaging Writer", "🗣️",  "25+ comments received"))

        # Follower awards
        if followers >= 50:
            candidates.append(("Follower Magnet",   "📣", "50+ followers"))
        if followers >= 100:
            candidates.append(("Community Builder", "🤝", "100+ followers"))
        if followers >= 500:
            candidates.append(("Influencer",        "💫", "500+ followers"))

        new_awards = []
        for name, icon, reason in candidates:
            if name not in existing:
                award = Award(user_id=user.id, name=name,
                              icon=icon, reason=reason)
                db.session.add(award)
                new_awards.append(f"{icon} {name}")

        if new_awards:
            # Single notification listing all new awards
            awards_str = ", ".join(new_awards)
            notif = Notification(
                user_id=user.id,
                message=f"🎉 New award{'s' if len(new_awards) > 1 else ''} earned: {awards_str}!",
                type="success")
            db.session.add(notif)
            db.session.commit()
    except Exception as e:
        print(f"Award check error: {e}")'''

if old in app:
    app = app.replace(old, new)
    patches += 1
    print("✓ Awards now trigger instantly with single notification")
else:
    print("✗ Awards pattern not found")

with open(APP, 'w') as f:
    f.write(app)

print(f"\n✅ {patches} fixes applied.")

