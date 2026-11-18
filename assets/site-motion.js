/*
 * Animações do site institucional, no estilo do modelo AppNext (Framer). Só deste site; o kit gomilhasx-motion continua cuidando
 * das entradas .gx-reveal, cartões e botões.
 *   [data-split]        título que aparece palavra por palavra, subindo 20px
 *   [data-scroll-words] parágrafo cujas palavras passam de cinza para a cor do texto conforme a rolagem
 *   [data-parallax="N"] sobe N px a mais que a rolagem enquanto passa pela tela (celular do topo)
 *   [data-scroll-x="N"] desliza para o lado acompanhando a rolagem (faixa de fotos); N = px por tela rolada (negativo = esquerda)
 * Sem JavaScript ou com "reduzir movimento", tudo aparece parado e legível.
 * Em tela estreita (celular, até 767px), título palavra por palavra, parágrafo que acende e parallax ficam desligados:
 * custam estilo, layout e pintura a cada quadro e pesam no celular. No computador nada muda.
 */
(function () {
  "use strict";
  var doc = document;
  // Com "reduzir movimento": abas, sanfona e carrossel continuam funcionando no clique, mas nada se move sozinho.
  var reduce = !!(window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches);
  if (!reduce) doc.documentElement.classList.add("sm-js");
  var leve = reduce || !!(window.matchMedia && matchMedia("(max-width: 767px)").matches);

  /* Quebra o texto de um elemento em palavras, mantendo os elementos internos (como <span> e <strong>). */
  function splitWords(el, cls) {
    var words = [];
    (function walk(node) {
      Array.prototype.slice.call(node.childNodes).forEach(function (n) {
        if (n.nodeType === 3) {
          var parts = n.textContent.split(/(\s+)/), frag = doc.createDocumentFragment();
          parts.forEach(function (p) {
            if (!p) return;
            if (/^\s+$/.test(p)) { frag.appendChild(doc.createTextNode(p)); return; }
            var s = doc.createElement("span"); s.className = cls; s.textContent = p; frag.appendChild(s); words.push(s);
          });
          node.replaceChild(frag, n);
        } else if (n.nodeType === 1 && !n.matches("svg, img, br")) walk(n);
      });
    })(el);
    return words;
  }

  /* Títulos palavra por palavra, quando entram na tela */
  // o título do topo da página aparece pronto: animar o que já está na tela atrasa a primeira tela completa (Speed Index)
  var splits = Array.prototype.filter.call(doc.querySelectorAll("[data-split]"), function (el) { return !el.closest(".hero, .page-hero, .post-head"); });
  if (!leve && splits.length && "IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("sm-in"); io.unobserve(e.target); } });
    }, { rootMargin: "0px 0px -8% 0px" });
    Array.prototype.forEach.call(splits, function (el) {
      var base = parseInt(el.getAttribute("data-split"), 10) || 0;
      splitWords(el, "sm-w").forEach(function (w, i) { w.style.transitionDelay = (base + i * 45) + "ms"; });
      io.observe(el);
    });
  }

  /* Abas: trocam o texto e a tela; avançam sozinhas a cada 4,5 s até a pessoa clicar */
  Array.prototype.forEach.call(doc.querySelectorAll("[data-tabs]"), function (box) {
    var tabs = box.querySelectorAll('[role="tab"]');
    var texts = box.querySelectorAll(".tab-text p, .pow-text p");
    var shots = box.querySelectorAll(".tab-phone .phone img");
    var cur = 0, timer = null;
    function show(i) {
      cur = i;
      Array.prototype.forEach.call(tabs, function (t, k) { t.setAttribute("aria-selected", String(k === i)); });
      Array.prototype.forEach.call(texts, function (t, k) { t.classList.toggle("on", k === i); });
      Array.prototype.forEach.call(shots, function (t, k) { t.classList.toggle("on", k === i); });
    }
    function auto() { if (!reduce) timer = setInterval(function () { show((cur + 1) % tabs.length); }, 4500); }
    Array.prototype.forEach.call(tabs, function (t, k) { t.addEventListener("click", function () { clearInterval(timer); show(k); }); });
    auto();
  });

  /* Sanfona: abre um item por vez; a barra dourada enche e passa para o próximo */
  Array.prototype.forEach.call(doc.querySelectorAll("[data-acc]"), function (acc) {
    var items = acc.querySelectorAll(".acc-item"), cur = 0, manual = false;
    function open(i) {
      cur = i;
      Array.prototype.forEach.call(items, function (it, k) { it.classList.toggle("open", k === i); it.querySelector("button").setAttribute("aria-expanded", String(k === i)); });
    }
    Array.prototype.forEach.call(items, function (it, k) {
      it.querySelector("button").addEventListener("click", function () { manual = true; open(k); });
      it.querySelector(".bar i").addEventListener("animationend", function () { if (!manual && k === cur) open((cur + 1) % items.length); });
    });
  });

  /* Perguntas: abre deslizando, a resposta aparece suave, uma aberta por vez (como no modelo) */
  Array.prototype.forEach.call(doc.querySelectorAll(".faq"), function (faq) {
    var items = Array.prototype.slice.call(faq.querySelectorAll("details"));
    items.forEach(function (d) {
      var sum = d.querySelector("summary"), wrap = doc.createElement("div");
      wrap.className = "resp";
      while (sum.nextSibling) wrap.appendChild(sum.nextSibling);
      d.appendChild(wrap);
      function anima(abrir) {
        if (reduce) { d.open = abrir; return; }
        var de = abrir ? 0 : wrap.scrollHeight;
        if (abrir) { d.open = true; d.classList.add("abrindo"); }
        else d.classList.add("fechando");
        var ate = abrir ? wrap.scrollHeight : 0;
        wrap.style.height = de + "px";
        wrap.getBoundingClientRect();
        wrap.style.transition = "height .45s cubic-bezier(.22,.61,.36,1)";
        requestAnimationFrame(function () { d.classList.remove("abrindo"); wrap.style.height = ate + "px"; });
        clearTimeout(d._t);
        d._t = setTimeout(function () { wrap.style.transition = ""; wrap.style.height = ""; d.classList.remove("fechando"); if (!abrir) d.open = false; }, 460);
      }
      sum.addEventListener("click", function (e) {
        e.preventDefault();
        var abrir = !d.open || d.classList.contains("fechando");
        if (abrir) items.forEach(function (o) { if (o !== d && o.open && !o.classList.contains("fechando")) o._fecha(); });
        anima(abrir);
      });
      d._fecha = function () { anima(false); };
    });
    if (!("IntersectionObserver" in window)) items.forEach(function (d) { d.classList.add("sm-in"); });
    else if (!reduce) {
      var io2 = new IntersectionObserver(function (es) {
        es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("sm-in"); io2.unobserve(e.target); } });
      }, { rootMargin: "0px 0px -6% 0px" });
      items.forEach(function (d, i) { d.style.transitionDelay = (i % 8) * 70 + "ms"; d.addEventListener("transitionend", function f(ev) { if (ev.propertyName === "transform") { d.style.transitionDelay = ""; d.removeEventListener("transitionend", f); } }); io2.observe(d); });
    }
  });

  /* Carrossel de telas */
  Array.prototype.forEach.call(doc.querySelectorAll("[data-car]"), function (box) {
    var phones = box.querySelectorAll(".car .phone"), cap = box.querySelector(".car-cap"), btns = box.querySelectorAll(".car-nav button");
    var caps = ["CRM Milhas com cada negociação por etapa e o lucro de cada uma", "Painel com o saldo e o custo do milheiro de cada programa", "Central de Cartões com faturas e pontos a receber"];
    var cur = 1, timer;
    function show(i) { cur = (i + phones.length) % phones.length; Array.prototype.forEach.call(phones, function (p, k) { p.classList.toggle("on", k === cur); }); if (cap) cap.textContent = caps[cur] || ""; }
    btns[0].addEventListener("click", function () { clearInterval(timer); show(cur - 1); });
    btns[1].addEventListener("click", function () { clearInterval(timer); show(cur + 1); });
    if (!reduce) timer = setInterval(function () { show(cur + 1); }, 4000);
  });

  /* Faixas e enfeites que se mexem sem parar (letreiros, ticker, barras, selos): parados enquanto estão fora da tela */
  if (!reduce && "IntersectionObserver" in window) {
    var io3 = new IntersectionObserver(function (es) {
      es.forEach(function (e) { e.target.classList.toggle("sm-pausa", !e.isIntersecting); });
    }, { rootMargin: "100px 0px" });
    Array.prototype.forEach.call(doc.querySelectorAll(".ticker, .logos, .strip, .results, .dark-card .bars, .cta2 .r"), function (el) { io3.observe(el); });
  }

  /* Parágrafo que acende com a rolagem */
  if (reduce) return;
  var scrollTexts = leve ? [] : Array.prototype.map.call(doc.querySelectorAll("[data-scroll-words]"), function (el) {
    return { el: el, words: splitWords(el, "sm-sw") };
  });
  var parallax = leve ? [] : Array.prototype.slice.call(doc.querySelectorAll("[data-parallax]"));
  var sliders = Array.prototype.slice.call(doc.querySelectorAll("[data-scroll-x]"));
  var stacks = Array.prototype.slice.call(doc.querySelectorAll("[data-stack]"));

  var queued = false;
  function frame() {
    queued = false;
    var vh = innerHeight;
    scrollTexts.forEach(function (t) {
      var r = t.el.getBoundingClientRect();
      // começa quando o topo do parágrafo chega a 85% da tela e termina quando o fim chega a 45%
      var start = vh * 0.85, end = vh * 0.45;
      var p = (start - r.top) / ((start - end) + r.height);
      p = Math.max(0, Math.min(1, p));
      var lit = p * t.words.length;
      t.words.forEach(function (w, i) { var o = Math.max(0, Math.min(1, lit - i)); w.style.opacity = (0.55 + 0.45 * o).toFixed(3); });
    });
    parallax.forEach(function (el) {
      var r = el.parentNode.getBoundingClientRect(), n = parseFloat(el.getAttribute("data-parallax")) || 80;
      var p = Math.max(0, Math.min(1, (vh - r.top) / (vh + r.height)));
      el.style.setProperty("--sm-y", ((1 - p * 1.6) * n).toFixed(1) + "px");
    });
    stackFrame(vh);
    sliders.forEach(function (el) {
      var r = el.getBoundingClientRect(), n = parseFloat(el.getAttribute("data-scroll-x")) || -120;
      if (r.bottom < -200 || r.top > vh + 200) return;
      el.style.transform = "translate3d(" + (((vh - r.top) / vh) * n).toFixed(1) + "px,0,0)";
    });
  }
  function stackFrame(vh) {
    stacks.forEach(function (st) {
      var sec = st.closest(".stack-sec"), r = sec.getBoundingClientRect();
      var p = Math.max(0, Math.min(1, -r.top / (r.height - vh)));
      var imgs = st.querySelectorAll("img"), n = imgs.length;
      Array.prototype.forEach.call(imgs, function (im, i) {
        var a = i / n, b = (i + 1) / n, q = Math.max(0, Math.min(1, (p - a) / (b - a)));
        if (i === 0) q = Math.max(q, 1);
        var e = 1 - Math.pow(1 - q, 3);
        im.style.setProperty("--y", ((1 - e) * vh * 1.1).toFixed(1) + "px");
      });
    });
  }
  function request() { if (!queued) { queued = true; requestAnimationFrame(frame); } }
  if (scrollTexts.length || parallax.length || sliders.length || stacks.length) {
    addEventListener("scroll", request, { passive: true });
    addEventListener("resize", request);
    frame();
  }
})();
