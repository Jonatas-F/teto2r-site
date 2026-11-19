"""Empacota uma página HTML do projeto em um único arquivo independente.

Embute CSS, JS, imagens (img, srcset, favicon, url() do CSS), SVGs e as fontes do
Google Fonts (baixadas uma vez e guardadas em tools/.fontcache). O resultado abre
direto no navegador, sem servidor e sem internet.

Uso (da raiz do repositório):
  python -I tools/bundle.py index.html dist/teto-site.html
  python -I tools/bundle.py brand/index.html dist/teto-brandbook.html
"""
import base64, hashlib, mimetypes, os, re, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "tools", ".fontcache")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0 Safari/537.36"
MIME = {".webp": "image/webp", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".svg": "image/svg+xml", ".woff2": "font/woff2", ".woff": "font/woff", ".ttf": "font/ttf"}


def data_uri(path):
    ext = os.path.splitext(path)[1].lower()
    raw = open(path, "rb").read()
    return f"data:{MIME.get(ext, mimetypes.guess_type(path)[0] or 'application/octet-stream')};base64," + base64.b64encode(raw).decode()


def fetch(url):
    os.makedirs(CACHE, exist_ok=True)
    f = os.path.join(CACHE, hashlib.sha1(url.encode()).hexdigest())
    if not os.path.exists(f):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        open(f, "wb").write(urllib.request.urlopen(req, timeout=60).read())
    return open(f, "rb").read()


def local(base_dir, ref):
    if re.match(r"^(data:|https?:|mailto:|tel:|#)", ref):
        return None
    p = os.path.normpath(os.path.join(base_dir, ref.split("#")[0].split("?")[0]))
    return p if os.path.isfile(p) else None


def inline_css(css, css_dir):
    def rep(m):
        ref = m.group(2)
        p = local(css_dir, ref)
        return f'url("{data_uri(p)}")' if p else m.group(0)
    return re.sub(r"""url\((['"]?)([^'")]+)\1\)""", rep, css)


def google_fonts(href):
    css = fetch(href).decode("utf-8")
    def rep(m):
        raw = fetch(m.group(1))
        return f'url("data:font/woff2;base64,{base64.b64encode(raw).decode()}")'
    return re.sub(r"url\((https://fonts\.gstatic\.com/[^)]+)\)", rep, css)


def bundle(src, dst):
    base_dir = os.path.dirname(os.path.abspath(src))
    html = open(src, encoding="utf-8").read()

    # preconnect e preload de imagem não servem mais
    html = re.sub(r'\s*<link rel="preconnect"[^>]*>', "", html)
    html = re.sub(r'\s*<link rel="preload" as="image"[^>]*>', "", html)

    # folhas de estilo locais e do Google Fonts
    def css_link(m):
        tag = m.group(0)
        href = re.search(r'href="([^"]+)"', tag).group(1)
        if href.startswith("https://fonts.googleapis.com"):
            return f"<style>\n{google_fonts(href.replace('&amp;', '&'))}\n</style>"
        p = local(base_dir, href)
        if not p:
            return tag
        return f"<style>\n{inline_css(open(p, encoding='utf-8').read(), os.path.dirname(p))}\n</style>"
    html = re.sub(r'<link[^>]+rel="stylesheet"[^>]*>', css_link, html)

    # favicons
    def icon(m):
        tag = m.group(0)
        href = re.search(r'href="([^"]+)"', tag).group(1)
        p = local(base_dir, href)
        return tag.replace(href, data_uri(p)) if p else tag
    html = re.sub(r'<link[^>]+rel="icon"[^>]*>', icon, html)

    # scripts
    def script(m):
        p = local(base_dir, m.group(1))
        if not p:
            return m.group(0)
        return "<script>\n" + open(p, encoding="utf-8").read().replace("</script", "<\\/script") + "\n</script>"
    html = re.sub(r'<script src="([^"]+)"[^>]*></script>', script, html)

    # imagens: srcset/sizes saem (uma fonte só), src vira data URI
    html = re.sub(r'\s(srcset|imagesrcset|sizes|imagesizes)="[^"]*"', "", html)
    def img_src(m):
        p = local(base_dir, m.group(2))
        return f'{m.group(1)}"{data_uri(p)}"' if p else m.group(0)
    html = re.sub(r'(<(?:img|source|image|use)[^>]*?\s(?:src|href)=)"([^"]+)"', img_src, html)

    # estilos inline e <style> do próprio HTML com url()
    html = re.sub(r"<style>(.*?)</style>", lambda m: "<style>" + inline_css(m.group(1), base_dir) + "</style>", html, flags=re.S)
    html = re.sub(r'style="([^"]*url\([^"]*)"', lambda m: 'style="' + inline_css(m.group(1), base_dir).replace('"', "'") + '"', html)

    # o que sobrar apontando para arquivo local vira aviso
    leftovers = [r for r in re.findall(r'(?:src|href)="([^"#][^"]*)"', html) if local(base_dir, r)]
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    open(dst, "w", encoding="utf-8").write(html)
    print(f"{dst}: {os.path.getsize(dst) / 1024 / 1024:.2f} MB; referências locais restantes: {leftovers[:10]}")


if __name__ == "__main__":
    bundle(sys.argv[1], sys.argv[2])
