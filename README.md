# TETO — Site (Remake)

Remake do site **[teto2r.com](https://teto2r.com)** — TETO Arquitetura Sustentável & Paisagismo, escritório de Limeira (SP) coordenado pelo arquiteto e urbanista Paulo Trigo.

Reconstrução em **HTML, CSS e JavaScript puros** (sem dependências/build), com layout responsivo e identidade visual de arquitetura sustentável (paleta verde/natureza).

## Estrutura

```
teto2r-site/
├── index.html        # página única (one-page)
├── css/style.css     # estilos e responsividade
├── js/main.js        # conteúdo dinâmico + interações
└── assets/           # imagens (adicionar fotos reais aqui)
```

## Seções

- **Hero** — "A Arquitetura da Felicidade" + CTAs
- **Quem Somos** — bio do Paulo Trigo e missão
- **Portfólio** — grade de projetos com filtros por categoria
- **De Olho nas Obras** — cards estilo blog
- **Serviços** — abas (Projetos, Consultoria, Reforma, Construção, Energia, Mobiliário)
- **Diferenciais** — 4 blocos
- **Depoimentos** — clientes e parceiros
- **Contato** — dados + formulário (demo, sem backend)

## Como rodar

Basta abrir o `index.html` no navegador — não há build.
Para servir localmente:

```bash
python -m http.server 8000
```

## Próximos passos

- [ ] Substituir os gradientes placeholder por **fotos reais** dos projetos (pasta `assets/`)
- [ ] Ligar o formulário de contato a um backend/serviço de e-mail
- [ ] Revisar textos, telefones e endereço com os dados oficiais da TETO
- [ ] Adicionar favicon e metatags Open Graph

## Observação

Conteúdo textual baseado no site original; dados de contato (telefones, e-mail) são **placeholders** e devem ser confirmados antes de publicar.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
