// ============================================================
//  WRITERSWORLD — Main JavaScript
// ============================================================

// ── SIDEBAR TOGGLE ──
const sidebar        = document.getElementById('sidebar');
const overlay        = document.getElementById('sidebarOverlay');
const hamburger      = document.getElementById('hamburger');

function openSidebar() {
  if (sidebar)  sidebar.classList.add('open');
  if (overlay)  overlay.classList.add('visible');
}

function closeSidebar() {
  if (sidebar)  sidebar.classList.remove('open');
  if (overlay)  overlay.classList.remove('visible');
}

if (hamburger) hamburger.addEventListener('click', openSidebar);
if (overlay)   overlay.addEventListener('click', closeSidebar);

// ── FLASH MESSAGE AUTO-DISMISS ──
document.querySelectorAll('.alert').forEach(function(el) {
  setTimeout(function() {
    el.style.transition = 'opacity 0.5s';
    el.style.opacity    = '0';
    setTimeout(function() { el.remove(); }, 500);
  }, 4000);
});

// ── LIKE BUTTON ──
function likeStory(storyId) {
  var btn   = document.getElementById('like-btn');
  var count = document.getElementById('like-count');
  fetch('/like/' + storyId, {
    method: 'POST',
    headers: { 'X-CSRFToken': getCookie('csrf_token') }
  })
  .then(function(r) { return r.json(); })
  .then(function(data) {
    if (data.liked) {
      btn.classList.add('btn-green');
      btn.classList.remove('btn-outline');
      btn.textContent = '♥ ' + data.count;
    } else {
      btn.classList.remove('btn-green');
      btn.classList.add('btn-outline');
      btn.textContent = '♡ ' + data.count;
    }
  })
  .catch(function(e) { console.error('Like error:', e); });
}

// ── FOLLOW BUTTON ──
function followUser(userId) {
  var btn = document.getElementById('follow-btn');
  fetch('/follow/' + userId, {
    method: 'POST',
    headers: { 'X-CSRFToken': getCookie('csrf_token') }
  })
  .then(function(r) { return r.json(); })
  .then(function(data) {
    var fc = document.getElementById('follower-count');
    if (data.following) {
      btn.textContent = 'Unfollow';
      btn.classList.remove('btn-outline');
      btn.classList.add('btn-gray');
    } else {
      btn.textContent = 'Follow';
      btn.classList.add('btn-outline');
      btn.classList.remove('btn-gray');
    }
    if (fc) fc.textContent = data.count;
  })
  .catch(function(e) { console.error('Follow error:', e); });
}

// ── ADD TO READING LIST ──
function addToList(listId, storyId) {
  fetch('/list/add/' + listId + '/' + storyId, {
    method: 'POST',
    headers: { 'X-CSRFToken': getCookie('csrf_token') }
  })
  .then(function(r) { return r.json(); })
  .then(function(data) {
    if (data.success) {
      showToast('Added to reading list!');
      closeListModal();
    }
  })
  .catch(function(e) { console.error('List error:', e); });
}

// ── LIST MODAL ──
function openListModal() {
  var modal = document.getElementById('listModal');
  if (modal) modal.style.display = 'flex';
}

function closeListModal() {
  var modal = document.getElementById('listModal');
  if (modal) modal.style.display = 'none';
}

// ── AEGIS AI ──
function aegisGrammar() {
  var text   = document.getElementById('storyContent');
  var result = document.getElementById('aegisResult');
  if (!text || !text.value.trim()) {
    showAegisResult('Please write some text first.');
    return;
  }
  showAegisResult('Aegis is checking your grammar...');
  fetch('/aegis/grammar', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrf_token')
    },
    body: JSON.stringify({ text: text.value.substring(0, 2000) })
  })
  .then(function(r) { return r.json(); })
  .then(function(data) {
    if (data.error) {
      showAegisResult('Error: ' + data.error);
    } else {
      showAegisResult(data.result);
    }
  })
  .catch(function(e) { showAegisResult('Aegis unavailable. Check internet.'); });
}

function aegisIdea() {
  var genre  = document.getElementById('storyGenre');
  var result = document.getElementById('aegisResult');
  var g      = genre ? genre.value : 'General';
  showAegisResult('Aegis is generating a story idea...');
  fetch('/aegis/idea', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrf_token')
    },
    body: JSON.stringify({ genre: g })
  })
  .then(function(r) { return r.json(); })
  .then(function(data) {
    if (data.error) {
      showAegisResult('Error: ' + data.error);
    } else {
      showAegisResult(data.result);
    }
  })
  .catch(function(e) { showAegisResult('Aegis unavailable. Check internet.'); });
}

function aegisTone() {
  var text = document.getElementById('storyContent');
  if (!text || !text.value.trim()) {
    showAegisResult('Please write some text first.');
    return;
  }
  showAegisResult('Aegis is analyzing the tone...');
  fetch('/aegis/tone', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrf_token')
    },
    body: JSON.stringify({ text: text.value.substring(0, 2000) })
  })
  .then(function(r) { return r.json(); })
  .then(function(data) {
    if (data.error) {
      showAegisResult('Error: ' + data.error);
    } else {
      showAegisResult(data.result);
    }
  })
  .catch(function(e) { showAegisResult('Aegis unavailable. Check internet.'); });
}

function showAegisResult(text) {
  var el = document.getElementById('aegisResult');
  if (el) {
    el.textContent = text;
    el.classList.add('visible');
  }
}

function applyGrammarFix() {
  var result  = document.getElementById('aegisResult');
  var content = document.getElementById('storyContent');
  if (!result || !content) return;
  if (confirm('Apply all grammar fixes to your story? This will update your text.')) {
    showToast('Fixes noted. Please apply them manually from the suggestions above.');
  }
}

// ── SHARE BUTTONS ──
function shareWhatsApp(title, url) {
  var text = encodeURIComponent('Read "' + title + '" on WritersWorld: ' + url);
  window.open('https://wa.me/?text=' + text, '_blank');
}

function shareTwitter(title, url) {
  var text = encodeURIComponent('"' + title + '" on WritersWorld');
  window.open('https://twitter.com/intent/tweet?text=' + text + '&url=' + encodeURIComponent(url), '_blank');
}

function shareFacebook(url) {
  window.open('https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(url), '_blank');
}

function copyLink(url) {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(url).then(function() {
      showToast('Link copied to clipboard!');
    });
  } else {
    var el = document.createElement('textarea');
    el.value = url;
    document.body.appendChild(el);
    el.select();
    document.execCommand('copy');
    document.body.removeChild(el);
    showToast('Link copied!');
  }
}

// ── TOAST NOTIFICATION ──
function showToast(message) {
  var toast = document.getElementById('toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'toast';
    toast.style.cssText = [
      'position:fixed', 'bottom:20px', 'left:50%',
      'transform:translateX(-50%)',
      'background:#00ff88', 'color:#0a0a0f',
      'padding:10px 20px', 'border-radius:6px',
      'font-weight:700', 'font-size:0.9rem',
      'z-index:9999', 'transition:opacity 0.3s',
      'box-shadow:0 4px 20px rgba(0,255,136,0.3)'
    ].join(';');
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.style.opacity = '1';
  toast.style.display = 'block';
  setTimeout(function() {
    toast.style.opacity = '0';
    setTimeout(function() { toast.style.display = 'none'; }, 300);
  }, 3000);
}

// ── CONFIRM DELETE ──
function confirmDelete(formId, message) {
  if (confirm(message || 'Are you sure? This cannot be undone.')) {
    document.getElementById(formId).submit();
  }
}

function confirmAction(formId, message) {
  if (confirm(message)) {
    document.getElementById(formId).submit();
  }
}

// ── CSRF COOKIE HELPER ──
function getCookie(name) {
  var value = '; ' + document.cookie;
  var parts = value.split('; ' + name + '=');
  if (parts.length === 2) return parts.pop().split(';').shift();
  return '';
}

// ── WORD COUNT ──
var wordCountEl = document.getElementById('wordCount');
var contentEl   = document.getElementById('storyContent');

if (contentEl && wordCountEl) {
  contentEl.addEventListener('input', function() {
    var words = contentEl.value.trim().split(/\s+/).filter(Boolean).length;
    var chars = contentEl.value.length;
    wordCountEl.textContent = words + ' words · ' + chars + ' characters';
  });
}

// ── AUTO SAVE DRAFT ──
var autoSaveTimer = null;
var autoSaveStatus = document.getElementById('autoSaveStatus');

if (contentEl) {
  contentEl.addEventListener('input', function() {
    if (autoSaveStatus) {
      autoSaveStatus.textContent = 'Unsaved changes...';
      autoSaveStatus.style.color = '#ffcc00';
    }
    clearTimeout(autoSaveTimer);
    autoSaveTimer = setTimeout(function() {
      var title = document.getElementById('storyTitle');
      if (title && title.value.trim() && contentEl.value.trim()) {
        localStorage.setItem('ww_draft_title',   title.value);
        localStorage.setItem('ww_draft_content', contentEl.value);
        if (autoSaveStatus) {
          autoSaveStatus.textContent = 'Draft saved locally';
          autoSaveStatus.style.color = '#00ff88';
        }
      }
    }, 2000);
  });

  // Restore draft if fields empty
  var savedTitle   = localStorage.getItem('ww_draft_title');
  var savedContent = localStorage.getItem('ww_draft_content');
  var titleEl      = document.getElementById('storyTitle');
  if (titleEl && contentEl && savedTitle && !titleEl.value && !contentEl.value) {
    if (confirm('You have an unsaved draft. Restore it?')) {
      titleEl.value   = savedTitle;
      contentEl.value = savedContent;
    }
  }
}

function clearDraft() {
  localStorage.removeItem('ww_draft_title');
  localStorage.removeItem('ww_draft_content');
}

// Clear draft on successful form submit
var writeForm = document.getElementById('writeForm');
if (writeForm) {
  writeForm.addEventListener('submit', clearDraft);
}

// ── PUBLISH TOGGLE ──
function setPublish(value) {
  var inp = document.getElementById('publishInput');
  var btn = document.getElementById('publishBtn');
  if (inp) inp.value = value;
  if (btn) {
    if (value === 'true') {
      btn.textContent = 'Publish Story';
      btn.className   = 'btn btn-green';
    } else {
      btn.textContent = 'Save as Draft';
      btn.className   = 'btn btn-gray';
    }
  }
}

// ── COMPETITION STATUS COLOR ──
document.querySelectorAll('.comp-status').forEach(function(el) {
  var status = el.textContent.trim();
  el.classList.add('status-' + status);
});

// ── ADMIN: PREVIEW ANNOUNCEMENT IMAGE ──
var announceImg = document.getElementById('announceImage');
var announcePreview = document.getElementById('announcePreview');
if (announceImg && announcePreview) {
  announceImg.addEventListener('change', function() {
    var file = announceImg.files[0];
    if (file) {
      var reader = new FileReader();
      reader.onload = function(e) {
        announcePreview.src     = e.target.result;
        announcePreview.style.display = 'block';
      };
      reader.readAsDataURL(file);
    }
  });
}

// ── COVER IMAGE PREVIEW ──
var coverInput   = document.getElementById('coverInput');
var coverPreview = document.getElementById('coverPreview');
if (coverInput && coverPreview) {
  coverInput.addEventListener('change', function() {
    var file = coverInput.files[0];
    if (file) {
      var reader = new FileReader();
      reader.onload = function(e) {
        coverPreview.src          = e.target.result;
        coverPreview.style.display = 'block';
      };
      reader.readAsDataURL(file);
    }
  });
}

// ── SEARCH ON ENTER ──
var searchInput = document.getElementById('searchInput');
if (searchInput) {
  searchInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
      document.getElementById('searchForm').submit();
    }
  });
}

// ── SCROLL TO TOP ──
var scrollBtn = document.getElementById('scrollTop');
if (scrollBtn) {
  window.addEventListener('scroll', function() {
    scrollBtn.style.display = window.scrollY > 300 ? 'block' : 'none';
  });
  scrollBtn.addEventListener('click', function() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

// ── CHAT AUTO SCROLL ──
var chatMessages = document.querySelector('.chat-messages');
if (chatMessages) {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ── MODAL CLOSE ON OUTSIDE CLICK ──
document.addEventListener('click', function(e) {
  var modal = document.getElementById('listModal');
  if (modal && e.target === modal) {
    closeListModal();
  }
});

// ── GENRE FILTER ──
var genreSelect = document.getElementById('genreFilter');
if (genreSelect) {
  genreSelect.addEventListener('change', function() {
    document.getElementById('searchForm').submit();
  });
}
