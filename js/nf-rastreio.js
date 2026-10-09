/* ============================================================
   NF Suplementos · nf-rastreio.js  (09/10/2026)
   ------------------------------------------------------------
   A ORIGEM do visitante até o WhatsApp, sem Tintim. O Nathan: "as origens precisam persistir das páginas até o nosso
   whatsapp, por link rastreável normal. não pode perder".
   1) dá um id anônimo ao visitante (nf_vid: localStorage + cookie, o mesmo nome das páginas /ir e /go do painel)
   2) guarda a origem (utm, fbclid, gclid, de onde veio) por 30 dias: a LP passa para o catálogo e a bio para os dois
   3) PageView com o MESMO event_id no GTM (pixel do navegador) e no servidor (site-capi do painel): o Meta conta uma vez
   4) todo link de WhatsApp leva o CÓDIGO INVISÍVEL do visitante na mensagem, depois da 1a palavra (o WhatsApp apaga o
      que fica no fim). No clique: grava o clique no painel (pre-lead) e dispara ClickButtonWhatsapp no navegador (GTM) e
      no servidor com o mesmo event_id. Quando a mensagem chega, o painel lê o código e o card nasce com a origem e o
      produto. O Contact NÃO sai daqui: é da 1a mensagem do lead, e quem dispara é o painel.
   Carrega ANTES do GTM (o PageView do GTM lê o nf_pv_event_id). Não depende do GTM: com bloqueador de anúncio, o painel
   e o servidor recebem igual. Escrito em ES5 de propósito (celular antigo).
   ============================================================ */
(function () {
  "use strict";
  var W = window, D = document;
  if (W.NF && W.NF.vid) return;   // carregado 2x: não duplica eventos

  var PAINEL = "https://nfsuplementos-painel.netlify.app/.netlify/functions";   // o .netlify.app do painel, nunca o domínio
  var NUMERO = "5517997587526";                                                 // o número conectado ao painel
  var MSG_PADRAO = "Olá! Vim pelo site da NF Suplementos.";
  var DIAS_ORIGEM = 30;
  var CHAVES = ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "fbclid", "gclid"];
  // botão sem produto: o nome que aparece no painel
  var BOTOES = { "header-wa": "botão do topo", "cta-primary": "botão principal", "cta-btn": "botão principal", "sticky-wa": "botão fixo",
    "whatsapp-float": "botão flutuante", "fern-cta": "seção da Fernanda", "foot-social": "rodapé", "bio-wa": "botão do WhatsApp" };
  W.dataLayer = W.dataLayer || [];

  function uuid() {
    if (W.crypto && W.crypto.randomUUID) return W.crypto.randomUUID();
    var b = []; for (var i = 0; i < 32; i++) b.push(Math.floor(Math.random() * 16).toString(16));
    b[12] = "4"; b[16] = (8 + Math.floor(Math.random() * 4)).toString(16);
    var s = b.join(""); return s.slice(0, 8) + "-" + s.slice(8, 12) + "-" + s.slice(12, 16) + "-" + s.slice(16, 20) + "-" + s.slice(20);
  }
  function lerCookie(n) { try { var m = D.cookie.match(new RegExp("(?:^|; )" + n + "=([^;]*)")); return m ? decodeURIComponent(m[1]) : null; } catch (e) { return null; } }
  function gravarCookie(n, v, dias) { try { D.cookie = n + "=" + encodeURIComponent(v) + ";path=/;max-age=" + Math.round(dias * 86400) + ";SameSite=Lax"; } catch (e) {} }
  function ler(k) { try { return W.localStorage.getItem(k); } catch (e) { return null; } }
  function gravar(k, v) { try { W.localStorage.setItem(k, v); } catch (e) {} }
  function params() {
    var o = {};
    (location.search || "").replace(/^\?/, "").split("&").forEach(function (kv) {
      if (!kv) return;
      var i = kv.indexOf("="), k = i < 0 ? kv : kv.slice(0, i), v = i < 0 ? "" : kv.slice(i + 1);
      try { o[decodeURIComponent(k)] = decodeURIComponent(v.replace(/\+/g, " ")); } catch (e) {}
    });
    return o;
  }
  function pagina() { var p = location.pathname || "/"; return /^\/catalogo/.test(p) ? "catalogo" : /^\/bio/.test(p) ? "bio" : "lp"; }
  function limpo(s) { return String(s == null ? "" : s).replace(/\s+/g, " ").replace(/^\s+|\s+$/g, "").slice(0, 90); }

  // ---------- 1) o visitante ----------
  var vid = ler("nf_vid") || lerCookie("nf_vid");
  if (!/^[0-9a-f]{8}-[0-9a-f]{2}/i.test(vid || "")) vid = uuid();   // o código usa os 10 primeiros hex do vid
  gravar("nf_vid", vid); gravarCookie("nf_vid", vid, 400);

  // ---------- 2) a origem, que não pode se perder entre as páginas ----------
  var P = params(), agora = Date.now(), pg = pagina();
  var veio = {}, temOrigem = false;
  CHAVES.forEach(function (k) { if (P[k]) { veio[k] = String(P[k]).slice(0, 300); temOrigem = true; } });
  // a BIO: o Instagram põe sozinho utm_source=ig&utm_medium=social no link do perfil. Na bio vale a nossa marca
  // (instagram / link_bio), que o painel mostra como "Link Bio"; com fbclid o painel mostra Meta Ads (decisão de 06/10).
  if (pg === "bio" && (!veio.utm_source || /^(ig|instagram)$/i.test(veio.utm_source))) {
    veio.utm_source = "instagram"; veio.utm_medium = "link_bio"; veio.utm_campaign = "bio_nf"; delete veio.utm_content; temOrigem = true;
  }
  var ref = D.referrer || "", refHost = "";
  try { refHost = ref ? new URL(ref).hostname.replace(/^www\./, "") : ""; } catch (e) { refHost = ""; }
  var externo = !!refHost && refHost !== location.hostname.replace(/^www\./, "");
  function deOndeVeio(h) {
    if (/(^|\.)(google|bing|yahoo|duckduckgo|ecosia)\./.test(h)) return { utm_source: h.replace(/^.*?(google|bing|yahoo|duckduckgo|ecosia)\..*$/, "$1"), utm_medium: "organic" };
    if (/instagram\.com$/.test(h)) return { utm_source: "instagram", utm_medium: "referral" };
    if (/(^|\.)(facebook\.com|fb\.com|fb\.me)$/.test(h)) return { utm_source: "facebook", utm_medium: "referral" };
    if (/youtube\.com$|youtu\.be$/.test(h)) return { utm_source: "youtube", utm_medium: "referral" };
    if (/tiktok\.com$/.test(h)) return { utm_source: "tiktok", utm_medium: "referral" };
    return { utm_source: h.slice(0, 60), utm_medium: "referral" };
  }
  var origem = null;
  try { origem = JSON.parse(ler("nf_origem") || "null"); } catch (e) { origem = null; }
  if (origem && !(agora - (origem.ts || 0) < DIAS_ORIGEM * 864e5)) origem = null;
  if (temOrigem) {
    origem = veio; origem.ts = agora; origem.pagina = location.href.split("#")[0].slice(0, 500); origem.referrer = externo ? ref.slice(0, 300) : null;
    gravar("nf_origem", JSON.stringify(origem));
  } else if (externo && !origem) {
    origem = deOndeVeio(refHost); origem.ts = agora; origem.pagina = location.href.split("#")[0].slice(0, 500); origem.referrer = ref.slice(0, 300);
    gravar("nf_origem", JSON.stringify(origem));
  }
  // _fbc: o clique do anúncio. O pixel cria quando carrega; aqui garante mesmo sem o pixel (bloqueador), no formato do Meta
  if (veio.fbclid && !lerCookie("_fbc")) gravarCookie("_fbc", "fb.1." + agora + "." + veio.fbclid, 90);
  function fbcAtual() { return lerCookie("_fbc") || (origem && origem.fbclid ? "fb.1." + origem.ts + "." + origem.fbclid : null); }

  // ---------- envio: beacon de texto puro (sem preflight; sobrevive à troca de página para o WhatsApp) ----------
  function enviar(url, corpo) {
    var s = JSON.stringify(corpo);
    try { if (navigator.sendBeacon && navigator.sendBeacon(url, new Blob([s], { type: "text/plain;charset=UTF-8" }))) return; } catch (e) {}
    try { fetch(url, { method: "POST", keepalive: true, mode: "no-cors", headers: { "Content-Type": "text/plain;charset=UTF-8" }, body: s }); } catch (e) {}
  }
  function novoId(tipo) { return tipo + "." + vid.replace(/-/g, "").slice(0, 10) + "." + Date.now() + "." + Math.floor(Math.random() * 1e4); }
  function capi(nome, id, extra) {
    var b = { event_name: nome, event_id: id, event_time: Date.now(), url: location.href.split("#")[0].slice(0, 500), fbp: lerCookie("_fbp"), fbc: fbcAtual(), external_id: vid };
    for (var k in (extra || {})) if (extra.hasOwnProperty(k)) b[k] = extra[k];
    enviar(PAINEL + "/site-capi", b);
  }

  // ---------- 3) PageView: o GTM lê o nf_pv_event_id; o servidor manda o mesmo ----------
  var pvId = novoId("pv");
  W.dataLayer.push({ nf_pv_event_id: pvId, nf_vid: vid, nf_pagina: pg });
  setTimeout(function () { capi("PageView", pvId, {}); }, 800);   // espera o _fbp nascer (o pixel do GTM cria)

  // ---------- 4) WhatsApp: código invisível + clique gravado ----------
  // CÓPIA de netlify/lib/zerowidth.js do painel (marcaCurta + embutir). Conferida pelo script de prova de 09/10/2026.
  function marcaCurta(v) {
    var h = String(v || "").replace(/[^0-9a-fA-F]/g, "").slice(0, 10).toLowerCase();
    if (h.length < 10) return "";
    var bits = "";
    for (var i = 0; i < h.length; i++) { var b = parseInt(h[i], 16).toString(2); while (b.length < 4) b = "0" + b; bits += b; }
    var out = "⁠";
    for (var j = 0; j < bits.length; j++) out += bits[j] === "1" ? "‌" : "​";
    return out + "⁠";
  }
  function embutir(texto, v) {
    var t = String(texto == null || texto === "" ? "Olá!" : texto), m = marcaCurta(v);
    if (!m) return t;
    var i = t.search(/\s/);
    if (i > 0) return t.slice(0, i) + m + t.slice(i);
    if (t.length >= 2) return t.slice(0, -1) + m + t.slice(-1);
    return "Olá" + m + "! " + t;
  }
  function semCodigo(t) { return String(t || "").replace(/[​‌⁠⁣]/g, ""); }
  function ehWhats(h) { return /^https?:\/\/(api\.)?wa\.me\//i.test(h) || /^https?:\/\/(api|web)\.whatsapp\.com\/send/i.test(h); }
  function decorar(a) {
    if (!a || !a.getAttribute) return false;
    if (a.getAttribute("data-nf-wa")) return true;
    var h = a.getAttribute("href") || "";
    if (!ehWhats(h)) return false;
    var num = NUMERO, txt = "";
    var m = h.match(/wa\.me\/(\d{10,15})/i) || h.match(/[?&]phone=(\d{10,15})/i);
    if (m) num = m[1];
    var t = h.match(/[?&]text=([^&#]*)/i);
    if (t) { try { txt = decodeURIComponent(t[1].replace(/\+/g, " ")); } catch (e) { txt = ""; } }
    txt = semCodigo(txt) || MSG_PADRAO;
    a.setAttribute("data-nf-texto", txt);
    a.setAttribute("href", "https://wa.me/" + num + "?text=" + encodeURIComponent(embutir(txt, vid)));
    a.setAttribute("data-nf-wa", "1");
    return true;
  }
  function decorarTudo() { var as = D.getElementsByTagName("a"); for (var i = 0; i < as.length; i++) { try { decorar(as[i]); } catch (e) {} } }
  // o produto que o lead clicou: card do catálogo, combo, "Quero o X por R$" da mensagem, ou o nome do botão
  function produtoDo(a) {
    var dp = a.getAttribute("data-produto"); if (dp) return limpo(dp);
    var nm = a.querySelector && a.querySelector(".prod-card-name");
    if (nm) { var br = a.querySelector(".prod-card-brand"); return limpo((br ? br.textContent + " · " : "") + nm.textContent); }
    var el = a; while (el && el !== D) { if (el.className && /(^|\s)agosto-combo(\s|$)/.test(el.className)) { var ct = el.querySelector(".combo-title"); if (ct) return limpo(ct.textContent); } el = el.parentNode; }
    var q = (a.getAttribute("data-nf-texto") || "").match(/quero (?:o |a |os |as )?(.+?) por r\$/i);
    if (q && q[1].length > 2) return limpo(q[1]);
    var cls = String(a.getAttribute("class") || "").split(/\s+/);
    for (var i = 0; i < cls.length; i++) if (BOTOES[cls[i]]) return BOTOES[cls[i]];
    return limpo(a.textContent) || "botão de WhatsApp";
  }
  function origemValida() { return origem && agora - (origem.ts || 0) < DIAS_ORIGEM * 864e5 ? origem : null; }
  function preLead(produto) {
    var o = origemValida() || { utm_source: "site", utm_medium: pg };   // sem origem nenhuma: veio direto no site (selo "Site" no painel)
    enviar(PAINEL + "/pre-lead", {
      vid: vid, slug: ("site-" + pg + ":" + produto).slice(0, 120),
      utm_source: o.utm_source || null, utm_medium: o.utm_medium || null, utm_campaign: o.utm_campaign || null, utm_term: o.utm_term || null, utm_content: o.utm_content || null,
      fbclid: o.fbclid || null, gclid: o.gclid || null, fbp: lerCookie("_fbp"), fbc: fbcAtual(),
      referrer: o.referrer || ref || null, pagina_captura: location.href.split("#")[0].slice(0, 500)
    });
  }
  function evento(nome, ga4, extra) {
    var id = novoId("ev");
    W.dataLayer.push({ event: "nf_evento", nf_evento: nome, nf_evento_ga4: ga4 || nome, nf_event_id: id, nf_produto: (extra && extra.content_name) || "", nf_pagina: pg });
    capi(nome, id, extra || {});
    return id;
  }
  // captura (true): roda antes do clique seguir, e o href já sai com o código mesmo que o link tenha nascido depois
  D.addEventListener("click", function (ev) {
    try {
      var el = ev.target, a = null;
      while (el && el !== D) { if (el.tagName === "A" && el.getAttribute("href")) { a = el; break; } el = el.parentNode; }
      if (!a || !decorar(a)) return;
      var produto = produtoDo(a), id = novoId("wa");
      W.dataLayer.push({ event: "nf_evento", nf_evento: "ClickButtonWhatsapp", nf_evento_ga4: "whatsapp_click", nf_event_id: id, nf_produto: produto, nf_pagina: pg });
      preLead(produto);
      capi("ClickButtonWhatsapp", id, { content_name: produto });
    } catch (e) {}
  }, true);
  if (D.readyState === "loading") D.addEventListener("DOMContentLoaded", decorarTudo); else decorarTudo();

  // para a bio e para o teste
  W.NF = { vid: vid, pagina: pg, origem: origemValida, evento: evento, embutir: embutir, decorar: decorar, versao: "2026-10-09" };
})();
