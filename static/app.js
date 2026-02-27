function submitDispute() {
  const textEl = document.getElementById("userInput");
  const submitBtn = document.getElementById('submitBtn');
  const spinner = document.getElementById('spinner');
  const statusEl = document.getElementById("statusText");
  const explanationEl = document.getElementById("explanationText");
  const text = textEl.value.trim();
  if (!text) {
    textEl.focus();
    return;
  }

  // UI: show processing state
  submitBtn.disabled = true;
  spinner.setAttribute('aria-hidden', 'false');
  statusEl.innerText = "Processing...";
  explanationEl.innerText = "";

  fetch("/dispute", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text })
  })
    .then(res => res.json())
    .then(data => {
      if (data.questions && data.questions.length) {
        statusEl.innerText = "Need more information";
        explanationEl.innerText = data.questions[0];
      } else {
        statusEl.innerText = data.status || 'Result';
        explanationEl.innerText = data.explanation || '';
      }
    })
    .catch(() => {
      statusEl.innerText = "Error";
      explanationEl.innerText = "Something went wrong. Please try again.";
    })
    .finally(() => {
      submitBtn.disabled = false;
      spinner.setAttribute('aria-hidden', 'true');
    });
}

// Load disputes for dashboard
function loadDisputes() {
  fetch('/disputes')
    .then(res => res.json())
    .then(data => {
      const tbody = document.querySelector('#disputeTable tbody');
      const total = document.getElementById('totalCount');
      const open = document.getElementById('openCount');
      const resolved = document.getElementById('resolvedCount');
      const rejected = document.getElementById('rejectedCount');
      tbody.innerHTML = '';

      if (!data || data.length === 0) {
        const empty = document.getElementById('emptyState'); if (empty) empty.hidden = false;
        if (total) total.innerText = '0';
        return;
      }

      // Stats
      const stats = { total: data.length, pending: 0, approved: 0, rejected: 0 };
      data.forEach(d => {
        const computed = computeStatus(d);
        if (computed.key === 'pending') stats.pending++;
        if (computed.key === 'approved') stats.approved++;
        if (computed.key === 'rejected') stats.rejected++;
      });
      if (total) total.innerText = stats.total;
      if (open) open.innerText = stats.pending;
      if (resolved) resolved.innerText = stats.approved;
      if (rejected) rejected.innerText = stats.rejected;
      
      // animate counters
      if (total) animateCount(total, stats.total);
      if (open) animateCount(open, stats.open);
      if (resolved) animateCount(resolved, stats.resolved);
      if (rejected) animateCount(rejected, stats.rejected);

      data.forEach(d => {
        const row = document.createElement('tr');
        const computed = computeStatus(d);
        const statusClass = computed.key; // 'approved' | 'rejected' | 'pending' | 'unknown'
        const label = computed.label;
        row.innerHTML = `
          <td>${d.transaction_id || '-'}</td>
          <td><span class="badge ${statusClass}" title="${d.final_status || ''}">${label}</span></td>
          <td>${d.explanation || '-'}</td>
          <td>${d.created_at || '-'}</td>
        `;
        tbody.appendChild(row);
      });

      // wire search
      const search = document.getElementById('searchInput');
      if (search) {
        search.addEventListener('input', (e) => filterDisputes(e.target.value, data));
      }
    })
    .catch(() => {
      const empty = document.getElementById('emptyState'); if (empty) empty.hidden = false;
    });
}

function filterDisputes(query, data) {
  const q = (query || '').toLowerCase().trim();
  const tbody = document.querySelector('#disputeTable tbody');
  tbody.innerHTML = '';
  const filtered = data.filter(d => {
    if (!q) return true;
    return (d.transaction_id || '').toLowerCase().includes(q)
      || (d.explanation || '').toLowerCase().includes(q)
      || (d.merchant_name || '').toLowerCase().includes(q)
      || (d.utr || '').toLowerCase().includes(q);
  });
  if (filtered.length === 0) {
    const empty = document.getElementById('emptyState'); if (empty) empty.hidden = false;
  }
  filtered.forEach(d => {
    const row = document.createElement('tr');
    const computed = computeStatus(d);
    const statusClass = computed.key;
    const label = computed.label;
    row.innerHTML = `
      <td>${d.transaction_id || '-'}</td>
      <td><span class="badge ${statusClass}" title="${d.final_status || ''}">${label}</span></td>
      <td>${d.explanation || '-'}</td>
      <td>${d.created_at || '-'}</td>
    `;
    tbody.appendChild(row);
  });
}

// derive a simple status label and key from whatever data we have
function computeStatus(d) {
  const raw = (d.final_status || '').toLowerCase();
  const text = (d.explanation || '').toLowerCase();
  const source = raw || text || '';

  // keyword maps
  const approvedWords = ['resolved', 'success', 'settled', 'approved', 'completed'];
  const rejectedWords = ['reject', 'failed', 'declined', 'error', 'denied', 'unauthorized'];
  const pendingWords = ['open', 'pending', 'escalate', 'escalated', 'review', 'processing', 'need more', 'awaiting'];

  for (const w of approvedWords) if (source.includes(w)) return { key: 'approved', label: 'Approved' };
  for (const w of rejectedWords) if (source.includes(w)) return { key: 'rejected', label: 'Rejected' };
  for (const w of pendingWords) if (source.includes(w)) return { key: 'pending', label: 'Pending' };

  // fallback: if there is some final_status text, show a cleaned version
  if (raw) return { key: raw.replace(/\s+/g,'-'), label: (d.final_status || raw).toString() };
  // last resort
  return { key: 'pending', label: 'Pending' };
}

// Chat: append messages and handle send
function appendMessage(role, text) {
  const win = document.getElementById('chatWindow');
  if (!win) return;
  const msg = document.createElement('div');
  msg.className = 'message ' + (role === 'user' ? 'user' : 'bot');
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = text;
  const meta = document.createElement('div');
  meta.className = 'meta';
  meta.textContent = role === 'user' ? 'You' : 'Assistant';
  msg.appendChild(bubble);
  msg.appendChild(meta);
  win.appendChild(msg);
  // animate bubble in
  bubble.style.animation = 'bubbleIn 320ms cubic-bezier(.2,.9,.2,1) both';
  win.scrollTop = win.scrollHeight;
}

// simple count-up animation for stat cards
function animateCount(el, to) {
  const start = 0;
  const duration = 800;
  let startTime = null;
  function step(ts) {
    if (!startTime) startTime = ts;
    const progress = Math.min((ts - startTime) / duration, 1);
    const value = Math.floor(progress * (to - start) + start);
    el.innerText = value;
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

// entrance animations + focus behavior
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.card').forEach((c, i) => {
    setTimeout(() => c.classList.add('animate-in'), 70 * i);
  });
  const chatInput = document.getElementById('chatInput');
  if (chatInput) chatInput.focus();
});

function submitDisputeChat() {
  const input = document.getElementById('chatInput');
  const text = (input && input.value || '').trim();
  if (!text) return;
  appendMessage('user', text);
  input.value = '';

  const spinner = document.getElementById('spinner');
  const statusEl = document.getElementById('statusText');
  const explanationEl = document.getElementById('explanationText');
  spinner.setAttribute('aria-hidden','false');
  statusEl.innerText = 'Processing...';
  explanationEl.innerText = '';

  fetch('/dispute', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ message: text }) })
    .then(res => res.json())
    .then(data => {
      if (data.questions && data.questions.length) {
        appendMessage('bot', data.questions[0]);
        statusEl.innerText = 'Need more information';
        explanationEl.innerText = data.questions[0];
      } else {
        const reply = data.explanation || data.status || 'Done';
        appendMessage('bot', reply);
        statusEl.innerText = data.status || 'Result';
        explanationEl.innerText = data.explanation || '';
      }
    })
    .catch(() => {
      appendMessage('bot', 'Sorry — something went wrong.');
      statusEl.innerText = 'Error';
      explanationEl.innerText = 'Something went wrong. Please try again.';
    })
    .finally(() => spinner.setAttribute('aria-hidden','true'));
}