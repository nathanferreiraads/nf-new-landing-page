#!/usr/bin/env python3
"""Uma vez só (24/11/2026): transforma os cards do catálogo antigo em tools/catalogo/produtos.json.
Daqui em diante a fonte é o produtos.json; este script fica só de registro."""
import json, re, sys, unicodedata

ORIG, DEST = sys.argv[1], sys.argv[2]
d = json.load(open(ORIG, encoding="utf-8"))

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

# pedido do Nathan em 24/11/2026: fora de estoque ou fora de linha
FORA = {("nyer nutrition", "creatina pura 300g"), ("nyer nutrition", "creatina pura"),
        ("dux nutrition", "fresh whey 450g"), ("probiótica", "100% pure whey"),
        ("dux nutrition", "body collagen protein"), ("nutra gold", "whey 3w grego"),
        ("nutrata", "barrinha whey grego")}

# seção antiga -> categoria nova (as seções por marca somem; cada produto fica na categoria dele)
PARA = {"proteinas": "whey", "creatina": "creatina", "pretreino": "pre-treino", "termogenicos": "termogenicos",
        "supercoffee": "cafe", "sudract": "endurance", "endurance": "endurance", "aminoacidos": "aminoacidos",
        "vitaminas": "vitaminas", "pastas": "pastas", "hipercalorico": "massa", "acessorios": "acessorios"}
ESPECIAL = {("byopure", "byocoffe 300g"): "cafe", ("byopure", "magnésio inositol"): "vitaminas",
            ("byopure", "creatina 210g"): None,                       # é a mesma Creatina Pura 210g da seção creatina
            ("byopure", "whey world collection 900g"): "whey", ("byopure", "crazyness whey 1kg"): "whey",
            ("nyer nutrition", "dark pump pré treino"): "pre-treino", ("nyer nutrition", "brutal termogênico"): "termogenicos"}

CATS = [
 ("whey", "Whey protein", "Whey concentrado, isolado e hidrolisado, em pote ou refil, a pronta entrega em Votuporanga."),
 ("creatina", "Creatina", "Creatina monohidratada pura, de 210 g a 510 g, das marcas mais pedidas da loja."),
 ("pre-treino", "Pré-treino", "Pré-treinos com e sem cafeína, para treinar de dia ou à noite."),
 ("termogenicos", "Termogênicos", "Termogênicos em cápsula e em pó, e cafeína pura."),
 ("cafe", "Café funcional", "Cafés funcionais para começar o dia ou trocar o pré-treino."),
 ("endurance", "Géis e hidratação", "Géis de carboidrato, repositores de sais e isotônicos para corrida, pedal e prova."),
 ("aminoacidos", "Aminoácidos", "Glutamina, beta-alanina e arginina em pó."),
 ("vitaminas", "Vitaminas e saúde", "Vitaminas, minerais, ômega 3 e colágeno para o dia a dia."),
 ("massa", "Hipercalóricos e carboidratos", "Hipercalórico, maltodextrina, dextrose e palatinose para quem precisa de mais calorias."),
 ("pastas", "Pastas e barras", "Pasta de amendoim e barra proteica para o lanche."),
 ("acessorios", "Acessórios", "Coqueteleira, galão e camiseta da NF."),
]
CERTO = {("z2", "gel z2 40g"): "Gel Z2 40g", ("z2", "saltz sachê 15g"): "SaltZ sachê 15g Z2",
         ("venom labs", "colágeno venom"): "Colágeno Venom Labs 230g", ("nf suplementos", "camiseta dry fit nf"): "Camiseta Dry Fit NF",
         ("byopure", "crazyness whey 1kg"): "Whey Crazyness 1kg Byopure", ("byopure", "crazyness whey 1,8kg"): "Whey Crazyness 1,8kg Byopure",
         ("isn nutrition", "creatina kreas 300g"): "Creatina Kreas 300g ISN", ("dux nutrition", "whey dux"): "Whey Dux 900g Dux Nutrition",
         ("byopure", "collagen type ii + msm"): "Collagen Type II + MSM Byopure", ("nutrition", "nac 60cps"): "NAC 60 cáps Nutrition",
         ("darkness", "évora pw 300g"): "Évora PW 300g Darkness", ("caffeine army", "super coffee 220g"): "SuperCoffee 220g Caffeine Army",
         ("caffeine army", "super coffee 380g"): "SuperCoffee 380g Caffeine Army"}
def limpar(f, ch, p):
    if ch in CERTO: return CERTO[ch]
    f = re.sub(r"(\d)(G|Kg|KG|Ml|ML|L)\b", lambda m: m.group(1) + m.group(2).lower().replace("l", "l"), f)
    f = re.sub(r"(\d+)\s?Cps\b", r"\1 cáps", f, flags=re.I)
    f = f.replace(" De ", " de ").replace("C/ Sabor", "com sabor").replace("Bt Gel", "BT Gel").replace("2.2l", "2,2 L")
    if ch[1] == "bt gel nitrato 30g": f += " " + p["desc"].split("·")[0].strip().lower()
    return f

cats = {c[0]: {"id": c[0], "titulo": c[1], "texto": c[2], "itens": []} for c in CATS}
vistos = set(); usados = set()
for p in d["prods"]:
    if p.get("combo"): continue
    ch = (p["marca"].lower(), p["nome"].lower())
    if ch in FORA: continue
    cat = ESPECIAL.get(ch, PARA.get(p["sec"])) if ch in ESPECIAL or p["sec"] in PARA else None
    if p["sec"] in ("outubro", "byopure", "nyer") and ch not in ESPECIAL: raise SystemExit("sem categoria: %r" % (ch,))
    if not cat: continue
    if (ch, p["preco"]) in vistos: continue          # o mesmo produto em duas seções antigas
    vistos.add((ch, p["preco"]))
    m = re.search(r"Quero (?:o |a |os |as )?(.+?) por R\$", p["msg"])
    falado = m.group(1).strip() if m else "%s %s" % (p["nome"].title(), p["marca"])
    nome = p["nome"]
    if ch == ("byopure", "lipo z 60cps"):          # o Nathan, 23/11: o Lipo Z é da linha Crazyness
        nome, falado = "CRAZYNESS LIPO Z 60CPS", "Lipo Z Crazyness 60 cápsulas"
    falado = limpar(falado, ch, p)
    ident = slug(p["marca"] + " " + nome)
    if ident in usados:                               # mesmo nome, versão diferente (BT Gel sem e com cafeína)
        ident = slug(p["marca"] + " " + nome + " " + p["desc"].split("·")[0]); nome = nome + " " + p["desc"].split("·")[0].strip().upper()
    usados.add(ident)
    it = {"id": ident, "marca": p["marca"], "nome": nome, "falado": falado, "desc": p["desc"],
          "preco": p["preco"], "de": p["de"], "img": p["img"]}
    if "LANÇAMENTO" in (p.get("tag") or ""): it["selo"] = "Lançamento"
    cats[cat]["itens"].append(it)

ids = [i["id"] for c in cats.values() for i in c["itens"]]
assert len(ids) == len(set(ids)), "id repetido"
ofertas = {
 "titulo": "Ofertas",
 "texto": "Enquanto durar o estoque.",
 "produtos": ["byopure-crazyness-whey-1kg"],
 "combos": [{"id": "combo-2x-whey-crazyness-1kg", "marca": "Byopure", "nome": "2X WHEY CRAZYNESS 1KG",
             "falado": "Combo 2x Whey Crazyness 1kg Byopure", "desc": "2 potes de 1 kg · 2 kg de whey no total",
             "preco": "199,90", "de": "259,80", "img": "mockups/whey-crazyness-1kg.png", "selo": "Combo"}],
}
json.dump({"_leia": "Fonte única do catálogo. Mudou preço ou estoque? Edite aqui e rode: python3 tools/gerar_catalogo.py && python3 tools/gerar_seo.py",
           "ofertas": ofertas, "categorias": [cats[c[0]] for c in CATS]},
          open(DEST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("produtos:", len(ids), "| por categoria:", {c["id"]: len(c["itens"]) for c in cats.values()})
