#!/usr/bin/env python3
"""IndexNow (09/10/2026): avisa Bing (que alimenta a busca do ChatGPT e o Copilot), Yandex e outros que uma URL mudou.
O Google nao usa IndexNow; para ele vale o sitemap. A chave e publica por desenho (fica na raiz do site).
Uso, da raiz do repo, DEPOIS do deploy:  python3 tools/indexnow.py   (manda todas as URLs do sitemap.xml)"""
import json, re, os, urllib.request
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY = "912a00bb19c54b1dacbe02fb4d75fd73"
urls = re.findall(r"<loc>([^<]+)</loc>", open(os.path.join(RAIZ, "sitemap.xml"), encoding="utf-8").read())
corpo = {"host": "nfsuplementosvotu.com.br", "key": KEY, "keyLocation": "https://nfsuplementosvotu.com.br/" + KEY + ".txt", "urlList": urls}
r = urllib.request.Request("https://api.indexnow.org/indexnow", data=json.dumps(corpo).encode(), headers={"Content-Type": "application/json; charset=utf-8"})
try:
    with urllib.request.urlopen(r, timeout=30) as f: print("IndexNow", f.status, len(urls), "urls")
except urllib.error.HTTPError as e: print("IndexNow ERRO", e.code, e.read().decode()[:300])
