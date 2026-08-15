from app import app, db
from database import Like, Comment, StoryView, Story
from datetime import datetime

with app.app_context():
    fixed_likes = 0
    fixed_comments = 0

    # Backfill views for existing likes
    likes = Like.query.all()
    for like in likes:
        existing = StoryView.query.filter_by(
            user_id=like.user_id, story_id=like.story_id).first()
        if not existing:
            sv = StoryView(story_id=like.story_id, user_id=like.user_id, ip_address='backfill')
            db.session.add(sv)
            story = Story.query.get(like.story_id)
            if story:
                story.views = (story.views or 0) + 1
            fixed_likes += 1

    db.session.commit()

    # Backfill views for existing comments
    comments = Comment.query.all()
    for c in comments:
        existing = StoryView.query.filter_by(
            user_id=c.user_id, story_id=c.story_id).first()
        if not existing:
            sv = StoryView(story_id=c.story_id, user_id=c.user_id, ip_address='backfill')
            db.session.add(sv)
            story = Story.query.get(c.story_id)
            if story:
                story.views = (story.views or 0) + 1
            fixed_comments += 1

    db.session.commit()
    print(f"[+] Backfilled {fixed_likes} missing views from likes")
    print(f"[+] Backfilled {fixed_comments} missing views from comments")
    print("[+] Done!")
