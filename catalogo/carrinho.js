/* NF Suplementos · carrinho do catálogo (24/11/2026)
   O pedido não é cobrado aqui: vira uma mensagem pronta para o WhatsApp da loja.
   O preço e o nome saem do próprio card (data-preco em centavos, data-nome), gerado do tools/catalogo/produtos.json.
   O link de envio é um <a> de wa.me: o /js/nf-rastreio.js põe o código invisível do visitante e grava o clique no painel,
   com o resumo do pedido em data-produto. Por isso, a cada mudança, o href é refeito e o data-nf-wa é apagado. */
(function () {
  "use strict";
  var D = document, W = window, NUMERO = "5517997587526", CHAVE = "nf_pedido_v1";
  var $ = function (id) { return D.getElementById(id); };
  var prod = {};                                   // id -> {nome, preco, img}
  var cards = D.querySelectorAll(".p[data-id]");
  for (var i = 0; i < cards.length; i++) {
    var c = cards[i], id = c.getAttribute("data-id");
    if (!prod[id]) { var im = c.querySelector("img"); prod[id] = { nome: c.getAttribute("data-nome"), preco: parseInt(c.getAttribute("data-preco"), 10) || 0, img: im ? im.getAttribute("src") : "" }; }
  }
  var pedido = {}, ordem = [];                     // id -> quantidade; ordem em que entrou
  try {
    var salvo = JSON.parse(W.localStorage.getItem(CHAVE) || "null");
    if (salvo && salvo.itens) for (var k = 0; k < salvo.itens.length; k++) {
      var it = salvo.itens[k];
      if (prod[it[0]] && it[1] > 0) { pedido[it[0]] = Math.min(99, it[1] | 0); ordem.push(it[0]); }   // produto que saiu do catálogo some do pedido
    }
    if (salvo && salvo.obs) $("obs").value = String(salvo.obs).slice(0, 200);
  } catch (e) {}

  function brl(c) { var r = Math.floor(c / 100), ct = c % 100; return "R$ " + String(r).replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "," + (ct < 10 ? "0" : "") + ct; }
  function guardar() { try { W.localStorage.setItem(CHAVE, JSON.stringify({ itens: ordem.map(function (id) { return [id, pedido[id]]; }), obs: $("obs").value })); } catch (e) {} }
  function contar() { var n = 0, t = 0; ordem.forEach(function (id) { n += pedido[id]; t += pedido[id] * prod[id].preco; }); return { n: n, t: t }; }

  function mudar(id, delta, origem) {
    if (!prod[id]) return;
    var q = (pedido[id] || 0) + delta;
    if (q <= 0) { delete pedido[id]; ordem = ordem.filter(function (x) { return x !== id; }); }
    else { if (!pedido[id]) ordem.push(id); pedido[id] = Math.min(99, q); }
    guardar(); pintar();
    if (delta > 0 && origem) pulsar(origem);
    if (delta > 0) pulsar($("barra"));
  }
  function pulsar(el) { if (!el) return; el.classList.remove("pulso"); void el.offsetWidth; el.classList.add("pulso"); }

  function mensagem() {
    var s = contar(), l = ["Olá! Quero fazer este pedido pelo catálogo:", ""];
    ordem.forEach(function (id) { l.push("▪ " + pedido[id] + "x " + prod[id].nome + " · " + brl(pedido[id] * prod[id].preco)); });
    l.push("", "*Total: " + brl(s.t) + "*");
    var o = $("obs").value.replace(/\s+/g, " ").replace(/^\s+|\s+$/g, "");
    if (o) l.push("Obs.: " + o);
    return l.join("\n");
  }
  function resumo() { return ("pedido: " + ordem.map(function (id) { return pedido[id] + "x " + prod[id].nome; }).join(" + ")).slice(0, 88); }

  function pintar() {
    var s = contar();
    // cada card (o mesmo produto pode estar em Ofertas e na categoria)
    for (var i = 0; i < cards.length; i++) {
      var q = pedido[cards[i].getAttribute("data-id")] || 0, box = cards[i].querySelector("[data-qtd]");
      box.classList.toggle("tem", q > 0);
      box.querySelector(".menos").hidden = !q;
      var n = box.querySelector(".n"); n.hidden = !q; n.textContent = q;
    }
    // barra
    $("barra").hidden = !s.n;
    $("barra-n").textContent = s.n;
    $("barra-v").textContent = brl(s.t);
    // lista
    var ul = $("itens"); ul.textContent = "";
    ordem.forEach(function (id) {
      var p = prod[id], li = D.createElement("li");
      li.innerHTML = '<span class="mini"><img alt="" loading="lazy"></span><span class="nm"></span><span class="vl"></span><span class="un"></span>' +
        '<span class="qtd tem"><button type="button" class="menos">−</button><span class="n"></span><button type="button" class="mais">+</button></span>';
      li.querySelector("img").src = p.img;
      li.querySelector(".nm").textContent = p.nome;
      li.querySelector(".vl").textContent = brl(pedido[id] * p.preco);
      li.querySelector(".un").textContent = brl(p.preco) + " cada";
      li.querySelector(".n").textContent = pedido[id];
      li.querySelector(".menos").setAttribute("aria-label", "Tirar um " + p.nome);
      li.querySelector(".mais").setAttribute("aria-label", "Mais um " + p.nome);
      li.querySelector(".menos").onclick = function () { mudar(id, -1); };
      li.querySelector(".mais").onclick = function () { mudar(id, 1); };
      ul.appendChild(li);
    });
    $("pedido-vazio").hidden = !!s.n;
    $("obs-caixa").hidden = !s.n;
    $("pedido-pe").hidden = !s.n;
    $("total").textContent = brl(s.t);
    var a = $("enviar");
    a.removeAttribute("data-nf-wa"); a.removeAttribute("data-nf-texto");
    a.setAttribute("href", "https://wa.me/" + NUMERO + "?text=" + encodeURIComponent(mensagem()));
    a.setAttribute("data-produto", resumo());
  }

  // adicionar e tirar nos cards
  D.addEventListener("click", function (ev) {
    var b = ev.target.closest ? ev.target.closest(".p .mais, .p .menos") : null;
    if (!b) return;
    var card = b.closest(".p");
    mudar(card.getAttribute("data-id"), b.classList.contains("mais") ? 1 : -1, b.parentNode);
  });

  // abrir e fechar o pedido
  var antes = null;
  function abrir() { antes = D.activeElement; $("fundo").hidden = false; $("pedido").hidden = false; D.body.classList.add("aberto"); $("fechar").focus(); }
  function fechar() { $("fundo").hidden = true; $("pedido").hidden = true; D.body.classList.remove("aberto"); if (antes && antes.focus) antes.focus(); }
  $("barra").onclick = abrir; $("fechar").onclick = fechar; $("fundo").onclick = fechar;
  D.addEventListener("keydown", function (e) { if (e.key === "Escape" && !$("pedido").hidden) fechar(); });
  $("obs").addEventListener("input", function () { guardar(); pintar_link(); });
  function pintar_link() { var a = $("enviar"); a.removeAttribute("data-nf-wa"); a.removeAttribute("data-nf-texto"); a.setAttribute("href", "https://wa.me/" + NUMERO + "?text=" + encodeURIComponent(mensagem())); }
  $("limpar").onclick = function () { pedido = {}; ordem = []; $("obs").value = ""; guardar(); pintar(); };

  // busca
  var inp = $("busca"), secs = D.querySelectorAll("main .cat"), info = $("busca-info"), vazio = $("busca-vazio");
  function semAcento(s) { return s.toLowerCase().normalize ? s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "") : s.toLowerCase(); }
  var indice = []; D.querySelectorAll("main .cat .p").forEach(function (c) { indice.push([c, semAcento(c.getAttribute("data-busca") || "")]); });
  function buscar() {
    var termos = semAcento(inp.value).split(/\s+/).filter(Boolean), achou = 0;
    D.body.classList.toggle("buscando", termos.length > 0);
    indice.forEach(function (x) { var ok = termos.every(function (t) { return x[1].indexOf(t) >= 0; }); x[0].hidden = !ok; if (ok) achou++; });
    secs.forEach(function (s) { s.hidden = !s.querySelector(".p:not([hidden])"); });
    info.hidden = !termos.length || !achou; vazio.hidden = !termos.length || achou > 0;
    if (termos.length && achou) info.textContent = achou + (achou === 1 ? " produto encontrado" : " produtos encontrados");
  }
  inp.addEventListener("input", buscar);
  inp.addEventListener("keydown", function (e) { if (e.key === "Enter") { inp.blur(); $("catalogo").scrollIntoView(); } });

  // categoria ativa na barra de categorias
  var chips = D.querySelectorAll(".chip"), alvos = [];
  chips.forEach(function (c) { var el = D.getElementById(c.getAttribute("href").slice(1)); if (el) alvos.push([c, el]); });
  var marcando = false;
  W.addEventListener("scroll", function () {
    if (marcando) return; marcando = true;
    W.requestAnimationFrame(function () {
      var atual = null, y = 130;
      alvos.forEach(function (a) { if (!a[1].hidden && a[1].getBoundingClientRect().top <= y) atual = a[0]; });
      chips.forEach(function (c) { var on = c === atual; if (on && !c.classList.contains("ativo")) { var p = c.parentNode; p.scrollLeft = c.offsetLeft - (p.clientWidth - c.offsetWidth) / 2; } c.classList.toggle("ativo", on); });
      marcando = false;
    });
  }, { passive: true });

  pintar();
})();
