/* ==========================================================================
   TETO v2 · interações
   ========================================================================== */
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
const supportsSDA = CSS.supports('(animation-timeline: view()) and (animation-range: entry)');

/* ---------- Header: muda de transparente para sólido ao sair do hero ---------- */
function initHeader() {
  const header = document.querySelector('.site-header');
  const hero = document.querySelector('.hero');
  if (!header || !hero) return;
  let ticking = false;
  const update = () => {
    // fica sólido quando o leitor já rolou um terço do hero (antes do texto passar por baixo do logo)
    header.classList.toggle('is-scrolled', scrollY > hero.offsetHeight * 0.33);
    ticking = false;
  };
  addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
  addEventListener('resize', update);
  update();
}

/* ---------- Menu mobile ---------- */
function initMenu() {
  const toggle = document.getElementById('menuToggle');
  const nav = document.getElementById('nav');
  if (!toggle || !nav) return;
  const setOpen = (open) => {
    toggle.setAttribute('aria-expanded', String(open));
    nav.classList.toggle('is-open', open);
    document.body.style.overflow = open ? 'hidden' : '';
  };
  toggle.addEventListener('click', () => setOpen(toggle.getAttribute('aria-expanded') !== 'true'));
  nav.addEventListener('click', (e) => { if (e.target.closest('a')) setOpen(false); });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && nav.classList.contains('is-open')) { setOpen(false); toggle.focus(); }
  });
}

/* ---------- Hero: troca de projetos com Ken Burns ---------- */
function initHero() {
  const hero = document.querySelector('.hero');
  const slides = [...document.querySelectorAll('.hero__slide')];
  const bars = [...document.querySelectorAll('.hero__progress i')];
  const name = document.getElementById('slideName');
  const pauseBtn = document.getElementById('heroPause');
  if (!hero || slides.length < 2) return;

  const DURATION = 6500;
  hero.style.setProperty('--slide-ms', `${DURATION}ms`);
  let index = 0;
  let timer = null;
  let paused = reduceMotion;

  const show = (i) => {
    index = (i + slides.length) % slides.length;
    slides.forEach((s, n) => s.classList.toggle('is-active', n === index));
    bars.forEach((b, n) => {
      b.classList.toggle('is-done', n < index);
      b.classList.remove('is-active');
    });
    // reinicia a animação da barra atual
    void bars[index]?.offsetWidth;
    bars[index]?.classList.add('is-active');
    name.textContent = slides[index].dataset.caption;
  };

  const schedule = () => {
    clearTimeout(timer);
    if (!paused) timer = setTimeout(() => { show(index + 1); schedule(); }, DURATION);
  };

  const setPaused = (p) => {
    paused = p;
    hero.classList.toggle('is-paused', p);
    pauseBtn.setAttribute('aria-pressed', String(p));
    pauseBtn.querySelector('.sr-only').textContent = p ? 'Retomar troca de imagens' : 'Pausar troca de imagens';
    schedule();
  };

  pauseBtn.addEventListener('click', () => setPaused(!paused));
  // não gasta CPU com o hero fora da tela
  new IntersectionObserver(([e]) => {
    if (!e.isIntersecting) clearTimeout(timer);
    else schedule();
  }).observe(hero);
  document.addEventListener('visibilitychange', () => (document.hidden ? clearTimeout(timer) : schedule()));

  show(0);
  setPaused(paused);
}

/* ---------- Manifesto: quebra em palavras para acender na rolagem ---------- */
function initWords() {
  document.querySelectorAll('[data-words]').forEach((el) => {
    const words = el.textContent.trim().split(/\s+/);
    el.innerHTML = words.map((w, i) => `<span class="w" style="--i:${i}">${w}</span>`).join(' ');
    el.setAttribute('aria-label', words.join(' '));
  });
}

/* ---------- Linha do tempo: índice para a sequência de entrada ---------- */
function initTimeline() {
  document.querySelectorAll('.timeline li').forEach((li, i) => li.style.setProperty('--n', i));
}

/* ---------- Carrossel de depoimentos ---------- */
function initQuotes() {
  const track = document.getElementById('quotes');
  if (!track) return;
  const pauseBtn = document.getElementById('quotesPause');
  const originals = [...track.children];
  const n = originals.length;
  if (n < 2) return;

  // Loop infinito: uma cópia dos depoimentos no fim, fora da leitura e do foco.
  originals.forEach((li) => {
    const clone = li.cloneNode(true);
    clone.setAttribute('aria-hidden', 'true');
    clone.inert = true;
    clone.classList.add('is-clone');
    track.append(clone);
  });

  const step = () => {
    const card = track.querySelector('.quote');
    const gap = parseFloat(getComputedStyle(track).columnGap) || 20;
    return card ? card.getBoundingClientRect().width + gap : 400;
  };
  const setWidth = () => step() * n;
  const smooth = reduceMotion ? 'auto' : 'smooth';

  // Ao passar do último original para as cópias, volta em silêncio para a posição equivalente.
  const normalize = () => {
    const w = setWidth();
    if (track.scrollLeft >= w - 2) track.scrollTo({ left: track.scrollLeft - w, behavior: 'instant' });
  };
  let settle;
  const onSettled = () => { clearTimeout(settle); settle = setTimeout(normalize, 80); };
  track.addEventListener('scrollend', onSettled);
  track.addEventListener('scroll', () => { clearTimeout(settle); settle = setTimeout(normalize, 220); }, { passive: true });

  const go = (dir) => {
    if (dir < 0 && track.scrollLeft < step() / 2) {
      track.scrollTo({ left: track.scrollLeft + setWidth(), behavior: 'instant' });
    }
    track.scrollBy({ left: step() * dir, behavior: smooth });
  };

  document.querySelectorAll('.carousel-nav .round-btn[data-dir]').forEach((btn) => {
    btn.addEventListener('click', () => { go(Number(btn.dataset.dir)); restart(); });
  });

  // Rodagem automática: 5 s por depoimento, com pausa manual e pausas automáticas.
  const DELAY = 5000;
  let timer = null;
  let userPaused = reduceMotion;
  let hover = false;
  let visible = false;
  const running = () => !userPaused && !hover && visible && !document.hidden;
  const restart = () => {
    clearInterval(timer);
    if (running()) timer = setInterval(() => go(1), DELAY);
  };
  const setPaused = (p) => {
    userPaused = p;
    if (pauseBtn) {
      pauseBtn.setAttribute('aria-pressed', String(p));
      pauseBtn.setAttribute('aria-label', p ? 'Retomar depoimentos' : 'Pausar depoimentos');
    }
    restart();
  };
  pauseBtn?.addEventListener('click', () => setPaused(!userPaused));
  const holdOn = () => { hover = true; restart(); };
  const holdOff = () => { hover = false; restart(); };
  track.addEventListener('pointerenter', holdOn);
  track.addEventListener('pointerleave', holdOff);
  track.addEventListener('focusin', holdOn);
  track.addEventListener('focusout', holdOff);
  track.addEventListener('touchstart', holdOn, { passive: true });
  track.addEventListener('touchend', () => setTimeout(holdOff, 3000), { passive: true });
  new IntersectionObserver(([e]) => { visible = e.isIntersecting; restart(); }, { threshold: 0.3 }).observe(track);
  document.addEventListener('visibilitychange', restart);
  setPaused(userPaused);
}

/* ---------- Formulário: monta a mensagem e abre o WhatsApp ---------- */
function initForm() {
  const form = document.getElementById('contactForm');
  const status = document.getElementById('formStatus');
  if (!form) return;
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    if (!form.checkValidity()) {
      status.textContent = 'Preencha nome e mensagem para continuar.';
      status.classList.add('is-error');
      form.querySelector(':invalid')?.focus();
      return;
    }
    const d = new FormData(form);
    const text = [
      `Olá, Paulo! Meu nome é ${d.get('nome')}.`,
      `Tipo de projeto: ${d.get('tipo')}.`,
      d.get('telefone') ? `Meu WhatsApp: ${d.get('telefone')}.` : '',
      '',
      d.get('mensagem'),
    ].filter((l, i) => l || i === 3).join('\n');
    status.classList.remove('is-error');
    status.textContent = 'Abrindo o WhatsApp com a sua mensagem...';
    window.open(`https://wa.me/5519988082306?text=${encodeURIComponent(text)}`, '_blank', 'noopener');
  });
}

/* ---------- Nav ativa conforme a seção visível ---------- */
function initActiveNav() {
  const links = [...document.querySelectorAll('.nav__list a')];
  const map = new Map(links.map((a) => [a.getAttribute('href').slice(1), a]));
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      const link = map.get(e.target.id);
      if (link && e.isIntersecting) {
        links.forEach((l) => l.removeAttribute('aria-current'));
        link.setAttribute('aria-current', 'true');
      }
    });
  }, { rootMargin: '-45% 0px -50% 0px' });
  map.forEach((_, id) => { const s = document.getElementById(id); if (s) io.observe(s); });
}

/* ---------- Fallbacks para navegadores sem scroll-driven animations ---------- */
function initFallbacks() {
  if (supportsSDA || reduceMotion) return;

  // revelações
  document.documentElement.classList.add('js-reveal');
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); } });
  }, { rootMargin: '0px 0px -10% 0px' });
  document.querySelectorAll('.reveal').forEach((el) => io.observe(el));

  // parallax das faixas e do hero
  const layers = [...document.querySelectorAll('.parallax')];
  const heroMedia = document.querySelector('.hero__media');
  let ticking = false;
  const update = () => {
    const vh = innerHeight;
    layers.forEach((layer) => {
      const r = layer.closest('section').getBoundingClientRect();
      if (r.bottom < 0 || r.top > vh) return;
      const p = (vh - r.top) / (vh + r.height); // 0 → 1
      layer.style.transform = `translateY(${(-10 + p * 20).toFixed(2)}%)`;
    });
    if (heroMedia && scrollY < vh) heroMedia.style.transform = `translateY(${(scrollY / vh) * 28}%)`;
    ticking = false;
  };
  addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
  update();
}

/* ---------- Boot ---------- */
initWords();
initHeader();
initMenu();
initHero();
initTimeline();
initQuotes();
initForm();
initActiveNav();
initFallbacks();
document.getElementById('year').textContent = new Date().getFullYear();
