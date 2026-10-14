(() => {
  'use strict';
  const pages = Array.isArray(window.LEVTECH_CATALOGUE_PAGES) ? window.LEVTECH_CATALOGUE_PAGES : [];
  const byId = id => document.getElementById(id);
  const nav = byId('thumbNav');
  const pageImage = byId('pageImage');
  const title = byId('pageTitle');
  const section = byId('pageSection');
  const currentPage = byId('currentPage');
  const totalPages = byId('totalPages');
  const currentTitle = byId('currentTitle');
  const progressFill = byId('progressFill');
  const pageSearch = byId('pageSearch');
  const loading = byId('imageLoader');
  let index = 0;
  let touchStartX = null;
  const zoomLevels = [1, 1.25, 1.5];
  let zoomIndex = 0;
  const zoomBtn = byId('zoomBtn');
  const stage = byId('stage');
  const zoomLabel = () => {
    if (zoomBtn) zoomBtn.innerHTML = `${zoomIndex === 0 ? '＋' : zoomIndex === 1 ? '⌕' : '−'} <span>${zoomIndex === 0 ? 'Zoom page' : `Zoom ${Math.round(zoomLevels[zoomIndex] * 100)}%`}</span>`;
  };
  const setZoom = next => {
    zoomIndex = Math.max(0, Math.min(zoomLevels.length - 1, next));
    if (stage) stage.classList.toggle('is-zoomed', zoomIndex > 0);
    if (pageImage && stage) {
      pageImage.style.width = zoomIndex === 0 ? '' : `${zoomLevels[zoomIndex] * 100}%`;
      pageImage.style.maxHeight = zoomIndex === 0 ? '' : 'none';
      pageImage.style.maxWidth = zoomIndex === 0 ? '' : 'none';
    }
    zoomLabel();
  };

  const safeText = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const renderNav = (filter = '') => {
    if (!nav) return;
    const q = filter.trim().toLowerCase();
    const visible = pages.map((p, i) => ({p, i})).filter(({p}) => `${p.title} ${p.description} ${p.num}`.toLowerCase().includes(q));
    nav.innerHTML = visible.map(({p, i}) => `
      <button type="button" class="thumb${i === index ? ' active' : ''}" data-index="${i}" aria-current="${i === index ? 'page' : 'false'}">
        <img src="pages/${safeText(p.filename)}" alt="" loading="lazy">
        <span class="thumbmeta"><span class="n">PAGE ${String(p.num).padStart(2,'0')}</span><span class="t">${safeText(p.title)}</span></span>
      </button>`).join('');
    nav.querySelectorAll('.thumb').forEach(btn => btn.addEventListener('click', () => go(Number(btn.dataset.index))));
  };
  const updateControls = () => {
    const p = pages[index];
    if (!p) return;
    title.textContent = p.title;
    section.textContent = `CATALOGUE / PAGE ${String(p.num).padStart(2,'0')}`;
    currentPage.textContent = String(p.num).padStart(2,'0');
    totalPages.textContent = String(pages.length).padStart(2,'0');
    currentTitle.textContent = p.title;
    progressFill.style.width = `${((index + 1) / pages.length) * 100}%`;
    byId('prevBtn').disabled = byId('prevTop').disabled = index === 0;
    byId('nextBtn').disabled = byId('nextTop').disabled = index === pages.length - 1;
    document.querySelectorAll('.thumb').forEach(btn => {
      const active = Number(btn.dataset.index) === index;
      btn.classList.toggle('active', active);
      btn.setAttribute('aria-current', active ? 'page' : 'false');
      if (active) btn.scrollIntoView({block:'nearest', behavior:'smooth'});
    });
    try { history.replaceState(null, '', `#page-${String(p.num).padStart(2,'0')}`); } catch (_) { /* file:// previews may restrict history updates */ }
  };
  const go = nextIndex => {
    if (!pages.length) return;
    index = Math.max(0, Math.min(pages.length - 1, nextIndex));
    const p = pages[index];
    pageImage.classList.add('changing');
    loading.hidden = false;
    const candidate = new Image();
    candidate.onload = () => {
      pageImage.src = candidate.src;
      pageImage.alt = `Page ${String(p.num).padStart(2,'0')}: ${p.title}`;
      setZoom(0);
      pageImage.classList.remove('changing');
      loading.hidden = true;
      updateControls();
    };
    candidate.onerror = () => {
      loading.textContent = 'This page image could not be opened. Check the pages folder.';
      pageImage.classList.remove('changing');
      loading.hidden = false;
      updateControls();
    };
    candidate.src = `pages/${p.filename}`;
  };
  const back = () => go(index - 1);
  const forward = () => go(index + 1);
  byId('prevBtn').addEventListener('click', back);
  byId('prevTop').addEventListener('click', back);
  byId('nextBtn').addEventListener('click', forward);
  byId('nextTop').addEventListener('click', forward);
  pageSearch.addEventListener('input', () => renderNav(pageSearch.value));
  if (zoomBtn) zoomBtn.addEventListener('click', () => setZoom(zoomIndex >= zoomLevels.length - 1 ? 0 : zoomIndex + 1));
  if (pageImage) pageImage.addEventListener('click', () => setZoom(zoomIndex === 0 ? 1 : 0));
  if (byId('fullBtn')) byId('fullBtn').addEventListener('click', async () => {
    try {
      if (!document.fullscreenElement) await stage.requestFullscreen();
      else await document.exitFullscreen();
    } catch (_) { /* fullscreen may be disabled by a host browser */ }
  });
  byId('themeToggle').addEventListener('click', () => {
    const next = document.body.dataset.theme === 'dark' ? 'light' : 'dark';
    document.body.dataset.theme = next;
    try { localStorage.setItem('levtech-catalogue-theme', next); } catch (_) {}
  });
  try {
    const savedTheme = localStorage.getItem('levtech-catalogue-theme');
    if (savedTheme === 'dark' || savedTheme === 'light') document.body.dataset.theme = savedTheme;
  } catch (_) {}
  document.addEventListener('keydown', e => {
    if (e.altKey || e.ctrlKey || e.metaKey || ['INPUT','TEXTAREA'].includes(document.activeElement?.tagName)) return;
    if (e.key === 'ArrowLeft') back();
    if (e.key === 'ArrowRight') forward();
    if (e.key === '+' || e.key === '=') { setZoom(zoomIndex + 1); e.preventDefault(); }
    if (e.key === '-' || e.key === '_') { setZoom(zoomIndex - 1); e.preventDefault(); }
    if (e.key.toLowerCase() === 'f' && stage && stage.requestFullscreen) { stage.requestFullscreen().catch(() => {}); }
    if (e.key === 'Home') go(0);
    if (e.key === 'End') go(pages.length - 1);
  });
  stage.addEventListener('touchstart', e => { touchStartX = e.changedTouches[0].screenX; }, {passive:true});
  stage.addEventListener('touchend', e => {
    if (touchStartX === null) return;
    const delta = e.changedTouches[0].screenX - touchStartX;
    if (Math.abs(delta) > 55) delta < 0 ? forward() : back();
    touchStartX = null;
  }, {passive:true});
  if (pages.length) {
    byId('sideCount').textContent = `${pages.length} pages`;
    renderNav();
    const target = location.hash.match(/page-(\d+)/i);
    if (target) {
      const pnum = Number(target[1]);
      const found = pages.findIndex(p => p.num === pnum);
      if (found >= 0) index = found;
    }
    go(index);
  } else {
    title.textContent = 'Catalogue data not found';
    section.textContent = 'SOURCE PACKAGE CHECK';
    loading.textContent = 'catalogue_manifest.js is missing or invalid.';
    loading.hidden = false;
  }
})();
