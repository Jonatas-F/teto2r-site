/* ============================================================
   TETO — interações e conteúdo dinâmico
   ============================================================ */

// Paletas de "foto" (gradientes placeholder até entrarem as fotos reais)
const palettes = [
  'linear-gradient(135deg,#3a5a40,#588157)',
  'linear-gradient(135deg,#344e41,#3a5a40)',
  'linear-gradient(135deg,#6b9668,#4f7a4d)',
  'linear-gradient(135deg,#2f5137,#588157)',
  'linear-gradient(135deg,#8ab66b,#4f7a4d)',
  'linear-gradient(135deg,#243f2c,#4f7a4d)',
  'linear-gradient(135deg,#55713f,#8ab66b)',
  'linear-gradient(135deg,#1b2e20,#3a5a40)'
];

/* ---------- Projetos ---------- */
const projects = [
  { title: 'Casa T+J', place: 'Porto Real', tags: ['arquitetura', 'paisagismo'], labels: ['Arquitetura', 'Paisagismo'] },
  { title: 'Casa Prada', place: '', tags: ['arquitetura'], labels: ['Arquitetura Sustentável'] },
  { title: 'Casa J.E.', place: 'Itapema', tags: ['arquitetura', 'construcao'], labels: ['Arquitetura', 'Construção'] },
  { title: 'Casa Bela Vista', place: 'A+G', tags: ['arquitetura', 'paisagismo'], labels: ['Arquitetura', 'Paisagismo'] },
  { title: 'Reforma do Escritório', place: '', tags: ['reforma'], labels: ['Reforma'] },
  { title: 'Casa A+E', place: '', tags: ['construcao', 'arquitetura'], labels: ['Construção'] },
  { title: 'Projeto MCMV', place: '', tags: ['arquitetura', 'construcao'], labels: ['Arquitetura', 'Construção'] },
  { title: 'Casa A+M', place: '', tags: ['paisagismo', 'arquitetura'], labels: ['Paisagismo'] }
];

const blog = [
  { title: 'Casa A+E', text: 'Acompanhamento da obra e das escolhas de materiais ecológicos ao longo da execução.' },
  { title: 'Casa MCMV', text: 'Habitação de interesse social com foco em conforto térmico e baixo custo de manutenção.' },
  { title: 'Casa Alphaville', text: 'Projeto em wood-frame em Piracicaba: estrutura de madeira, rápida e sustentável.' },
  { title: 'Casa T+J — Porto Real', text: 'Quinta etapa da obra: integração do paisagismo com a arquitetura da residência.' }
];

const testimonials = [
  { name: 'Estefânia Buzolin', role: 'Cliente residencial', text: 'A casa trouxe uma calma que eu não sabia que precisava. Cada ambiente respira natureza.' },
  { name: 'Jean François Hardouin', role: 'Diretor · Enza Zaden Brasil', text: 'Profissionalismo e sensibilidade ambiental em cada detalhe do projeto corporativo.' },
  { name: 'Dra. Adriana Sato', role: 'Cliente residencial', text: 'É como ter uma casa de férias dentro da cidade. O bem-estar é diário.' },
  { name: 'Itaraju e Sueli', role: 'Clientes residenciais', text: 'Nossa conexão com a natureza ficou parte da rotina. Projeto que mudou nossa vida.' },
  { name: 'Eng. Alex Aguilera', role: 'Parceiro técnico', text: 'Rigor técnico somado a uma visão sustentável rara no mercado. Recomendo sem hesitar.' }
];

const services = {
  projetos:    { h: 'Projetos Residenciais e Comerciais', p: 'Projeto modular e otimizado para reduzir desperdício de material, com tijolo ecológico, blocos cerâmicos estruturais ou de concreto, aço e madeira.' },
  consultoria: { h: 'Consultoria, Palestras e Workshops', p: 'Palestras e oficinas em eventos sobre meio ambiente, arquitetura sustentável e paisagismo, levando conhecimento prático a clientes e profissionais.' },
  reforma:     { h: 'Reformas Sustentáveis', p: 'Readequação de espaços existentes com soluções de eficiência, reaproveitamento de materiais e melhoria do conforto ambiental.' },
  construcao:  { h: 'Direção de Obra e Acompanhamento', p: 'Visitas regulares ao canteiro para orientar equipes e fornecedores, garantindo fidelidade ao projeto e qualidade da execução.' },
  energia:     { h: 'Energia e Infraestrutura Verde', p: 'Placas solares, cisternas de captação de água da chuva e tratamento de esgoto doméstico por plantas (zona de raízes).' },
  mobiliario:  { h: 'Mobiliário Sob Medida', p: 'Peças exclusivas com madeira de reflorestamento, demolição, ferro e outros materiais reaproveitados.' }
};

/* ---------- Render ---------- */
function mediaStyle(i) { return `style="background:${palettes[i % palettes.length]}"`; }

function renderProjects() {
  const grid = document.getElementById('projectsGrid');
  grid.innerHTML = projects.map((p, i) => `
    <article class="card" data-cats="${p.tags.join(' ')}">
      <div class="card__media" ${mediaStyle(i)}>
        <div class="card__tags">${p.labels.map(l => `<span class="card__tag">${l}</span>`).join('')}</div>
      </div>
      <div class="card__body">
        <h3 class="card__title">${p.title}${p.place ? ' · ' + p.place : ''}</h3>
        <a href="#contato" class="card__link">Ver projeto →</a>
      </div>
    </article>`).join('');
}

function renderBlog() {
  const grid = document.getElementById('blogGrid');
  grid.innerHTML = blog.map((b, i) => `
    <article class="card">
      <div class="card__media" ${mediaStyle(i + 2)}></div>
      <div class="card__body">
        <h3 class="card__title">${b.title}</h3>
        <p class="card__text">${b.text}</p>
        <a href="#obras" class="card__link">Ler mais →</a>
      </div>
    </article>`).join('');
}

function renderTestimonials() {
  const grid = document.getElementById('testimonialsGrid');
  grid.innerHTML = testimonials.map((t, i) => {
    const initials = t.name.split(' ').slice(0, 2).map(n => n[0]).join('');
    return `
    <article class="testimonial">
      <div class="testimonial__head">
        <div class="testimonial__avatar" style="background:${palettes[i % palettes.length]}">${initials}</div>
        <div>
          <div class="testimonial__name">${t.name}</div>
          <div class="testimonial__role">${t.role}</div>
        </div>
      </div>
      <p class="testimonial__text">“${t.text}”</p>
    </article>`;
  }).join('');
}

function renderServices() {
  const panels = document.getElementById('svcPanels');
  panels.innerHTML = Object.entries(services).map(([key, s], i) => `
    <div class="svc-panel ${i === 0 ? 'is-active' : ''}" data-panel="${key}">
      <h3>${s.h}</h3>
      <p>${s.p}</p>
    </div>`).join('');
}

/* ---------- Interactions ---------- */
function initFilters() {
  const btns = document.querySelectorAll('.filter');
  btns.forEach(btn => btn.addEventListener('click', () => {
    btns.forEach(b => b.classList.remove('is-active'));
    btn.classList.add('is-active');
    const f = btn.dataset.filter;
    document.querySelectorAll('#projectsGrid .card').forEach(card => {
      const show = f === 'all' || card.dataset.cats.includes(f);
      card.classList.toggle('is-hidden', !show);
    });
  }));
}

function initServiceTabs() {
  const tabs = document.querySelectorAll('.svc-tab');
  tabs.forEach(tab => tab.addEventListener('click', () => {
    tabs.forEach(t => t.classList.remove('is-active'));
    tab.classList.add('is-active');
    const key = tab.dataset.tab;
    document.querySelectorAll('.svc-panel').forEach(p => {
      p.classList.toggle('is-active', p.dataset.panel === key);
    });
  }));
}

function initNav() {
  const toggle = document.getElementById('navToggle');
  const nav = document.getElementById('nav');
  toggle.addEventListener('click', () => nav.classList.toggle('is-open'));
  nav.querySelectorAll('a').forEach(a => a.addEventListener('click', () => nav.classList.remove('is-open')));
}

function initForm() {
  const form = document.getElementById('contactForm');
  const status = document.getElementById('formStatus');
  form.addEventListener('submit', e => {
    e.preventDefault();
    if (!form.checkValidity()) {
      status.textContent = 'Preencha os campos obrigatórios.';
      status.style.color = '#e0a66b';
      return;
    }
    status.textContent = 'Mensagem enviada! Em breve entraremos em contato. (demo — sem backend)';
    status.style.color = 'var(--accent)';
    form.reset();
  });
}

/* ---------- Boot ---------- */
document.addEventListener('DOMContentLoaded', () => {
  renderProjects();
  renderBlog();
  renderTestimonials();
  renderServices();
  initFilters();
  initServiceTabs();
  initNav();
  initForm();
  document.getElementById('year').textContent = new Date().getFullYear();
});
