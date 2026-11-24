#!/usr/bin/env python3
"""
NF Suplementos · gerar_catalogo.py (24/11/2026)
Rodar da raiz do repositorio:  python3 tools/gerar_catalogo.py && python3 tools/gerar_seo.py

Monta catalogo/index.html a partir de tools/catalogo/produtos.json (a fonte unica: nome, preco, estoque).
O preco de cada produto mora em UM lugar so. O carrinho (catalogo/carrinho.js) le o preco do proprio card.
Depois, o gerar_seo.py preenche o JSON-LD dos produtos, o llms-full.txt e o sitemap.
"""
import json, os, html, datetime
from urllib.parse import quote

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://nfsuplementosvotu.com.br"
WA = "5517997587526"
HOJE = datetime.date.today()
MESES = "janeiro fevereiro março abril maio junho julho agosto setembro outubro novembro dezembro".split()

def esc(s): return html.escape(str(s), quote=True)
def centavos(p): return int(round(float(p.replace(".", "").replace(",", ".")) * 100))
def reais(c): return ("%d,%02d" % (c // 100, c % 100))
def wa(msg): return "https://wa.me/%s?text=%s" % (WA, quote(msg, safe=""))

D = json.load(open(os.path.join(RAIZ, "tools/catalogo/produtos.json"), encoding="utf-8"))
POR_ID = {i["id"]: i for c in D["categorias"] for i in c["itens"]}
CAT_SAB = {i["id"]: i.get("sabores", c.get("sabores", False)) for c in D["categorias"] for i in c["itens"]}
TOTAL = len(POR_ID) + len(D["ofertas"]["combos"])

FAQ = [
 ("Como funciona o pedido pelo catálogo?",
  "Toque em Adicionar nos produtos que você quer, abra Ver pedido e toque em Enviar pedido no WhatsApp. A Fernanda recebe a lista pronta com o total, confirma o estoque e os sabores e combina a entrega e o pagamento."),
 ("Como escolho o sabor?",
  "Os sabores variam conforme a disponibilidade do estoque no dia. No pedido, escreva o sabor que você prefere; a Fernanda confirma no WhatsApp quais sabores tem antes de fechar."),
 ("Vocês entregam no mesmo dia em Votuporanga?",
  "Sim. Pedidos feitos até as 14h são entregues no mesmo dia em Votuporanga, com entrega grátis."),
 ("Quais as formas de pagamento?",
  "Pix, link de pagamento (cartão) ou pagamento na entrega. O pagamento é combinado no WhatsApp, nada é cobrado nesta página."),
 ("Os suplementos são originais?",
  "Sim. Todos os produtos são originais e lacrados, comprados das marcas oficiais ou de distribuidores autorizados. A NF é loja parceira oficial da Byopure em Votuporanga."),
 ("Qual o horário de atendimento?",
  "Segunda a sexta, das 9h às 18h, e sábado, das 9h às 12h."),
 ("Vocês entregam em outras cidades da região?",
  "A entrega grátis no mesmo dia é para Votuporanga. Para outras cidades da região, chame no WhatsApp e consulte."),
]

WA_SVG = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor"><path d="M.057 24l1.687-6.163a11.867 11.867 0 01-1.587-5.946C.16 5.335 5.495 0 12.05 0a11.817 11.817 0 018.413 3.488 11.824 11.824 0 013.48 8.414c-.003 6.557-5.338 11.892-11.893 11.892a11.9 11.9 0 01-5.688-1.448L.057 24zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884a9.86 9.86 0 001.51 5.26l-.999 3.648 3.978-1.607zm11.387-5.464c-.074-.124-.272-.198-.57-.347-.297-.149-1.758-.868-2.031-.967-.272-.099-.47-.149-.669.149-.198.297-.768.967-.941 1.165-.173.198-.347.223-.644.074-.297-.149-1.255-.462-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.297-.347.446-.521.151-.172.2-.296.3-.495.099-.198.05-.372-.025-.521-.075-.148-.669-1.611-.916-2.206-.242-.579-.487-.501-.669-.51l-.57-.01c-.198 0-.52.074-.792.372s-1.04 1.016-1.04 2.479 1.065 2.876 1.213 3.074c.149.198 2.095 3.2 5.076 4.487.709.306 1.263.489 1.694.626.712.226 1.36.194 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.695.248-1.29.173-1.414z"/></svg>'

def card(p, destaque=False, sab=False):
    sab = p.get("sabores", sab)
    c = centavos(p["preco"]); de = centavos(p["de"]) if p.get("de") else 0
    selo = ""
    if p.get("selo"): selo = '<span class="selo selo-nome">%s</span>' % esc(p["selo"])
    elif de > c: selo = '<span class="selo">-%d%%</span>' % round((1 - c / de) * 100)
    antes = '<s>R$ %s</s>' % reais(de) if de > c else ""
    return f'''<article class="p{' p-destaque' if destaque else ''}"{' data-sabor="1"' if sab else ''} data-id="{esc(p['id'])}" data-nome="{esc(p['falado'])}" data-preco="{c}" data-busca="{esc((p['marca'] + ' ' + p['nome'] + ' ' + p['falado'] + ' ' + p['desc']).lower())}">
<div class="p-img{' p-img2' if p.get('img2') else ''}">{selo}<img src="{esc(p['img'])}" alt="{esc(p['falado'])}" loading="lazy" decoding="async" width="300" height="300">{('<img src="%s" alt="" loading="lazy" decoding="async" width="300" height="300">' % esc(p['img2'])) if p.get('img2') else ''}</div>
<div class="p-txt">
<p class="p-marca">{esc(p['marca'])}</p>
<h3 class="p-nome">{esc(p['nome'])}</h3>
<p class="p-desc">{esc(p['desc'])}</p>{'<p class="p-sabor">Sabores conforme a disponibilidade</p>' if sab else ''}
</div>
<div class="p-pe">
<p class="p-preco">{antes}<strong>R$ {reais(c)}</strong></p>
<div class="qtd" data-qtd>
<button type="button" class="menos" aria-label="Tirar um {esc(p['falado'])} do pedido" hidden>−</button>
<span class="n" aria-live="polite" hidden>0</span>
<button type="button" class="mais" aria-label="Adicionar {esc(p['falado'])} ao pedido"><span class="mais-t">Adicionar</span><span class="mais-s" aria-hidden="true">+</span></button>
</div>
</div>
</article>'''

def pagina():
    nav = '<a href="#ofertas" class="chip chip-of">Ofertas</a>' + "".join(
        '<a href="#%s" class="chip">%s</a>' % (c["id"], esc(c["titulo"])) for c in D["categorias"])
    of = D["ofertas"]
    of_cards = "".join(card(x, True) for x in of["combos"]) + "".join(card(POR_ID[i], True, CAT_SAB[i]) for i in of["produtos"])
    secoes = ""
    for c in D["categorias"]:
        extra = ""
        if c["id"] == "whey":
            extra = ' <a href="/blog/byopure-em-votuporanga/">A NF é loja parceira oficial da Byopure em Votuporanga: veja qual escolher.</a>'
        secoes += f'''<section class="cat" id="{c['id']}" aria-labelledby="t-{c['id']}">
<header class="cat-h"><h2 id="t-{c['id']}">{esc(c['titulo'])}</h2><p>{esc(c['texto'])}{extra}</p></header>
<div class="grade">
{chr(10).join(card(p, False, c.get('sabores', False)) for p in c['itens'])}
</div>
</section>
'''
    faq_html = "".join('<details><summary>%s</summary><p>%s</p></details>' % (esc(q), esc(a)) for q, a in FAQ)
    faq_ld = json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
        ensure_ascii=False, separators=(",", ":"))
    atual = "%d de %s de %d" % (HOJE.day, MESES[HOJE.month - 1], HOJE.year)
    css = open(os.path.join(RAIZ, "tools/catalogo/catalogo.css"), encoding="utf-8").read()
    oi = wa("Olá! Vim pelo catálogo e quero tirar uma dúvida.")
    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Catálogo NF Suplementos Votuporanga: preços de whey, creatina e pré-treino</title>
<meta name="description" content="Catálogo da NF Suplementos com preço: whey, creatina, pré-treino, termogênicos e vitaminas originais. Monte seu pedido, envie no WhatsApp e receba no mesmo dia em Votuporanga.">
<meta name="robots" content="index, follow, max-image-preview:large">
<link rel="canonical" href="{SITE}/catalogo/">
<meta name="geo.region" content="BR-SP">
<meta name="geo.placename" content="Votuporanga, São Paulo, Brasil">
<meta property="og:type" content="website">
<meta property="og:site_name" content="NF Suplementos">
<meta property="og:locale" content="pt_BR">
<meta property="og:title" content="Catálogo NF Suplementos · Votuporanga">
<meta property="og:description" content="{TOTAL} produtos originais com preço. Monte seu pedido e receba no mesmo dia em Votuporanga.">
<meta property="og:url" content="{SITE}/catalogo/">
<meta property="og:image" content="{SITE}/assets/og-nf-suplementos.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" href="logo-nf.png">
<link rel="alternate" type="text/plain" href="{SITE}/llms-full.txt" title="Catálogo em texto">
<!-- NF-SCHEMA-CATALOGO (gerado por tools/gerar_seo.py a partir do produtos.json; nao editar a mao) -->
<!-- /NF-SCHEMA-CATALOGO -->
<script type="application/ld+json">{faq_ld}</script>
<meta name="theme-color" content="#000000">
<!-- rastreio da NF: ANTES do GTM -->
<script src="/js/nf-rastreio.js"></script>
<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
}})(window,document,'script','dataLayer','GTM-MN4V6NWL');</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
{css}
</style>
</head>
<body>
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-MN4V6NWL" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<a class="pular" href="#ofertas">Ir para os produtos</a>

<header class="topo">
<a class="marca" href="/" aria-label="NF Suplementos, página inicial"><img src="logo-nf.png" alt="NF Suplementos" width="200" height="214"><span>Votuporanga</span></a>
<a class="header-wa" href="{oi}" target="_blank" rel="noopener" data-produto="catálogo: dúvida no topo">{WA_SVG}<span>Tirar dúvida</span></a>
</header>

<section class="abre">
<div class="abre-in">
<h1>Suplementos em Votuporanga. <span>Monte seu pedido e receba hoje.</span></h1>
<p class="abre-p">{TOTAL} produtos originais com preço. Entrega grátis na cidade para pedido feito até as 14h. Você escolhe aqui e fecha com a Fernanda no WhatsApp.</p>
<ol class="passos">
<li><span><b>Adicione</b> os produtos ao pedido</span></li>
<li><span><b>Confira</b> a lista e diga o sabor</span></li>
<li><span><b>Envie</b> pronto no WhatsApp</span></li>
</ol>
<label class="busca"><span class="so-leitor">Buscar produto ou marca</span>
<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.6-3.6"/></svg>
<input type="search" id="busca" placeholder="Buscar whey, creatina, Byopure..." autocomplete="off" enterkeyhint="search"></label>
</div>
</section>

<nav class="chips" aria-label="Categorias"><div class="chips-in">{nav}</div></nav>

<main id="catalogo">
<p class="busca-info" id="busca-info" hidden></p>
<div class="vazio" id="busca-vazio" hidden>
<p>Não achei esse produto no catálogo. A loja tem mais de 200 itens, pergunte para a Fernanda.</p>
<a class="search-empty" href="{wa("Olá! Procurei um produto no catálogo e não achei. Vocês têm?")}" target="_blank" rel="noopener" data-produto="catálogo: busca sem resultado">Perguntar no WhatsApp</a>
</div>

<section class="ofertas" id="ofertas" aria-labelledby="t-ofertas">
<header class="cat-h"><h2 id="t-ofertas">{esc(of['titulo'])}</h2><p>{esc(of['texto'])}</p></header>
<div class="grade grade-of">
{of_cards}
</div>
</section>

{secoes}</main>

<section class="faq" id="duvidas" aria-labelledby="t-faq">
<h2 id="t-faq">Dúvidas sobre o pedido</h2>
{faq_html}
<p class="faq-mais">Quer entender o que tomar? Leia o <a href="/blog/">blog da NF Suplementos</a>.</p>
</section>

<footer class="rodape">
<p class="rodape-nf">NF Suplementos</p>
<p>Loja de suplementos em Votuporanga-SP. Entrega grátis no mesmo dia na cidade, para pedido até as 14h.<br>
Seg a sex 9h às 18h · Sáb 9h às 12h · WhatsApp <a class="foot-social" href="https://wa.me/{WA}" target="_blank" rel="noopener">(17) 99758-7526</a> · <a href="https://www.instagram.com/_nfsuplementos" target="_blank" rel="noopener">@_nfsuplementos</a></p>
<p class="rodape-nav"><a href="/">Início</a><a href="/blog/">Blog</a><a href="/#perguntas">Perguntas frequentes</a></p>
<p class="rodape-obs">Preços atualizados em {atual}, sujeitos ao estoque do dia. Suplementos não são medicamentos e não substituem uma alimentação equilibrada.</p>
</footer>

<button type="button" class="barra" id="barra" hidden aria-haspopup="dialog" aria-controls="pedido">
<span class="barra-n" id="barra-n">0</span><span class="barra-t">Ver pedido</span><span class="barra-v" id="barra-v">R$ 0,00</span>
</button>

<div class="fundo" id="fundo" hidden></div>
<aside class="pedido" id="pedido" role="dialog" aria-modal="true" aria-labelledby="t-pedido" hidden>
<header class="pedido-h"><h2 id="t-pedido">Seu pedido</h2><button type="button" class="fechar" id="fechar" aria-label="Fechar o pedido">×</button></header>
<div class="pedido-corpo">
<p class="pedido-vazio" id="pedido-vazio">Seu pedido está vazio. Toque em Adicionar nos produtos do catálogo.</p>
<ul class="itens" id="itens"></ul>
<label class="obs" id="obs-caixa" hidden><span id="obs-titulo">Observação (opcional)</span>
<small class="obs-aviso" id="obs-aviso" hidden>Os sabores dependem do estoque do dia. Escreva o que você prefere e a Fernanda confirma no WhatsApp o que tem.</small>
<textarea id="obs" rows="2" maxlength="200" placeholder="Ex.: whey de chocolate, pré-treino de uva"></textarea></label>
</div>
<footer class="pedido-pe" id="pedido-pe" hidden>
<p class="total"><span>Total</span><strong id="total">R$ 0,00</strong></p>
<p class="pedido-nota">Entrega grátis em Votuporanga. O pagamento (Pix, link ou na entrega) você combina no WhatsApp.</p>
<a class="enviar" id="enviar" href="{oi}" target="_blank" rel="noopener">{WA_SVG}Enviar pedido no WhatsApp</a>
<button type="button" class="limpar" id="limpar">Esvaziar pedido</button>
</footer>
</aside>

<script src="carrinho.js" defer></script>
</body>
</html>
'''

if __name__ == "__main__":
    open(os.path.join(RAIZ, "catalogo/index.html"), "w", encoding="utf-8").write(pagina())
    print("ok: catalogo/index.html com %d produtos e %d combo(s)" % (len(POR_ID), len(D["ofertas"]["combos"])))
