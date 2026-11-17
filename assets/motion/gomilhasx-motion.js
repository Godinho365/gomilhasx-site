/*!
 * GOMilhasX Motion Kit v1.0.0 (ver gomilhasx-motion.css). JavaScript puro, sem dependências, ~4 KB.
 * - .gx-reveal entra ao aparecer na tela; .gx-stage[data-gx-bg] ganha o fundo (partículas em canvas + feixes);
 * - [data-gx-count] conta até o número (use só com dado real; o texto do servidor fica se não houver animação).
 * Respeita prefers-reduced-motion, pausa fora da tela e com a aba oculta, e usa menos partículas no celular.
 */
(function () {
  "use strict";
  var doc = document, root = doc.documentElement;
  root.classList.add("gx-js");
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var hasIO = "IntersectionObserver" in window, sweepBound = false;

  /* ---------- entrada das seções ---------- */
  function reveal() {
    var els = doc.querySelectorAll(".gx-reveal:not(.gx-in)");
    if (reduce || !hasIO) { els.forEach(function (el) { el.classList.add("gx-in"); }); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("gx-in"); io.unobserve(e.target); } });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    els.forEach(function (el) { io.observe(el); });
    // rolagem rápida ou salto por âncora: o que já passou da tela também aparece
    var queued = false;
    function sweep() {
      queued = false;
      doc.querySelectorAll(".gx-reveal:not(.gx-in)").forEach(function (el) {
        if (el.getBoundingClientRect().top < window.innerHeight * 0.92) { el.classList.add("gx-in"); io.unobserve(el); }
      });
    }
    if (!sweepBound) { sweepBound = true; window.addEventListener("scroll", function () { if (!queued) { queued = true; requestAnimationFrame(sweep); } }, { passive: true }); }
    sweep();
  }

  /* ---------- contadores (dados reais vindos do servidor) ---------- */
  function counters() {
    var els = doc.querySelectorAll("[data-gx-count]:not([data-gx-done])");
    els.forEach(function (el) { el.setAttribute("data-gx-done", "1"); });
    if (reduce || !hasIO) return; // fica o texto que o servidor escreveu
    var fmt = new Intl.NumberFormat("pt-BR");
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        io.unobserve(e.target);
        var el = e.target, end = Number(el.getAttribute("data-gx-count")), original = el.textContent;
        if (!isFinite(end) || end <= 0) return;
        var pre = el.getAttribute("data-gx-prefix") || "", suf = el.getAttribute("data-gx-suffix") || "";
        var t0 = performance.now(), dur = 1200;
        (function step(t) {
          var k = Math.min(1, (t - t0) / dur), v = Math.round(end * (1 - Math.pow(1 - k, 3)));
          el.textContent = pre + fmt.format(v) + suf;
          if (k < 1) requestAnimationFrame(step); else el.textContent = original;
        })(t0);
      });
    }, { threshold: 0.4 });
    els.forEach(function (el) { io.observe(el); });
  }

  /* ---------- fundo: partículas + feixes ---------- */
  function stage(el) {
    if (el.getAttribute("data-gx-ready")) return; // já montado (navegação sem recarregar)
    el.setAttribute("data-gx-ready", "1");
    var variant = el.getAttribute("data-gx-bg") || "network";
    var bg = doc.createElement("div");
    bg.className = "gx-bg"; bg.setAttribute("data-variant", variant); bg.setAttribute("aria-hidden", "true");
    for (var i = 0; i < 4; i++) { var beam = doc.createElement("span"); beam.className = "gx-beam"; bg.appendChild(beam); }
    el.insertBefore(bg, el.firstChild);
    if (reduce) return;

    var canvas = doc.createElement("canvas"); bg.appendChild(canvas);
    var ctx = canvas.getContext("2d"); if (!ctx) return;
    var dpr = Math.min(window.devicePixelRatio || 1, 1.5), w = 0, h = 0, pts = [], running = false, visible = true, raf = 0;
    var light = (function () { // tema claro: partículas mais suaves
      var c = getComputedStyle(doc.body).backgroundColor.match(/\d+/g);
      return c ? (0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]) > 160 : false;
    })();
    var alpha = light ? 0.35 : 0.6, link = variant === "grid" ? 90 : 130, speed = variant === "flow" ? 0.35 : 0.12;

    function size() {
      var r = el.getBoundingClientRect(); w = r.width; h = r.height;
      canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      var n = w < 640 ? 16 : w < 1024 ? 28 : 44; // menos no celular
      pts = [];
      for (var i = 0; i < n; i++) pts.push({ x: Math.random() * w, y: Math.random() * h, vx: (variant === "flow" ? 1 : Math.random() - 0.5) * speed, vy: (Math.random() - 0.5) * speed, r: Math.random() * 1.4 + 0.6 });
    }
    function frame() {
      ctx.clearRect(0, 0, w, h);
      for (var i = 0; i < pts.length; i++) {
        var p = pts[i]; p.x += p.vx; p.y += p.vy;
        if (p.x < -10) p.x = w + 10; else if (p.x > w + 10) p.x = -10;
        if (p.y < -10) p.y = h + 10; else if (p.y > h + 10) p.y = -10;
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 6.283); ctx.fillStyle = "rgba(34,211,238," + alpha + ")"; ctx.fill();
        for (var j = i + 1; j < pts.length; j++) { // conexões (rede de rotas)
          var q = pts[j], dx = p.x - q.x, dy = p.y - q.y, d = dx * dx + dy * dy;
          if (d < link * link) {
            ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y);
            ctx.strokeStyle = "rgba(34,211,238," + (alpha * 0.35 * (1 - Math.sqrt(d) / link)) + ")"; ctx.lineWidth = 1; ctx.stroke();
          }
        }
      }
      raf = requestAnimationFrame(frame);
    }
    function play() { if (!running && visible && !doc.hidden) { running = true; raf = requestAnimationFrame(frame); } }
    function pause() { running = false; cancelAnimationFrame(raf); }
    size();
    if (hasIO) new IntersectionObserver(function (e) { visible = e[0].isIntersecting; visible ? play() : pause(); }).observe(el);
    doc.addEventListener("visibilitychange", function () { doc.hidden ? pause() : play(); });
    var t; window.addEventListener("resize", function () { clearTimeout(t); t = setTimeout(size, 200); }, { passive: true });
    play();
  }

  function init() {
    doc.querySelectorAll(".gx-stage[data-gx-bg]").forEach(stage);
    reveal(); counters();
  }
  if (doc.readyState === "loading") doc.addEventListener("DOMContentLoaded", init); else init();
  // Páginas que trocam de conteúdo sem recarregar (Next.js) chamam GOMilhasXMotion.refresh() depois de cada troca
  window.GOMilhasXMotion = { refresh: init };
})();
