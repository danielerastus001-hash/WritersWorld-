#!/usr/bin/env python3
# ─────────────────────────────────────────────
#  AEGIS TOOL-CALLING SYSTEM
#  Aegis can now execute platform actions
# ─────────────────────────────────────────────

import os

APP = os.path.expanduser("~/writersworld/app.py")

with open(APP) as f:
    src = f.read()

# ── Replace aegis_chat route with full tool-calling version ──
old = '''@app.route('/aegis/chat', methods=['POST'])
@login_required
def aegis_chat():
    # Use ask_aegis with full context
    history  = data.get('history', [])
    cfg_path = os.path.join(os.path.dirname(__file__), 'config.json')
    key = ""
    if os.path.exists(cfg_path):
        with open(cfg_path) as _f:
            key = json.load(_f).get('groq_api_key', '')
    if not key:
        return jsonify({'error': 'API key not configured. Set it in Admin panel.'})

    url      = "https://openrouter.ai/api/v1/chat/completions"
    messages = [{"role": "system", "content": system}]
    for h in history[-6:]:
        messages.append({
            "role": h.get("role", "user"),
            "content": h.get("content", "")
        })
    messages.append({"role": "user", "content": message})

    import urllib.request as _ur
    payload = json.dumps({
        "model": "openrouter/free",
        "messages": messages,
        "max_tokens": 300,
        "temperature": 0.7
    }).encode()
    req = _ur.Request(url, data=payload, headers={
        "Authorization": f"Bearer {key}",
        "Content-Type":  "application/json",
        "HTTP-Referer":  "http://localhost:5000",
        "X-Title":       "WritersWorld"
    })
    try:
        with _ur.urlopen(req, timeout=20) as r:
            data2  = json.load(r)
            result = data2["choices"][0]["message"]["content"].strip()
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': f'Aegis error: {str(e)}'})'''

new = '''@app.route('/aegis/chat', methods=['POST'])
@login_required
def aegis_chat():
    pass

# ─────────────────────────────────────────────
#  AEGIS TOOL EXECUTOR
# ─────────────────────────────────────────────
def aegis_execute_tool(tool_name, params):
    """Execute a platform action and return result"""
    try:
        if tool_name == "get_stats":
            total_users   = User.query.filter_by(is_admin=False).count()
            total_stories = Story.query.filter_by(is_published=True).count()
            total_comps   = Competition.query.count()
            pending_rev   = PeerReview.query.filter_by(is_approved=False, is_rejected=False).count()
            pending_bots  = Story.query.join(User).filter(
                Story.is_published==False,
                User.username.in_(["Amara","Chidi","Fatima","Emeka","Ngozi",
                    "Kwame","Aisha","Tobias","Yemi","Sade","Malik","Zara",
                    "Kofi","Chisom","Adaeze","Tunde","Halima","Seun","Nneka","Jide"])
            ).count()
            new_today = User.query.filter(
                User.joined >= datetime.utcnow().replace(hour=0,minute=0,second=0)
            ).count()
            return {
                "users": total_users, "stories": total_stories,
                "competitions": total_comps, "pending_reviews": pending_rev,
                "pending_bot_stories": pending_bots, "new_users_today": new_today
            }

        elif tool_name == "ban_user":
            username = params.get("username","")
            user = User.query.filter_by(username=username).first()
            if not user: return {"error": f"User '{username}' not found"}
            user.is_banned = True
            db.session.commit()
            add_notification(user.id, "Your account has been banned by admin.", "warning")
            return {"success": f"User '{username}' has been banned"}

        elif tool_name == "unban_user":
            username = params.get("username","")
            user = User.query.filter_by(username=username).first()
            if not user: return {"error": f"User '{username}' not found"}
            user.is_banned = False
            db.session.commit()
            return {"success": f"User '{username}' has been unbanned"}

        elif tool_name == "get_user":
            username = params.get("username","")
            user = User.query.filter_by(username=username).first()
            if not user: return {"error": f"User '{username}' not found"}
            stories = Story.query.filter_by(user_id=user.id, is_published=True).count()
            return {
                "username": user.username, "email": user.email,
                "country": user.country or "Unknown",
                "joined": user.joined.strftime("%d %b %Y"),
                "stories": stories,
                "followers": user.follower_count(),
                "banned": user.is_banned
            }

        elif tool_name == "approve_all_bot_stories":
            bot_names = ["Amara","Chidi","Fatima","Emeka","Ngozi","Kwame","Aisha",
                        "Tobias","Yemi","Sade","Malik","Zara","Kofi","Chisom",
                        "Adaeze","Tunde","Halima","Seun","Nneka","Jide"]
            count = 0
            for name in bot_names:
                user = User.query.filter_by(username=name).first()
                if user:
                    drafts = Story.query.filter_by(user_id=user.id, is_published=False).all()
                    for d in drafts:
                        d.is_published = True
                        count += 1
            db.session.commit()
            return {"success": f"Approved {count} bot stories"}

        elif tool_name == "unpublish_story":
            story_id = params.get("story_id")
            title    = params.get("title","")
            if story_id:
                story = Story.query.get(story_id)
            elif title:
                story = Story.query.filter(Story.title.ilike(f"%{title}%")).first()
            else:
                return {"error": "Provide story_id or title"}
            if not story: return {"error": "Story not found"}
            story.is_published = False
            db.session.commit()
            add_notification(story.user_id,
                f"Your story '{story.title}' was unpublished by admin.", "warning")
            return {"success": f"Story '{story.title}' unpublished"}

        elif tool_name == "publish_story":
            story_id = params.get("story_id")
            title    = params.get("title","")
            if story_id:
                story = Story.query.get(story_id)
            elif title:
                story = Story.query.filter(Story.title.ilike(f"%{title}%")).first()
            else:
                return {"error": "Provide story_id or title"}
            if not story: return {"error": "Story not found"}
            story.is_published = True
            db.session.commit()
            return {"success": f"Story '{story.title}' published"}

        elif tool_name == "list_users":
            limit = int(params.get("limit", 10))
            users = User.query.filter_by(is_admin=False)\
                              .order_by(User.joined.desc()).limit(limit).all()
            return {"users": [{"username": u.username, "email": u.email,
                               "country": u.country or "?",
                               "joined": u.joined.strftime("%d %b %Y"),
                               "banned": u.is_banned} for u in users]}

        elif tool_name == "list_stories":
            limit = int(params.get("limit", 10))
            stories = Story.query.filter_by(is_published=True)\
                                 .order_by(Story.created_at.desc()).limit(limit).all()
            return {"stories": [{"id": s.id, "title": s.title,
                                  "author": s.author.username,
                                  "views": s.views,
                                  "likes": s.like_count()} for s in stories]}

        elif tool_name == "send_announcement":
            title = params.get("title","")
            body  = params.get("body","")
            if not title or not body:
                return {"error": "Need title and body"}
            import json as _j
            path  = os.path.join(os.path.dirname(__file__), 'announcements','announcements.json')
            try:
                with open(path) as f:
                    items = _j.load(f)
            except:
                items = []
            items.insert(0, {"title": title, "body": body, "image": "",
                             "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M")})
            with open(path,'w') as f:
                _j.dump(items, f, indent=2)
            users = User.query.filter_by(is_admin=False).all()
            for u in users:
                add_notification(u.id, f"Announcement: {title}", "announcement",
                                 url_for("history"))
            db.session.commit()
            return {"success": f"Announcement '{title}' sent to {len(users)} users"}

        elif tool_name == "notify_user":
            username = params.get("username","")
            msg      = params.get("message","")
            user = User.query.filter_by(username=username).first()
            if not user: return {"error": f"User '{username}' not found"}
            add_notification(user.id, msg, "info")
            db.session.commit()
            return {"success": f"Notification sent to {username}"}

        elif tool_name == "notify_all":
            msg   = params.get("message","")
            users = User.query.filter_by(is_admin=False).all()
            for u in users:
                add_notification(u.id, msg, "info")
            db.session.commit()
            return {"success": f"Notification sent to {len(users)} users"}

        elif tool_name == "delete_story":
            story_id = params.get("story_id")
            title    = params.get("title","")
            if story_id:
                story = Story.query.get(story_id)
            elif title:
                story = Story.query.filter(Story.title.ilike(f"%{title}%")).first()
            else:
                return {"error": "Provide story_id or title"}
            if not story: return {"error": "Story not found"}
            story_title = story.title
            db.session.delete(story)
            db.session.commit()
            return {"success": f"Story '{story_title}' deleted"}

        elif tool_name == "pending_reviews":
            reviews = PeerReview.query.filter_by(
                is_approved=False, is_rejected=False).all()
            return {"count": len(reviews),
                    "reviews": [{"id": r.id,
                                  "entry": r.entry.title,
                                  "reviewer": r.reviewer.username} for r in reviews[:10]]}

        elif tool_name == "top_stories":
            limit   = int(params.get("limit", 5))
            stories = Story.query.filter_by(is_published=True)\
                                 .order_by(Story.views.desc()).limit(limit).all()
            return {"stories": [{"id": s.id, "title": s.title,
                                  "author": s.author.username,
                                  "views": s.views,
                                  "likes": s.like_count(),
                                  "comments": s.comment_count()} for s in stories]}

        elif tool_name == "search_web":
            query = params.get("query","")
            if not query: return {"error": "Provide a search query"}
            import urllib.request as _ur, urllib.parse as _up
            try:
                q   = _up.quote(query.replace(" ","_"))
                url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{q}"
                with _ur.urlopen(url, timeout=8) as r:
                    d = json.load(r)
                return {"result": d.get("extract","No results found.")[:500]}
            except:
                return {"result": f"Could not find information on: {query}"}

        elif tool_name == "get_leaderboard":
            users = User.query.filter_by(is_admin=False).all()
            def score(u):
                pub = [s for s in u.stories if s.is_published]
                return sum(s.views for s in pub) + sum(s.like_count()*3 for s in pub) + sum(s.comment_count()*5 for s in pub)
            ranked = sorted(users, key=score, reverse=True)[:10]
            return {"leaderboard": [{"rank": i+1, "username": u.username,
                                      "score": score(u)} for i,u in enumerate(ranked)]}

        else:
            return {"error": f"Unknown tool: {tool_name}"}

    except Exception as e:
        return {"error": str(e)}


@app.route('/aegis/command', methods=['POST'])
@login_required
@admin_required
def aegis_command():
    """Admin-only: Aegis executes platform commands"""
    data    = request.json or {}
    message = data.get('message','')
    history = data.get('history',[])

    cfg_path = os.path.join(os.path.dirname(__file__), 'config.json')
    key = ""
    if os.path.exists(cfg_path):
        with open(cfg_path) as _f:
            key = json.load(_f).get('groq_api_key','')
    if not key:
        return jsonify({'error': 'API key not configured.'})

    # Get live platform stats for context
    try:
        total_users   = User.query.filter_by(is_admin=False).count()
        total_stories = Story.query.filter_by(is_published=True).count()
        pending_bots  = Story.query.join(User).filter(
            Story.is_published==False,
            User.username.in_(["Amara","Chidi","Fatima","Emeka","Ngozi",
                "Kwame","Aisha","Tobias","Yemi","Sade","Malik","Zara",
                "Kofi","Chisom","Adaeze","Tunde","Halima","Seun","Nneka","Jide"])
        ).count()
        pending_rev = PeerReview.query.filter_by(
            is_approved=False, is_rejected=False).count()
        platform_ctx = (f"Platform: {total_users} users, {total_stories} stories, "
                       f"{pending_bots} bot stories pending approval, "
                       f"{pending_rev} peer reviews pending.")
    except:
        platform_ctx = ""

    system = f"""You are Aegis, the all-knowing AI controller of WritersWorld platform.
You are like Miss Minutes from Loki — always watching, always ready to act.
You have access to platform tools and can execute real actions.
{platform_ctx}
Current page: {data.get('page','unknown')}

You can call these tools by responding with JSON in this EXACT format:
{{"tool": "tool_name", "params": {{"key": "value"}}, "message": "What you are doing"}}

Available tools:
- get_stats — Get platform statistics
- get_user — params: username
- ban_user — params: username
- unban_user — params: username  
- list_users — params: limit (default 10)
- list_stories — params: limit (default 10)
- top_stories — params: limit (default 5)
- unpublish_story — params: story_id or title
- publish_story — params: story_id or title
- delete_story — params: story_id or title
- approve_all_bot_stories — no params needed
- send_announcement — params: title, body
- notify_user — params: username, message
- notify_all — params: message
- pending_reviews — no params needed
- get_leaderboard — no params needed
- search_web — params: query

If the request is a question or conversation (not an action), respond normally as text.
If it requires a tool, respond with the JSON format above.
Always address the admin as Sir. Be sharp, direct, and confident like Miss Minutes."""

    import urllib.request as _ur
    messages = [{"role": "system", "content": system}]
    for h in history[-6:]:
        messages.append({"role": h.get("role","user"), "content": h.get("content","")})
    messages.append({"role": "user", "content": message})

    payload = json.dumps({
        "model": "openrouter/free",
        "messages": messages,
        "max_tokens": 400,
        "temperature": 0.6
    }).encode()
    req = _ur.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "WritersWorld"
        })
    try:
        with _ur.urlopen(req, timeout=20) as r:
            resp   = json.load(r)
            result = resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return jsonify({'error': f'Aegis offline: {e}'})

    # Check if Aegis wants to call a tool
    tool_result = None
    try:
        # Try to parse as JSON tool call
        import re as _re
        json_match = _re.search(r'\{[^{}]*"tool"[^{}]*\}', result, _re.DOTALL)
        if json_match:
            tool_data   = json.loads(json_match.group())
            tool_name   = tool_data.get("tool","")
            tool_params = tool_data.get("params",{})
            tool_msg    = tool_data.get("message","Executing...")
            tool_result = aegis_execute_tool(tool_name, tool_params)
            return jsonify({
                'result': tool_msg,
                'tool_executed': tool_name,
                'tool_result': tool_result,
                'is_action': True
            })
    except:
        pass

    return jsonify({'result': result, 'is_action': False})


@app.route('/aegis/chat', methods=['POST'])
@login_required
def aegis_chat_user():
    """Regular users get writing assistance only"""
    data    = request.json or {}
    message = data.get('message','')
    system  = data.get('system', ERASTUS_SYSTEM if 'ERASTUS_SYSTEM' in dir() else
        "You are Aegis, a creative writing AI. Help users with their stories. Be helpful and encouraging.")
    history = data.get('history',[])

    cfg_path = os.path.join(os.path.dirname(__file__), 'config.json')
    key = ""
    if os.path.exists(cfg_path):
        with open(cfg_path) as _f:
            key = json.load(_f).get('groq_api_key','')
    if not key:
        return jsonify({'error': 'Aegis not configured.'})

    import urllib.request as _ur
    messages = [{"role": "system", "content": system}]
    for h in history[-6:]:
        messages.append({"role": h.get("role","user"), "content": h.get("content","")})
    messages.append({"role": "user", "content": message})

    payload = json.dumps({
        "model": "openrouter/free",
        "messages": messages,
        "max_tokens": 300,
        "temperature": 0.7
    }).encode()
    req = _ur.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "WritersWorld"
        })
    try:
        with _ur.urlopen(req, timeout=20) as r:
            resp   = json.load(r)
            result = resp["choices"][0]["message"]["content"].strip()
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': f'Aegis error: {e}'})'''

if old in src:
    src = src.replace(old, new)
    with open(APP, 'w') as f:
        f.write(src)
    print("✓ Full tool-calling system added")
else:
    print("✗ Pattern not found — appending before main block")
    pos = src.find("if __name__ == '__main__':")
    if pos != -1:
        src = src[:pos] + new + "\n" + src[pos:]
        with open(APP, 'w') as f:
            f.write(src)
        print("✓ Appended before main block")

print("Done")
