// ── GlideTrip Mockup — Interactive Script ────────────────────────────────────

// ── Mock Data ────────────────────────────────────────────────────────────────
const MOCK_FLIGHTS = [
  { airline: 'Air India', code: 'AI', flight: 'AI 302', dep: 'DEL', depTime: '07:15', arr: 'GOI', arrTime: '09:40', duration: '2h 25m', class: 'Economy', price: '4,830', logo: null },
  { airline: 'IndiGo', code: '6E', flight: '6E 891', dep: 'DEL', depTime: '11:40', arr: 'GOI', arrTime: '14:10', duration: '2h 30m', class: 'Economy', price: '3,210', logo: null },
  { airline: 'Vistara', code: 'UK', flight: 'UK 847', dep: 'DEL', depTime: '16:05', arr: 'GOI', arrTime: '18:25', duration: '2h 20m', class: 'Economy', price: '5,470', logo: null },
  { airline: 'SpiceJet', code: 'SG', flight: 'SG 136', dep: 'DEL', depTime: '20:30', arr: 'GOI', arrTime: '23:05', duration: '2h 35m', class: 'Economy', price: '2,890', logo: null },
];

const MOCK_HOTELS = [
  { name: 'Taj Fort Aguada Resort & Spa', stars: 5, rating: 4.7, reviews: '2,148', price: '12,450', thumb: 'https://picsum.photos/seed/tajgoa/128/128', address: 'Sinquerim, Candolim, North Goa' },
  { name: 'DoubleTree by Hilton Panaji', stars: 4, rating: 4.3, reviews: '1,876', price: '6,320', thumb: 'https://picsum.photos/seed/hiltonpanaji/128/128', address: 'Dayanand Bandodkar Marg, Panaji' },
  { name: 'Acron Waterfront Resort', stars: 4, rating: 4.5, reviews: '934', price: '4,180', thumb: 'https://picsum.photos/seed/acronbaga/128/128', address: 'Baga River Road, Baga' },
];

const MOCK_PLACES = [
  { name: 'Basilica of Bom Jesus', type: 'Heritage site', rating: 4.6, desc: 'UNESCO World Heritage Site, houses the mortal remains of St. Francis Xavier in a silver casket.', thumb: 'https://picsum.photos/seed/bomjesus/128/128', address: 'Old Goa, Goa' },
  { name: 'Cafe Bodega', type: 'Cafe', rating: 4.4, desc: 'Charming courtyard cafe in a restored colonial art gallery, known for its European-style pastries.', thumb: 'https://picsum.photos/seed/cafebodega/128/128', address: 'Sunaparanta Centre, Altinho, Panaji' },
  { name: 'Dudhsagar Falls', type: 'Waterfall', rating: 4.8, desc: 'Four-tiered waterfall on the Mandovi River, one of the tallest in India at 310m.', thumb: 'https://picsum.photos/seed/dudhsagar/128/128', address: 'Mollem National Park, Sanguem' },
  { name: 'Gunpowder', type: 'Kerala cuisine', rating: 4.5, desc: 'Relaxed open-air restaurant serving authentic South Indian thalis and Malabar seafood.', thumb: 'https://picsum.photos/seed/gunpowder/128/128', address: 'Assagao, Bardez, North Goa' },
];

const MOCK_CHAT = [
  {
    role: 'user',
    content: 'Plan a weekend trip to Goa from Delhi. Budget-friendly flights and a nice hotel near the beach.'
  },
  {
    role: 'assistant',
    steps: ['Searching Flights...', 'Searching Hotels...', 'Searching Local Places...'],
    content: `<h3>Here's your Goa weekend plan</h3>
<p>I found <strong>4 flights</strong> from Delhi to Goa, <strong>3 beachside hotels</strong>, and some top-rated places to visit.</p>

<p><strong>Best value flight:</strong> SpiceJet SG 136 at <strong>Rs 2,890</strong> — departs 20:30, perfect for a Friday night departure.</p>

<p><strong>Recommended stay:</strong> Acron Waterfront Resort in Baga at <strong>Rs 4,180/night</strong> — 4-star, rated 4.5 with direct river access and 10 min walk to Baga Beach.</p>

<h3>Must-visit spots</h3>
<ul>
<li><strong>Basilica of Bom Jesus</strong> — UNESCO heritage, free entry</li>
<li><strong>Dudhsagar Falls</strong> — book a jeep safari, best visited early morning</li>
<li><strong>Cafe Bodega</strong> — perfect for a relaxed brunch in Panaji</li>
<li><strong>Gunpowder</strong> — authentic Kerala thali in a garden setting</li>
</ul>

<p>Want me to check specific dates or find restaurants near your hotel?</p>`
  }
];

// ── DOM Refs ─────────────────────────────────────────────────────────────────
const landing = document.getElementById('landing');
const copilot = document.getElementById('copilot');
const landingForm = document.getElementById('landingForm');
const landingInput = document.getElementById('landingInput');
const chatFeed = document.getElementById('chatFeed');
const chatInput = document.getElementById('chatInput');
const chatSend = document.getElementById('chatSend');
const tabBtns = document.querySelectorAll('.tab-btn');
const tabPanels = document.querySelectorAll('.tab-content');

// ── Transition: Landing -> Copilot ───────────────────────────────────────────
function activateCopilot(query) {
  landing.classList.add('hidden');
  copilot.classList.add('active');

  // Populate mock data
  renderFlights();
  renderHotels();
  renderPlaces();

  // Simulate chat with delay
  simulateChat(query);
}

// ── Landing form submit ──────────────────────────────────────────────────────
landingForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const q = landingInput.value.trim();
  if (q) activateCopilot(q);
});

// Chip clicks
document.querySelectorAll('.chip').forEach(chip => {
  chip.addEventListener('click', () => {
    activateCopilot(chip.dataset.query);
  });
});

// ── Chat simulation ──────────────────────────────────────────────────────────
async function simulateChat(query) {
  // Add user message
  addMessage('user', query || MOCK_CHAT[0].content);

  // Show typing dots
  const dotsEl = addTypingDots();
  await delay(800);

  // Replace dots with steps
  dotsEl.remove();
  const stepsEl = addStepsExpander(MOCK_CHAT[1].steps);
  await delay(600);

  // Simulate steps completing one by one
  const dots = stepsEl.querySelectorAll('.step-dot');
  for (let i = 0; i < dots.length; i++) {
    dots[i].classList.remove('active');
    if (i + 1 < dots.length) dots[i + 1].classList.add('active');
    await delay(500);
  }
  // Mark last done
  dots[dots.length - 1].classList.remove('active');
  await delay(300);

  // Add AI response with typing effect
  addMessage('assistant', MOCK_CHAT[1].content);
  scrollChat();
}

function addMessage(role, content) {
  const msg = document.createElement('div');
  msg.className = `msg msg-${role}`;

  if (role === 'user') {
    msg.innerHTML = `<div class="bubble-user">${escapeHtml(content)}</div>`;
  } else {
    msg.innerHTML = `<div class="ai-content">${content}</div>`;
  }

  chatFeed.appendChild(msg);
  scrollChat();
  return msg;
}

function addTypingDots() {
  const el = document.createElement('div');
  el.className = 'msg msg-ai';
  el.innerHTML = `<div class="typing-dots"><span></span><span></span><span></span></div>`;
  chatFeed.appendChild(el);
  scrollChat();
  return el;
}

function addStepsExpander(steps) {
  const el = document.createElement('div');
  el.className = 'msg msg-ai';
  el.innerHTML = `
    <div class="steps-expander">
      <button class="steps-header" onclick="this.parentElement.classList.toggle('collapsed')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
        <span class="steps-label">Research (${steps.length} steps)</span>
        <svg class="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M18 15l-6-6-6 6"/></svg>
      </button>
      <div class="steps-list">
        ${steps.map((s, i) => `
          <div class="step-item">
            <span class="step-dot ${i === 0 ? 'active' : ''}"></span>
            ${s}
          </div>
        `).join('')}
      </div>
    </div>`;
  chatFeed.appendChild(el);
  scrollChat();
  return el;
}

function scrollChat() {
  chatFeed.scrollTop = chatFeed.scrollHeight;
}

// ── Chat input handling ──────────────────────────────────────────────────────
chatInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleChatSend();
  }
});
chatSend.addEventListener('click', handleChatSend);

function handleChatSend() {
  const q = chatInput.value.trim();
  if (!q) return;
  addMessage('user', q);
  chatInput.value = '';

  // Fake AI response after delay
  const dotsEl = addTypingDots();
  setTimeout(() => {
    dotsEl.remove();
    addMessage('assistant', '<p>I\'ll look into that for you. Searching for the best options now...</p>');
  }, 1500);
}

// ── Tab switching ────────────────────────────────────────────────────────────
tabBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    tabBtns.forEach(b => b.classList.remove('active'));
    tabPanels.forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.querySelector(`[data-panel="${btn.dataset.tab}"]`).classList.add('active');
  });
});

// ── Render cards ─────────────────────────────────────────────────────────────
function renderFlights() {
  const panel = document.getElementById('flightsPanel');
  panel.innerHTML = MOCK_FLIGHTS.map(f => `
    <div class="card card-flight">
      <div class="card-row">
        <div class="airline-logo">${f.code}</div>
        <div class="card-col" style="flex:1">
          <div class="card-title">
            <span class="font-mono">${f.depTime}</span> ${f.dep}
            <span class="route-arrow">&rarr;</span>
            <span class="font-mono">${f.arrTime}</span> ${f.arr}
          </div>
          <div class="card-meta">${f.airline} &middot; ${f.flight} &middot; ${f.duration} &middot; ${f.class}</div>
        </div>
        <div class="card-right">
          <span class="card-price">&#8377;${f.price}</span>
          <button class="card-action">Select</button>
        </div>
      </div>
    </div>
  `).join('');
}

function renderHotels() {
  const panel = document.getElementById('hotelsPanel');
  panel.innerHTML = MOCK_HOTELS.map(h => `
    <div class="card card-hotel">
      <div class="card-row">
        <div class="hotel-thumb">
          ${h.thumb ? `<img src="${h.thumb}" alt="${h.name}">` : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 22V4a2 2 0 012-2h8a2 2 0 012 2v18z"/></svg>`}
        </div>
        <div class="card-col" style="flex:1;gap:0.25rem">
          <div class="card-title">${h.name}</div>
          <div style="display:flex;align-items:center;gap:0.5rem">
            <div class="stars">
              ${'<svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>'.repeat(Math.min(h.stars, 5))}
            </div>
            <span class="star-num">${h.rating}</span>
            <span style="color:var(--text-secondary);font-size:0.75rem" class="font-mono">(${h.reviews})</span>
          </div>
          <div class="card-meta">${h.address}</div>
        </div>
        <div class="card-right">
          <div><span class="card-price">&#8377;${h.price}</span><span class="card-price-sub">/night</span></div>
          <button class="card-action">Details</button>
        </div>
      </div>
    </div>
  `).join('');
}

function renderPlaces() {
  const panel = document.getElementById('placesPanel');
  panel.innerHTML = MOCK_PLACES.map(p => `
    <div class="card card-place" style="padding:0;overflow:hidden">
      <div class="card-row" style="gap:0">
        <div class="place-thumb" style="margin:0;width:80px;border-radius:0">
          ${p.thumb ? `<img src="${p.thumb}" alt="${p.name}">` : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>`}
        </div>
        <div class="card-col" style="flex:1;padding:0.875rem 1rem;gap:0.2rem">
          <div style="display:flex;align-items:center;justify-content:space-between;gap:0.5rem">
            <span class="card-title">${p.name}</span>
            <span class="type-badge">${p.type}</span>
          </div>
          <div style="display:flex;align-items:center;gap:0.375rem">
            <svg viewBox="0 0 24 24" fill="var(--sem-rating)" stroke="none" style="width:13px;height:13px"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
            <span class="font-mono" style="font-size:0.8125rem;color:var(--text-body)">${p.rating}</span>
          </div>
          <p class="line-clamp-2" style="font-size:0.75rem;color:var(--text-secondary);margin:0">${p.desc}</p>
        </div>
      </div>
    </div>
  `).join('');
}

// ── Helpers ──────────────────────────────────────────────────────────────────
function escapeHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function delay(ms) {
  return new Promise(r => setTimeout(r, ms));
}
