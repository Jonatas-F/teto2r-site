# TETO · Site v2

Reformulação do site **[teto2r.com](https://teto2r.com)**: TETO Arquitetura Sustentável & Paisagismo, escritório de Limeira (SP) coordenado pelo arquiteto e urbanista Paulo Trigo.

HTML, CSS e JavaScript puros, sem build e sem dependências. Fotos reais dos projetos em WebP.

## Rodar local

```bash
python -m http.server 5180 --bind 127.0.0.1
```

- Site: http://127.0.0.1:5180/
- Avaliação UX/UI e identidade: http://127.0.0.1:5180/identidade.html

## Identidade

| Token | Cor | Uso |
|---|---|---|
| Grama | `#3B7A2A` | Botões, links (4,6:1 no Cal) |
| Grama profundo | `#23501A` | Fundo de serviços |
| Telha | `#B04E28` | Destaques, contato (4,7:1 no Cal) |
| Ferro | `#171716` | Títulos, vigas, seções escuras |
| Cal | `#F5F0E6` | Fundo principal |
| Broto | `#8DC63F` | Verde do logo, **só sobre fundo escuro** |

Tipografia: Archivo (variável, títulos semicondensados) + Instrument Serif itálico (palavras de emoção).

## Estrutura

```
index.html        página única
identidade.html   avaliação do site atual + decisões de design
css/style.css     tokens, layout, animações guiadas pela rolagem
js/main.js        hero, menu, filtro, carrossel, formulário → WhatsApp, fallbacks
assets/img/       WebP 960/1920 + logos (originais em assets/img/src/, fora do git)
```

## Pendências

- [ ] Fotos em alta da Casa A+M, Reforma do escritório e Casa Alphaville (só existem em 600 px)
- [ ] Confirmar telefones, e-mail e endereço com o escritório
- [ ] Decidir se Cursos e Blog voltam ao menu
- [ ] Páginas individuais de projeto com galeria
- [ ] Versão do símbolo do logo em Grama para fundo claro
