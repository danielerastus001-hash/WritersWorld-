// ============================================================
//  AEGIS FLOATING AI — Miss Minutes Edition
//  Full tool-calling for admin, writing assist for users
// ============================================================

(function() {
  var IS_ADMIN = document.body.dataset.admin === 'true';

  // ── Floating button ──
  var fab = document.createElement('div');
  fab.id  = 'aegisFab';
  fab.innerHTML = '🤖';
  fab.style.cssText = [
    'position:fixed','bottom:80px','right:20px',
    'width:56px','height:56px',
    'background:linear-gradient(135deg,#00ff88,#00cc6a)',
    'border-radius:50%','display:flex',
    'align-items:center','justify-content:center',
    'font-size:1.5rem','cursor:pointer','z-index:1000',
    'box-shadow:0 4px 20px rgba(0,255,136,0.4)',
    'transition:transform 0.2s'
  ].join(';');

  // ── Chat panel ──
  var panel = document.createElement('div');
  panel.id  = 'aegisPanel';
  panel.style.cssText = [
    'position:fixed','bottom:148px','right:20px',
    'width:320px','max-height:500px',
    'background:#16161f','border:1px solid #00ff88',
    'border-radius:14px','display:none','flex-direction:column',
    'z-index:1000','box-shadow:0 8px 40px rgba(0,255,136,0.2)',
    'overflow:hidden'
  ].join(';');

  panel.innerHTML = [
    '<div style="background:linear-gradient(135deg,#004422,#002211);padding:14px 16px;display:flex;justify-content:space-between;align-items:center;">',
      '<div style="display:flex;align-items:center;gap:8px;">',
        '<span style="font-size:1.3rem;">🤖</span>',
        '<div>',
          '<div style="color:#00ff88;font-weight:700;font-size:0.92rem;">Aegis</div>',
          '<div style="color:#00cc6a;font-size:0.68rem;">' + (IS_ADMIN ? 'Platform Controller · Miss Minutes Mode' : 'Writing Assistant') + '</div>',
        '</div>',
      '</div>',
      '<div style="display:flex;gap:6px;align-items:center;">',
        '<button onclick="aegisClearMemory()" title="Clear chat" style="background:none;border:none;color:#666;cursor:pointer;font-size:0.85rem;padding:4px;">🗑</button>',
        '<button onclick="aegisClose()" style="background:none;border:none;color:#00ff88;cursor:pointer;font-size:1.1rem;padding:4px;">✕</button>',
      '</div>',
    '</div>',
    '<div id="aegisMsgs" style="flex:1;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:10px;max-height:320px;"></div>',
    IS_ADMIN ? '<div id="aegisQuickCmds" style="padding:8px 12px;border-top:1px solid #1e1e2e;display:flex;gap:6px;overflow-x:auto;flex-shrink:0;"></div>' : '',
    '<div style="padding:10px 12px;border-top:1px solid #1e1e2e;display:flex;gap:8px;flex-shrink:0;">',
      '<input id="aegisInput" type="text" placeholder="' + (IS_ADMIN ? 'Command Aegis...' : 'Ask Aegis...') + '"',
        'style="flex:1;background:#0a0a0f;border:1px solid #1e1e2e;color:#c8c8d8;padding:8px 12px;border-radius:8px;font-size:0.85rem;outline:none;"',
        'onkeydown="if(event.key===\'Enter\')aegisSend()">',
      '<button onclick="aegisSend()" style="background:#00ff88;color:#0a0a0f;border:none;border-radius:8px;padding:8px 12px;cursor:pointer;font-weight:700;font-size:0.85rem;">➤</button>',
    '</div>'
  ].join('');

  // ── Styles ──
  var style = document.createElement('style');
  style.textContent = [
    '#aegisFab:hover{transform:scale(1.1)}',
    '@keyframes aegisPulse{0%{box-shadow:0 4px 20px rgba(0,255,136,0.4)}50%{box-shadow:0 4px 30px rgba(0,255,136,0.8)}100%{box-shadow:0 4px 20px rgba(0,255,136,0.4)}}',
    '.aegis-bot{background:#1a2a1a;border:1px solid #004422;border-radius:10px 10px 10px 4px;padding:10px 12px;color:#c8c8d8;font-size:0.85rem;line-height:1.5;max-width:92%;}',
    '.aegis-user{background:#004422;border-radius:10px 10px 4px 10px;padding:10px 12px;color:#00ff88;font-size:0.85rem;align-self:flex-end;max-width:92%;}',
    '.aegis-action{background:#1a1a4a;border:1px solid #4444ff;border-radius:8px;padding:10px 12px;color:#aaaaff;font-size:0.82rem;max-width:92%;}',
    '.aegis-result{background:#0a2a0a;border:1px solid #006633;border-radius:8px;padding:10px 12px;color:#00cc88;font-size:0.8rem;max-width:92%;white-space:pre-wrap;}',
    '.aegis-error{background:#2a0a0a;border:1px solid #660000;border-radius:8px;padding:10px 12px;color:#ff6666;font-size:0.82rem;max-width:92%;}',
    '.aegis-typing{color:#00ff88;font-size:0.78rem;font-style:italic;padding:4px;}',
    '.aegis-cmd{background:#002211;border:1px solid #004422;color:#00ff88;padding:4px 10px;border-radius:12px;font-size:0.72rem;cursor:pointer;white-space:nowrap;flex-shrink:0;}',
    '.aegis-cmd:hover{background:#004422;}',
    '#aegisMsgs::-webkit-scrollbar{width:4px}',
    '#aegisMsgs::-webkit-scrollbar-thumb{background:#004422;border-radius:2px}'
  ].join('');
  document.head.appendChild(style);
  document.body.appendChild(panel);
  document.body.appendChild(fab);

  // ── Quick commands for admin ──
  if (IS_ADMIN) {
    var cmds = [
      ['📊 Stats',        'get stats'],
      ['⏳ Pending',      'show pending reviews'],
      ['🤖 Approve Bots', 'approve all bot stories'],
      ['👥 New Users',    'list latest users'],
      ['🏆 Top Stories',  'show top stories'],
      ['📢 Announce',     'send announcement: '],
    ];
    var cmdBox = document.getElementById('aegisQuickCmds');
    if (cmdBox) {
      cmds.forEach(function(c) {
        var btn = document.createElement('button');
        btn.className   = 'aegis-cmd';
        btn.textContent = c[0];
        btn.onclick = function() {
          var input = document.getElementById('aegisInput');
          input.value = c[1];
          input.focus();
          if (!c[1].endsWith(' ')) aegisSend();
        };
        cmdBox.appendChild(btn);
      });
    }
  }

  // ── Toggle ──
  fab.addEventListener('click', function() {
    if (panel.style.display === 'none') {
      panel.style.display = 'flex';
      fab.innerHTML = '✕';
      restoreMemory();
      if (!window._aegisGreeted) {
        window._aegisGreeted = true;
        setTimeout(aegisGreet, 300);
      }
      setTimeout(function() {
        var m = document.getElementById('aegisMsgs');
        if (m) m.scrollTop = m.scrollHeight;
      }, 100);
    } else {
      aegisClose();
    }
  });

  window.aegisClose = function() {
    panel.style.display = 'none';
    fab.innerHTML = '🤖';
  };

  // ── Memory ──
  var MEM_KEY = 'aegis_v2_memory';

  function saveMsg(role, text) {
    var mem = JSON.parse(localStorage.getItem(MEM_KEY) || '[]');
    mem.push({role: role, text: text, time: new Date().toISOString()});
    if (mem.length > 50) mem = mem.slice(-50);
    localStorage.setItem(MEM_KEY, JSON.stringify(mem));
  }

  function getHistory() {
    return JSON.parse(localStorage.getItem(MEM_KEY) || '[]').slice(-8).map(function(m) {
      return {role: m.role === 'user' ? 'user' : 'assistant', content: m.text};
    });
  }

  function restoreMemory() {
    var mem   = JSON.parse(localStorage.getItem(MEM_KEY) || '[]');
    var msgs  = document.getElementById('aegisMsgs');
    if (!msgs || msgs.children.length > 0) return;
    mem.slice(-6).forEach(function(m) {
      addMsg(m.text, m.role === 'user' ? 'user' : 'bot');
    });
  }

  window.aegisClearMemory = function() {
    localStorage.removeItem(MEM_KEY);
    var m = document.getElementById('aegisMsgs');
    if (m) m.innerHTML = '';
    addMsg('Memory cleared, Sir. Fresh start.', 'bot');
  };

  // ── Add message ──
  function addMsg(text, type) {
    var msgs = document.getElementById('aegisMsgs');
    if (!msgs) return;
    var div  = document.createElement('div');
    div.className = type === 'user' ? 'aegis-user' :
                    type === 'action' ? 'aegis-action' :
                    type === 'result' ? 'aegis-result' :
                    type === 'error'  ? 'aegis-error'  : 'aegis-bot';
    div.textContent = text;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
  }

  window.aegisAddMsg = addMsg;

  function setTyping(show) {
    var el = document.getElementById('aegisTyping');
    if (show && !el) {
      var d = document.createElement('div');
      d.id  = 'aegisTyping';
      d.className = 'aegis-typing';
      d.textContent = 'Aegis is working...';
      document.getElementById('aegisMsgs').appendChild(d);
      document.getElementById('aegisMsgs').scrollTop = 99999;
    } else if (!show && el) {
      el.remove();
    }
  }

  // ── Greet ──
  window.aegisGreet = function() {
    var h    = new Date().getHours();
    var greet= h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening';
    var page = window.location.pathname;
    var ctx  = page.includes('admin') ? 'the Control Centre' :
               page.includes('write') ? 'the story editor' :
               page.includes('dashboard') ? 'the dashboard' :
               page.includes('competition') ? 'the competitions page' : 'the platform';

    var msg = IS_ADMIN
      ? greet + ", Sir. I'm Aegis — your platform controller. You're on " + ctx + ". I'm watching everything. What would you like me to do?"
      : greet + "! I'm Aegis, your writing assistant. Need a story idea, grammar check, or tone analysis? I'm here to help.";

    addMsg(msg, 'bot');
    saveMsg('bot', msg);
  };

  // ── Send ──
  function formatResult(obj) {
    if (!obj) return 'Done.';
    var lines = [];
    Object.keys(obj).forEach(function(k) {
      var v = obj[k];
      if (Array.isArray(v)) {
        lines.push(k.toUpperCase() + ':');
        v.forEach(function(item, i) {
          if (typeof item === 'object') {
            var parts = Object.values(item).join(' | ');
            lines.push('  ' + (i+1) + '. ' + parts);
          } else {
            lines.push('  ' + (i+1) + '. ' + item);
          }
        });
      } else {
        lines.push(k + ': ' + v);
      }
    });
    return lines.join('\n');
  }

  window.aegisSend = function() {
    var input = document.getElementById('aegisInput');
    var text  = input.value.trim();
    if (!text) return;
    input.value = '';
    addMsg(text, 'user');
    saveMsg('user', text);
    setTyping(true);

    var endpoint = IS_ADMIN ? '/aegis/command' : '/aegis/chat';
    var page     = window.location.pathname;

    fetch(endpoint, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      credentials: 'same-origin',
      body: JSON.stringify({
        message: text,
        history: getHistory(),
        page: page,
        context: 'WritersWorld platform'
      })
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
      setTyping(false);
      if (data.error) {
        addMsg('✗ ' + data.error, 'error');
        return;
      }
      if (data.is_action && data.tool_executed) {
        addMsg('⚡ ' + (data.result || 'Executing...'), 'action');
        saveMsg('bot', data.result || '');
        if (data.tool_result) {
          var res = data.tool_result;
          if (res.error) {
            addMsg('✗ ' + res.error, 'error');
          } else if (res.success) {
            addMsg('✓ ' + res.success, 'result');
            saveMsg('bot', res.success);
          } else {
            var out = formatResult(res);
            addMsg(out, 'result');
            saveMsg('bot', out);
          }
        }
      } else if (data.result) {
        // Check if result is raw JSON tool call — execute it
        var raw = data.result.trim();
        var jsonMatch = raw.match(/\{[\s\S]*\"tool\"[\s\S]*\}/);
        if (jsonMatch) {
          try {
            var td = JSON.parse(jsonMatch[0]);
            if (td.tool) {
              addMsg('⚡ ' + (td.message || 'Executing ' + td.tool + '...'), 'action');
              fetch('/aegis/tool', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                credentials: 'same-origin',
                body: JSON.stringify({tool: td.tool, params: td.params || {}})
              })
              .then(function(r){return r.json();})
              .then(function(tr){
                if (tr.error) { addMsg('✗ ' + tr.error, 'error'); }
                else if (tr.success) { addMsg('✓ ' + tr.success, 'result'); }
                else { addMsg(formatResult(tr), 'result'); }
              });
              return;
            }
          } catch(e) {}
        }
        addMsg(raw, 'bot');
        saveMsg('bot', raw);
      }
    })
    .catch(function(e) {
      setTyping(false);
      addMsg('Connection error. Check server is running.', 'error');
    });
  };

  // ── Notification watcher ──
  var _lastBadge = -1;
  setInterval(function() {
    var badge = document.querySelector('.notif-badge');
    if (badge) {
      var n = parseInt(badge.textContent) || 0;
      if (_lastBadge >= 0 && n > _lastBadge && panel.style.display !== 'none') {
        addMsg('🔔 New notification arrived, Sir.', 'bot');
      }
      _lastBadge = n;
    }
  }, 30000);

})();
