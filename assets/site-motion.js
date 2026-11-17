/*
 * Animações do site institucional, no estilo do modelo AppNext (Framer). Só deste site; o kit gomilhasx-motion continua cuidando
 * das entradas .gx-reveal, cartões e botões.
 *   [data-split]        título que aparece palavra por palavra, subindo 20px
 *   [data-scroll-words] parágrafo cujas palavras passam de cinza para a cor do texto conforme a rolagem
 *   [data-parallax="N"] sobe N px a mais que a rolagem enquanto passa pela tela (celular do topo)
 *   [data-scroll-x="N"] desliza para o lado acompanhando a rolagem (faixa de fotos); N = px por tela rolada (negativo = esquerda)
 * Sem JavaScript ou com "reduzir movimento", tudo aparece parado e legível.
 */
(function () {
  "use strict";
  var doc = document;
  if (window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  doc.documentElement.classList.add("sm-js");

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
  var splits = doc.querySelectorAll("[data-split]");
  if (splits.length && "IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("sm-in"); io.unobserve(e.target); } });
    }, { rootMargin: "0px 0px -8% 0px" });
    Array.prototype.forEach.call(splits, function (el) {
      var base = parseInt(el.getAttribute("data-split"), 10) || 0;
      splitWords(el, "sm-w").forEach(function (w, i) { w.style.transitionDelay = (base + i * 45) + "ms"; });
      io.observe(el);
    });
  }

  /* Parágrafo que acende com a rolagem */
  var scrollTexts = Array.prototype.map.call(doc.querySelectorAll("[data-scroll-words]"), function (el) {
    return { el: el, words: splitWords(el, "sm-sw") };
  });
  var parallax = Array.prototype.slice.call(doc.querySelectorAll("[data-parallax]"));
  var sliders = Array.prototype.slice.call(doc.querySelectorAll("[data-scroll-x]"));

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
      t.words.forEach(function (w, i) { var o = Math.max(0, Math.min(1, lit - i)); w.style.opacity = (0.2 + 0.8 * o).toFixed(3); });
    });
    parallax.forEach(function (el) {
      var r = el.parentNode.getBoundingClientRect(), n = parseFloat(el.getAttribute("data-parallax")) || 80;
      var p = Math.max(0, Math.min(1, (vh - r.top) / (vh + r.height)));
      el.style.setProperty("--sm-y", ((1 - p * 1.6) * n).toFixed(1) + "px");
    });
    sliders.forEach(function (el) {
      var r = el.getBoundingClientRect(), n = parseFloat(el.getAttribute("data-scroll-x")) || -120;
      if (r.bottom < -200 || r.top > vh + 200) return;
      el.style.transform = "translate3d(" + (((vh - r.top) / vh) * n).toFixed(1) + "px,0,0)";
    });
  }
  function request() { if (!queued) { queued = true; requestAnimationFrame(frame); } }
  if (scrollTexts.length || parallax.length || sliders.length) {
    addEventListener("scroll", request, { passive: true });
    addEventListener("resize", request);
    frame();
  }
})();
