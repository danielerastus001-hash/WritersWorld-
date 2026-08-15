#!/usr/bin/env python3
# ─────────────────────────────────────────────
#  FULL PATCH — Peer Reviews + Awards + Notifs
#  Run: python3 full_patch.py
# ─────────────────────────────────────────────

import os

APP  = os.path.expanduser("~/writersworld/app.py")
ADM  = os.path.expanduser("~/writersworld/templates/admin.html")
PROF = os.path.expanduser("~/writersworld/templates/profile.html")

with open(APP) as f:
    app = f.read()

patches = 0

# ── 1. Notify admin when competition entry submitted ──
old = '''        db.session.commit()
        flash('Entry submitted!', 'success')
        return redirect(url_for('competition_view', comp_id=comp_id))
    return render_template('competition_write.html',
                           comp=comp, entry=existing)'''

new = '''        admin = User.query.filter_by(is_admin=True).first()
        if admin:
            add_notification(
                admin.id,
                f"New competition entry: '{title}' by {current_user.username} for '{comp.title}'",
                'competition',
                url_for('competition_view', comp_id=comp_id))
        db.session.commit()
        flash('Entry submitted!', 'success')
        return redirect(url_for('competition_view', comp_id=comp_id))
    return render_template('competition_write.html',
                           comp=comp, entry=existing)'''

if old in app:
    app = app.replace(old, new)
    patches += 1
    print("✓ Admin notified on competition entry")
else:
    print("✗ Entry notification pattern not found")

# ── 2. Notify admin on peer review ──
old2 = '''        db.session.add(review)
        # Notify admin
        admin = User.query.filter_by(is_admin=True).first()
        if admin:
            add_notification(admin.id,
                f"New peer review submitted for '{entry.title}'",
                'review', url_for('admin_panel'))
        db.session.commit()
        flash('Review submitted! Awaiting admin approval.', 'success')'''

new2 = '''        db.session.add(review)
        admin = User.query.filter_by(is_admin=True).first()
        if admin:
            add_notification(
                admin.id,
                f"New peer review by {current_user.username} for '{entry.title}' — needs your approval",
                'review',
                url_for('admin_panel'))
        db.session.commit()
        flash('Review submitted! Awaiting admin approval.', 'success')'''

if old2 in app:
    app = app.replace(old2, new2)
    patches += 1
    print("✓ Peer review notification improved")
else:
    print("✗ Peer review pattern not found")

# ── 3. Pass pending reviews to admin panel ──
old3 = '''    republish_requests = Story.query.filter_by(pending_republish=True).all()
    return render_template('admin.html',
        users=users, stories=stories,
        comments=comments,
        announcements=announcements,
        competitions=competitions,
        republish_requests=republish_requests)'''

new3 = '''    republish_requests = Story.query.filter_by(pending_republish=True).all()
    pending_reviews    = PeerReview.query.filter_by(
                          is_approved=False, is_rejected=False).all()
    return render_template('admin.html',
        users=users, stories=stories,
        comments=comments,
        announcements=announcements,
        competitions=competitions,
        republish_requests=republish_requests,
        pending_reviews=pending_reviews)'''

if old3 in app:
    app = app.replace(old3, new3)
    patches += 1
    print("✓ Pending reviews passed to admin")
else:
    print("✗ Admin panel pattern not found")

# ── 4. Notify writer when review approved ──
old4 = '''    if action == 'approve':
        review.is_approved = True
        review.is_rejected = False
        add_notification(review.entry.user_id,
            f"A peer review for your competition entry has been approved.",
            'review')
    elif action == 'reject':
        review.is_rejected = True
        review.is_approved = False
    db.session.commit()
    flash(f'Review {action}d.', 'success')
    return redirect(url_for('admin_panel'))'''

new4 = '''    if action == 'approve':
        review.is_approved = True
        review.is_rejected = False
        add_notification(
            review.entry.user_id,
            f"A peer review for your entry '{review.entry.title}' has been approved by admin. You can now read it.",
            'review',
            url_for('competition_view', comp_id=review.entry.competition_id))
        add_notification(
            review.reviewer_id,
            f"Your peer review for '{review.entry.title}' was approved by admin.",
            'success')
    elif action == 'reject':
        review.is_rejected = True
        review.is_approved = False
        add_notification(
            review.reviewer_id,
            f"Your peer review for '{review.entry.title}' was not approved by admin.",
            'warning')
    db.session.commit()
    flash(f'Review {action}d.', 'success')
    return redirect(url_for('admin_panel'))'''

if old4 in app:
    app = app.replace(old4, new4)
    patches += 1
    print("✓ Writer notified when review approved")
else:
    print("✗ Review action pattern not found")

# ── 5. Pass awards to profile ──
old5 = '''    awards = Award.query.filter_by(user_id=user_id)\
                        .order_by(Award.created_at.desc()).all()
    return render_template('profile.html',
        user=user, stories=stories, drafts=drafts,
        is_owner=is_owner, following=following, awards=awards)'''

if old5 in app:
    print("✓ Awards already passed to profile")
else:
    old5b = '''    return render_template('profile.html',
        user=user, stories=stories, drafts=drafts,
        is_owner=is_owner, following=following)'''
    new5b = '''    awards = Award.query.filter_by(user_id=user_id)\
                        .order_by(Award.created_at.desc()).all()
    return render_template('profile.html',
        user=user, stories=stories, drafts=drafts,
        is_owner=is_owner, following=following, awards=awards)'''
    if old5b in app:
        app = app.replace(old5b, new5b)
        patches += 1
        print("✓ Awards added to profile route")
    else:
        print("✗ Profile route pattern not found")

with open(APP, 'w') as f:
    f.write(app)

# ── 6. Add peer reviews section to admin.html ──
with open(ADM) as f:
    adm = f.read()

peer_section = '''
<div class="admin-section" id="reviews">
  <h2>📝 Pending Peer Reviews
    {% if pending_reviews %}
    <span style="background:var(--red);color:#fff;border-radius:12px;padding:2px 10px;font-size:0.78rem;margin-left:8px;animation:pulse 1.5s infinite;">{{ pending_reviews|length }}</span>
    {% endif %}
  </h2>
  {% if pending_reviews %}
  {% for review in pending_reviews %}
  <div class="card" style="border-left:4px solid var(--green); margin-bottom:12px;">
    <div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px; align-items:flex-start;">
      <div style="flex:1;">
        <h4 style="color:var(--green);">Entry: {{ review.entry.title }}</h4>
        <p class="text-dim" style="font-size:0.82rem; margin-top:4px;">
          Reviewer: <strong>{{ review.reviewer.username }}</strong> |
          Submitted: {{ review.submitted_at.strftime('%d %b %Y') }}
        </p>
        <div style="margin-top:12px; background:var(--dark); border-radius:6px; padding:12px; font-size:0.85rem;">
          <p style="color:var(--green); font-weight:600; margin-bottom:6px;">Review Answers:</p>
          <p><strong>Q1:</strong> {{ review.q1 }}</p>
          <p style="margin-top:6px;"><strong>Q2:</strong> {{ review.q2 }}</p>
          <p style="margin-top:6px;"><strong>Q3:</strong> {{ review.q3 }}</p>
          <p style="margin-top:6px;"><strong>Q4:</strong> {{ review.q4 }}</p>
          <p style="margin-top:6px;"><strong>Q5:</strong> {{ review.q5 }}</p>
          {% if review.extra %}
          <p style="margin-top:6px;"><strong>Extra:</strong> {{ review.extra }}</p>
          {% endif %}
        </div>
      </div>
      <div style="display:flex; flex-direction:column; gap:8px;">
        <form method="POST" action="{{ url_for('admin_review_action', review_id=review.id, action='approve') }}">
          <button type="submit" class="btn btn-green btn-sm">✓ Approve</button>
        </form>
        <form method="POST" action="{{ url_for('admin_review_action', review_id=review.id, action='reject') }}">
          <button type="submit" class="btn btn-red btn-sm">✗ Reject</button>
        </form>
      </div>
    </div>
  </div>
  {% endfor %}
  {% else %}
  <div class="card" style="text-align:center; color:var(--text-dim); padding:20px; font-size:0.88rem;">
    No pending peer reviews.
  </div>
  {% endif %}
</div>
'''

if 'id="reviews"' not in adm:
    # Add after republish section
    adm = adm.replace(
        '<div class="admin-section">\n  <h2>👥 All Users',
        peer_section + '\n<div class="admin-section">\n  <h2>👥 All Users'
    )
    with open(ADM, 'w') as f:
        f.write(adm)
    patches += 1
    print("✓ Peer reviews section added to admin")
else:
    print("✓ Peer reviews section already in admin")

# ── 7. Fix awards display on profile ──
with open(PROF) as f:
    prof = f.read()

awards_block = '''{% if awards is defined and awards %}
<div class="card" style="margin-bottom:20px;">
  <h3 style="color:var(--green); margin-bottom:14px;">🏅 Awards & Badges</h3>
  <div style="display:flex; flex-wrap:wrap; gap:10px;">
    {% for award in awards %}
    <div style="background:var(--dark); border:1px solid var(--green-dark); border-radius:10px; padding:10px 14px; text-align:center; min-width:90px;">
      <div style="font-size:1.8rem; line-height:1;">{{ award.icon }}</div>
      <div style="color:var(--green); font-size:0.78rem; font-weight:700; margin-top:6px;">{{ award.name }}</div>
      <div style="color:var(--text-dim); font-size:0.7rem; margin-top:2px;">{{ award.reason }}</div>
      <div style="color:var(--text-dim); font-size:0.68rem; margin-top:2px;">{{ award.created_at.strftime('%d %b %Y') }}</div>
    </div>
    {% endfor %}
  </div>
</div>
{% endif %}'''

if 'Awards & Badges' not in prof:
    prof = prof.replace(
        '{% if current_user.is_authenticated and current_user.is_admin %}',
        awards_block + '\n\n{% if current_user.is_authenticated and current_user.is_admin %}'
    )
    with open(PROF, 'w') as f:
        f.write(prof)
    patches += 1
    print("✓ Awards badges shown on profile")
else:
    print("✓ Awards already on profile")

print(f"\n✅ {patches} patches applied.")
