#!/usr/bin/env python3
# Add /aegis/chat route to app.py
import os

APP = os.path.expanduser("~/writersworld/app.py")

with open(APP) as f:
    src = f.read()

old = '# ─────────────────────────────────────────────\n#  EXPERT REVIEW ROUTE'

new = '''# ─────────────────────────────────────────────
#  AEGIS FLOATING CHAT ROUTE
# ─────────────────────────────────────────────
@app.route('/aegis/chat', methods=['POST'])
@login_required
def aegis_chat():
    data    = request.json or {}
    message = data.get('message', '')
    system  = data.get('system', AEGIS_SYSTEM if 'AEGIS_SYSTEM' in dir() else
        "You are Aegis, a smart AI assistant for WritersWorld. Address user as Sir.")
    page    = data.get('page', '')
    context = data.get('context', '')

    # Enrich system prompt with live platform stats
    try:
        total_users   = User.query.count()
        total_stories = Story.query.filter_by(is_published=True).count()
        total_comps   = Competition.query.count()
        pending_rev   = PeerReview.query.filter_by(is_approved=False, is_rejected=False).count()
        new_users_today = User.query.filter(
            User.joined >= datetime.utcnow().replace(hour=0,minute=0,second=0)).count()

        platform_context = (
            f"Platform stats: {total_users} total users, "
            f"{total_stories} published stories, "
            f"{total_comps} competitions, "
            f"{pending_rev} pending peer reviews, "
            f"{new_users_today} new users today. "
        )
        system = platform_context + system
    except:
        pass

    result, error = ask_aegis(message, system=system, max_tokens=300)
    if error:
        return jsonify({'error': error})
    return jsonify({'result': result})

# ─────────────────────────────────────────────
#  EXPERT REVIEW ROUTE'''

if old in src:
    src = src.replace(old, new)
    with open(APP, 'w') as f:
        f.write(src)
    print("✓ Aegis chat route added")
else:
    print("✗ Pattern not found")
