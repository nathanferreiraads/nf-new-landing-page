#!/usr/bin/env python3
"""
NF Suplementos · gerar_seo.py (09/10/2026)
Rodar da raiz do repositorio:  python3 tools/gerar_seo.py

Gera tudo que e SEO/GEO/LLM e precisa bater com o conteudo real, para nunca ficar desatualizado:
  1. catalogo/index.html  -> bloco JSON-LD com cada produto e preco (lido dos proprios cards)
  2. blog/<slug>/index.html e blog/index.html  -> a partir de tools/blog/artigos.json + tools/blog/<slug>.html
  3. llms.txt e llms-full.txt  -> o resumo para as IAs (ChatGPT, Gemini, Claude, Perplexity) e o catalogo em texto
  4. sitemap.xml

Mudou preco no catalogo? Rode de novo. Artigo novo do mes? Escreva o .html em tools/blog/, ponha a linha no
artigos.json e rode de novo. Nada aqui e editado a mao no arquivo gerado.
"""
import json, os, re, html, datetime
from urllib.parse import quote

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://nfsuplementosvotu.com.br"
WA = "5517997587526"
HOJE = datetime.date.today().isoformat()

def rd(p): return open(os.path.join(RAIZ, p), encoding="utf-8").read()
def wr(p, s):
    p = os.path.join(RAIZ, p); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(s)
def txt(s): return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()
def esc(s): return html.escape(s, quote=True)

# ------------------------------------------------------------------ 1. catalogo
def produtos_do_catalogo():
    c = rd("catalogo/index.html")
    vistos, out = set(), []
    secao = ""
    for m in re.finditer(r'<section[^>]*id="([^"]+)"|<a href="https://wa\.me[^"]*" class="prod-card[^"]*"[^>]*>(.*?)</a>', c, re.S):
        if m.group(1): secao = m.group(1); continue
        b = m.group(2)
        nome = txt(re.search(r'prod-card-name">(.*?)</div>', b, re.S).group(1))
        marca = txt(re.search(r'prod-card-brand">(.*?)</div>', b, re.S).group(1))
        desc = re.search(r'prod-card-desc">(.*?)</div>', b, re.S)
        img = re.search(r'<img src="([^"]+)"', b).group(1)
        v = re.search(r'prod-price-value">(\d+)</span>(?:<span class="prod-price-cents">,(\d+))?', b)
        if not v: continue
        preco = "%s.%s" % (v.group(1), (v.group(2) or "00"))
        old = re.search(r'prod-price-old">R\$ ([\d\.]+,\d+)', b)
        chave = (marca.lower(), nome.lower())
        if chave in vistos: continue          # o mesmo produto aparece em mais de uma secao (oferta + categoria)
        vistos.add(chave)
        out.append({"nome": nome, "marca": marca, "desc": txt(desc.group(1)) if desc else "", "secao": secao,
                    "img": SITE + "/catalogo/" + img, "preco": preco, "de": old.group(1) if old else None})
    combos = []
    for m in re.finditer(r'<div class="agosto-combo[^"]*">(.*?)<a href', c, re.S):
        b = m.group(1)
        t = txt(re.search(r'combo-title">(.*?)</div>', b, re.S).group(1))
        v = re.search(r'combo-price-value">(\d+)</span>(?:<span class="combo-price-cents">,(\d+))?', b)
        d = re.search(r'combo-desc">(.*?)</div>', b, re.S)
        combos.append({"nome": t, "desc": txt(d.group(1)) if d else "", "preco": "%s,%s" % (v.group(1), v.group(2) or "00")})
    return out, combos

def schema_catalogo(prods):
    itens = []
    for i, p in enumerate(prods, 1):
        prod = {"@type": "Product", "name": "%s %s" % (p["marca"], p["nome"].title()), "brand": {"@type": "Brand", "name": p["marca"]},
                "image": p["img"], "category": p["secao"],
                "offers": {"@type": "Offer", "price": p["preco"], "priceCurrency": "BRL", "availability": "https://schema.org/InStock",
                           "url": SITE + "/catalogo/", "seller": {"@id": SITE + "/#store"},
                           "areaServed": {"@type": "City", "name": "Votuporanga"}}}
        if p["desc"]: prod["description"] = p["desc"]
        itens.append({"@type": "ListItem", "position": i, "item": prod})
    ld = [{"@context": "https://schema.org", "@type": "ItemList", "name": "Catálogo de suplementos NF Suplementos em Votuporanga",
           "url": SITE + "/catalogo/", "numberOfItems": len(itens), "itemListElement": itens},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Início", "item": SITE + "/"},
              {"@type": "ListItem", "position": 2, "name": "Catálogo", "item": SITE + "/catalogo/"}]}]
    return "".join('<script type="application/ld+json">%s</script>\n' % json.dumps(x, ensure_ascii=False, separators=(",", ":")) for x in ld)

def gravar_schema_catalogo(prods):
    c = rd("catalogo/index.html")
    a, b = "<!-- NF-SCHEMA-CATALOGO", "<!-- /NF-SCHEMA-CATALOGO -->"
    i = c.index(a); i = c.index("-->", i) + 3; j = c.index(b)
    c = c[:i] + "\n" + schema_catalogo(prods) + c[j:]
    wr("catalogo/index.html", c)

# ------------------------------------------------------------------ 2. blog
WA_SVG = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M.057 24l1.687-6.163a11.867 11.867 0 01-1.587-5.946C.16 5.335 5.495 0 12.05 0a11.817 11.817 0 018.413 3.488 11.824 11.824 0 013.48 8.414c-.003 6.557-5.338 11.892-11.893 11.892a11.9 11.9 0 01-5.688-1.448L.057 24zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884a9.86 9.86 0 001.51 5.26l-.999 3.648 3.978-1.215zm11.387-5.464c-.074-.124-.272-.198-.57-.347-.297-.149-1.758-.868-2.031-.967-.272-.099-.47-.149-.669.149-.198.297-.768.967-.941 1.165-.173.198-.347.223-.644.074-.297-.149-1.255-.462-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.297-.347.446-.521.151-.172.2-.296.3-.495.099-.198.05-.372-.025-.521-.075-.148-.669-1.611-.916-2.206-.242-.579-.487-.501-.669-.51l-.57-.01c-.198 0-.52.074-.792.372s-1.04 1.016-1.04 2.479 1.065 2.876 1.213 3.074c.149.198 2.096 3.2 5.077 4.487.709.306 1.263.489 1.694.626.712.226 1.36.194 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.695.248-1.29.173-1.414z"/></svg>'

HEAD_COMUM = '''<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<!-- rastreio da NF: ANTES do GTM -->
<script src="/js/nf-rastreio.js"></script>
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);})(window,document,'script','dataLayer','GTM-MN4V6NWL');</script>
<meta name="robots" content="index, follow, max-image-preview:large">
<meta name="geo.region" content="BR-SP">
<meta name="geo.placename" content="Votuporanga, São Paulo, Brasil">
<meta name="theme-color" content="#0A0A0A">
<link rel="icon" type="image/png" href="/assets/logo.png">
<link rel="alternate" type="text/plain" href="/llms.txt" title="LLMs.txt">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/blog/blog.css">'''

GTM_NOSCRIPT = '<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-MN4V6NWL" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>'

def header(ativo="blog"):
    return f'''<header class="site"><div class="site-inner">
  <a class="logo" href="/"><img src="/assets/logo.png" alt="NF Suplementos" width="34" height="34"><span>NF<small>SUPLEMENTOS · VOTUPORANGA</small></span></a>
  <nav class="menu" aria-label="Menu">
    <a href="/">Início</a><a href="/catalogo/">Catálogo</a><a href="/blog/"{' class="active"' if ativo == "blog" else ''}>Blog</a><a href="/#perguntas">Dúvidas</a>
  </nav>
  <a class="nav-cta" href="https://wa.me/{WA}?text={quote("Olá! Vim pelo blog da NF Suplementos.", safe="")}" data-produto="blog: botão do topo">Pedir no WhatsApp</a>
</div></header>'''

FOOTER = f'''<footer class="site-foot">
  <div class="flogo">NF SUPLEMENTOS</div>
  <p>Loja de suplementos em Votuporanga-SP · Entrega grátis no mesmo dia na cidade (pedido até 14h)<br>
  Seg a sex 9h às 18h · Sáb 9h às 12h · WhatsApp <a href="https://wa.me/{WA}">(17) 99758-7526</a> · <a href="https://www.instagram.com/_nfsuplementos" rel="noopener">@_nfsuplementos</a></p>
  <p class="foot-nav"><a href="/">Início</a> · <a href="/catalogo/">Catálogo e preços</a> · <a href="/blog/">Blog</a> · <a href="/#perguntas">Perguntas frequentes</a></p>
  <p class="aviso">Conteúdo educativo. Suplementos não são medicamentos e não substituem uma alimentação equilibrada. Gestantes, lactantes, crianças e pessoas com doenças ou em uso de medicamentos devem consultar médico ou nutricionista.</p>
</footer>'''

AUTOR = {"nome": "Equipe NF Suplementos", "cargo": "Loja de suplementos em Votuporanga-SP",
         "bio": "Quem escreve é a equipe que atende pelo WhatsApp e entrega suplementos originais em Votuporanga todos os dias. Os textos seguem as regras da ANVISA para suplementos alimentares e estudos científicos citados em cada artigo. É informação para você escolher melhor, não orientação individual: para isso, procure um nutricionista ou médico."}

def data_br(iso):
    m = ["janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"]
    d = datetime.date.fromisoformat(iso); return "%d de %s de %d" % (d.day, m[d.month - 1], d.year)

def artigo(a, todos):
    slug = a["slug"]; url = f"{SITE}/blog/{slug}/"
    corpo = rd(f"tools/blog/{slug}.html")
    faq = a.get("faq", [])
    rel = [x for x in todos if x["slug"] in a.get("relacionados", [])][:3]
    msg = a["cta_msg"]
    ld = [
        {"@context": "https://schema.org", "@type": "BlogPosting", "headline": a["h1"], "description": a["descricao"],
         "image": SITE + a.get("imagem", "/assets/og-nf-suplementos.jpg"), "datePublished": a["publicado"], "dateModified": a.get("atualizado", a["publicado"]),
         "inLanguage": "pt-BR", "mainEntityOfPage": url, "url": url, "articleSection": a["categoria"],
         "author": {"@type": "Organization", "name": AUTOR["nome"], "url": SITE + "/"},
         "publisher": {"@id": SITE + "/#store", "@type": "Store", "name": "NF Suplementos", "logo": {"@type": "ImageObject", "url": SITE + "/assets/logo.png"}},
         "about": a.get("sobre", []), "isPartOf": {"@type": "Blog", "@id": SITE + "/blog/#blog", "name": "Blog NF Suplementos"}},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Início", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": SITE + "/blog/"},
            {"@type": "ListItem", "position": 3, "name": a["curto"], "item": url}]},
    ]
    if faq:
        ld.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": txt(r)}} for q, r in faq]})
    lds = "\n".join('<script type="application/ld+json">%s</script>' % json.dumps(x, ensure_ascii=False) for x in ld)
    faq_html = ""
    if faq:
        faq_html = '<section class="faq" aria-labelledby="faq-t"><h2 id="faq-t">Perguntas frequentes</h2>\n' + "\n".join(
            f'<details{" open" if i == 0 else ""}><summary>{esc(q)}<span class="plus">+</span></summary><p>{r}</p></details>' for i, (q, r) in enumerate(faq)) + "\n</section>"
    rel_html = "".join(f'<a class="rel-card" href="/blog/{r["slug"]}/"><span class="tag">{esc(r["categoria"])}</span><h3>{esc(r["h1"])}</h3></a>' for r in rel)
    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
{HEAD_COMUM}
<title>{esc(a["titulo"])}</title>
<meta name="description" content="{esc(a["descricao"])}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="NF Suplementos">
<meta property="og:locale" content="pt_BR">
<meta property="og:title" content="{esc(a["h1"])}">
<meta property="og:description" content="{esc(a["descricao"])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}{a.get("imagem", "/assets/og-nf-suplementos.jpg")}">
<meta property="article:published_time" content="{a["publicado"]}">
<meta property="article:modified_time" content="{a.get("atualizado", a["publicado"])}">
<meta name="twitter:card" content="summary_large_image">
{lds}
</head>
<body>
{GTM_NOSCRIPT}
{header()}
<nav class="breadcrumb" aria-label="Você está em"><a href="/">Início</a> › <a href="/blog/">Blog</a> › <span>{esc(a["curto"])}</span></nav>
<article>
  <span class="eyebrow">{esc(a["categoria"])}</span>
  <h1>{esc(a["h1"])}</h1>
  <div class="meta">
    <div class="avatar">NF</div>
    <div class="who"><strong>{AUTOR["nome"]}</strong><span>{AUTOR["cargo"]}</span></div>
    <span class="read">{a["leitura"]} min de leitura · Atualizado em <time datetime="{a.get("atualizado", a["publicado"])}">{data_br(a.get("atualizado", a["publicado"]))}</time></span>
  </div>
  <p class="capsula">{a["capsula"]}</p>
{corpo}
{faq_html}
  <div class="cta-box" id="cta">
    <h2>{esc(a["cta_titulo"])}</h2>
    <p>{a["cta_texto"]}</p>
    <a class="btn-wpp" id="cta-wpp-{slug}" data-produto="blog: {slug}" href="https://wa.me/{WA}?text={quote(msg, safe="")}" target="_blank" rel="noopener">{WA_SVG}{esc(a["cta_botao"])}</a>
    <a class="btn-sec" href="/catalogo/">Ver catálogo com preços</a>
  </div>
  <div class="author">
    <div class="ava">NF</div>
    <div><h2 class="author-n">{AUTOR["nome"]}</h2><div class="cred">{AUTOR["cargo"]}</div><p>{AUTOR["bio"]}</p></div>
  </div>
</article>
{('<section class="related"><h2 class="rel-title">Leia também</h2><div class="rel-grid">' + rel_html + '</div></section>') if rel_html else ''}
{FOOTER}
</body>
</html>
'''

def vitrine(arts):
    pilar = [a for a in arts if a.get("pilar")]
    outros = [a for a in arts if not a.get("pilar")]
    def card(a, big=False):
        return f'''<a class="post-card{' big' if big else ''}" href="/blog/{a["slug"]}/"><span class="tag">{esc(a["categoria"])}</span><h2>{esc(a["h1"])}</h2><p>{txt(a["capsula"])[:170]}…</p><span class="ler">Ler artigo →</span></a>'''
    ld = {"@context": "https://schema.org", "@type": "Blog", "@id": SITE + "/blog/#blog", "name": "Blog NF Suplementos",
          "description": "Guias sobre whey protein, creatina, pré-treino e suplementação, da NF Suplementos em Votuporanga-SP.",
          "url": SITE + "/blog/", "inLanguage": "pt-BR", "publisher": {"@id": SITE + "/#store"},
          "blogPost": [{"@type": "BlogPosting", "headline": a["h1"], "url": f"{SITE}/blog/{a['slug']}/", "datePublished": a["publicado"]} for a in arts]}
    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
{HEAD_COMUM}
<title>Blog de Suplementação: Whey, Creatina e Pré-treino | NF Suplementos Votuporanga</title>
<meta name="description" content="Guias diretos sobre whey protein, creatina, pré-treino e como escolher suplementos originais. Da NF Suplementos, loja com entrega grátis no mesmo dia em Votuporanga-SP.">
<link rel="canonical" href="{SITE}/blog/">
<meta property="og:type" content="website">
<meta property="og:title" content="Blog NF Suplementos">
<meta property="og:description" content="Whey, creatina e pré-treino explicados sem enrolação. NF Suplementos, Votuporanga-SP.">
<meta property="og:url" content="{SITE}/blog/">
<meta property="og:image" content="{SITE}/assets/og-nf-suplementos.jpg">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
{GTM_NOSCRIPT}
{header()}
<main class="vitrine">
  <span class="eyebrow">Blog NF Suplementos</span>
  <h1>Suplementação sem enrolação</h1>
  <p class="lead">Whey, creatina, pré-treino e como escolher bem, explicado por quem entrega suplemento original em Votuporanga todo dia.</p>
  {"".join(card(a, True) for a in pilar)}
  <div class="post-grid">{"".join(card(a) for a in outros)}</div>
</main>
{FOOTER}
</body>
</html>
'''

# ------------------------------------------------------------------ 3. llms.txt
def llms(prods, combos, arts):
    marcas = sorted({p["marca"] for p in prods})
    base = f'''# NF Suplementos

> Loja de suplementos alimentares em Votuporanga, São Paulo, Brasil. Vende whey protein, creatina, pré-treino, termogênicos, vitaminas e mais de 200 produtos originais a pronta entrega. O pedido é feito pelo WhatsApp (17) 99758-7526 e a entrega é grátis no mesmo dia em Votuporanga para pedidos até as 14h.

## Dados da loja
- Nome: NF Suplementos (também conhecida como NF Suplementos Votuporanga)
- Cidade: Votuporanga, SP, Brasil. Atendimento online com entrega; o endereço do estoque é informado pelo WhatsApp para retirada.
- WhatsApp e telefone: +55 17 99758-7526
- Horário: segunda a sexta, 9h às 18h; sábado, 9h às 12h
- Entrega: grátis em Votuporanga, no mesmo dia para pedidos até as 14h. Outras cidades da região: consultar pelo WhatsApp.
- Pagamento: Pix, link de pagamento (cartão) ou pagamento na entrega
- Produtos: originais e lacrados, comprados das marcas ou de distribuidores autorizados
- Marcas: {", ".join(marcas)}
- Instagram: https://www.instagram.com/_nfsuplementos
- Google: {"https://www.google.com/maps/place/?q=place_id:ChIJJ413VvNZvZQRInhUreaYYPE"} (nota 5,0)

## Páginas
- [Site](https://nfsuplementosvotu.com.br/): como pedir, entrega, ofertas do mês e perguntas frequentes
- [Catálogo com preços](https://nfsuplementosvotu.com.br/catalogo/): todos os produtos, por categoria
- [Catálogo em texto](https://nfsuplementosvotu.com.br/llms-full.txt): a lista completa de produtos e preços atualizada
- [Blog](https://nfsuplementosvotu.com.br/blog/): guias de suplementação

## Blog
''' + "\n".join(f'- [{a["h1"]}]({SITE}/blog/{a["slug"]}/): {txt(a["descricao"])}' for a in arts) + "\n"
    full = base + f"\n## Catálogo completo (preços em reais, atualizado em {data_br(HOJE)})\n"
    nomes_secao = {"outubro": "Ofertas do mês", "byopure": "Byopure", "nyer": "Nyer Nutrition", "proteinas": "Proteínas (whey)", "creatina": "Creatina",
                   "pretreino": "Pré-treino", "supercoffee": "SuperCoffee", "sudract": "Sudract (endurance)", "endurance": "Endurance e carboidratos",
                   "termogenicos": "Termogênicos", "aminoacidos": "Aminoácidos", "vitaminas": "Vitaminas e saúde", "pastas": "Pastas e barras",
                   "hipercalorico": "Hipercalóricos e carboidratos", "acessorios": "Acessórios"}
    sec = None
    for p in prods:
        if p["secao"] != sec:
            sec = p["secao"]; full += f"\n### {nomes_secao.get(sec, sec)}\n"
        preco = p["preco"].replace(".", ",")
        de = f" (de R$ {p['de']})" if p["de"] else ""
        full += f"- {p['marca']} {p['nome'].title()}" + (f" · {p['desc']}" if p["desc"] else "") + f": R$ {preco}{de}\n"
    if combos:
        full += "\n### Combos\n" + "".join(f"- {c['nome'].title()} ({c['desc']}): R$ {c['preco']}\n" for c in combos)
    full += "\nPreços sujeitos a alteração e ao estoque do dia. Para pedir: WhatsApp +55 17 99758-7526.\n"
    return base, full

# ------------------------------------------------------------------ 4. sitemap
def sitemap(arts):
    urls = [(SITE + "/", HOJE, "1.0"), (SITE + "/catalogo/", HOJE, "0.9"), (SITE + "/blog/", HOJE, "0.8")]
    urls += [(f"{SITE}/blog/{a['slug']}/", a.get("atualizado", a["publicado"]), "0.9" if a.get("pilar") else "0.7") for a in arts]
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(
        f"  <url><loc>{u}</loc><lastmod>{d}</lastmod><priority>{p}</priority></url>\n" for u, d, p in urls) + "</urlset>\n"

if __name__ == "__main__":
    prods, combos = produtos_do_catalogo()
    gravar_schema_catalogo(prods)
    arts = json.load(open(os.path.join(RAIZ, "tools/blog/artigos.json"), encoding="utf-8"))
    for a in arts:
        wr(f"blog/{a['slug']}/index.html", artigo(a, arts))
    wr("blog/index.html", vitrine(arts))
    base, full = llms(prods, combos, arts)
    wr("llms.txt", base); wr("llms-full.txt", full)
    wr("sitemap.xml", sitemap(arts))
    print(f"ok: {len(prods)} produtos no schema, {len(combos)} combos, {len(arts)} artigos, sitemap com {len(arts) + 3} urls")
