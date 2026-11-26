// Aviso de cookies e Google Tag Manager só com permissão (LGPD). Sem escolha guardada, nada do Google é pedido.
// A escolha fica neste navegador (localStorage "gn_consent" e cookie first-party "gn_consent", 12 meses, SameSite=Lax),
// com versão: se o texto ou as categorias mudarem, VERSAO sobe e o aviso aparece de novo. O Umami (/stats/) não usa
// cookie e não depende desta escolha. "Preferências de cookies" no rodapé ([data-cookies]) reabre as opções.
(function () {
  "use strict";
  var VERSAO = 1, CHAVE = "gn_consent", DIAS = 365, GTM = "GTM-N742HXVS";
  var POLITICA = "https://manager.gonorte.com.br/privacidade";
  var gtmCarregado = false, box = null, abriuPor = null;

  function ler() {
    var bruto = null;
    try { bruto = localStorage.getItem(CHAVE); } catch (e) {}
    if (!bruto) {
      var m = document.cookie.match(/(?:^|;\s*)gn_consent=([^;]*)/);
      if (m) { try { bruto = decodeURIComponent(m[1]); } catch (e) {} }
    }
    try {
      var c = JSON.parse(bruto || "null");
      if (c && c.v === VERSAO && typeof c.a === "boolean" && typeof c.m === "boolean") return c;
    } catch (e) {}
    return null;
  }

  function gravar(a, m) {
    var c = { v: VERSAO, a: a, m: m, t: Date.now() }, txt = JSON.stringify(c);
    try { localStorage.setItem(CHAVE, txt); } catch (e) {}
    try {
      document.cookie = CHAVE + "=" + encodeURIComponent(txt) + "; Max-Age=" + DIAS * 86400 + "; Path=/; SameSite=Lax" +
        (location.protocol === "https:" ? "; Secure" : "");
    } catch (e) {}
    return c;
  }

  function gtag() { window.dataLayer.push(arguments); }

  function sinais(c) {
    var mkt = c.m ? "granted" : "denied";
    return { analytics_storage: c.a ? "granted" : "denied", ad_storage: mkt, ad_user_data: mkt, ad_personalization: mkt };
  }

  // Carrega o GTM uma vez, já com o modo de consentimento: padrão tudo negado e, em seguida, o que a pessoa permitiu
  function carregarGtm(c) {
    if (gtmCarregado) return;
    gtmCarregado = true;
    window.dataLayer = window.dataLayer || [];
    gtag("consent", "default", { ad_storage: "denied", analytics_storage: "denied", ad_user_data: "denied", ad_personalization: "denied" });
    gtag("consent", "update", sinais(c));
    window.dataLayer.push({ "gtm.start": Date.now(), event: "gtm.js" });
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtm.js?id=" + GTM;
    document.head.appendChild(s);
  }

  // Permissão retirada: o Google é avisado (consent update denied) e os cookies dele neste site são apagados
  function apagarCookiesGoogle() {
    var dominios = ["", "; domain=" + location.hostname, "; domain=." + location.hostname.replace(/^www\./, "")];
    document.cookie.split(";").forEach(function (par) {
      var nome = par.split("=")[0].trim();
      if (!/^(_ga|_gid|_gat|_gcl|_gac)/.test(nome)) return;
      dominios.forEach(function (d) { document.cookie = nome + "=; Max-Age=0; Path=/" + d; });
    });
  }

  function aplicar(c, antes) {
    if (c.a || c.m) {
      if (gtmCarregado) gtag("consent", "update", sinais(c)); else carregarGtm(c);
    } else if (gtmCarregado) {
      gtag("consent", "update", sinais(c));
    }
    if (antes && ((antes.a && !c.a) || (antes.m && !c.m))) apagarCookiesGoogle();
  }

  function montar() {
    box = document.createElement("section");
    box.className = "ck";
    box.id = "aviso-cookies";
    box.setAttribute("role", "region");
    box.setAttribute("aria-label", "Aviso de cookies");
    box.hidden = true;
    box.innerHTML =
      '<div class="ck-opcoes" id="ck-opcoes" hidden>' +
        '<p class="ck-tit">Escolha o que permitir</p>' +
        '<label class="ck-op"><input type="checkbox" name="ck-a"><span><b>Analíticos</b><small>Google Analytics, pelo Google Tag Manager: quantas pessoas visitam e quais páginas leem.</small></span></label>' +
        '<label class="ck-op"><input type="checkbox" name="ck-m"><span><b>Marketing</b><small>Medir anúncios do Google e mostrar anúncios mais relevantes.</small></span></label>' +
        '<p class="ck-nota">Sem cookie e sempre ligada: a contagem de visitas no nosso próprio servidor, sem dado pessoal.</p>' +
        '<button type="button" class="ck-btn ck-salvar" data-ck="salvar">Salvar escolha</button>' +
      '</div>' +
      '<div class="ck-linha">' +
        '<p class="ck-txt">Usamos cookies do Google para medir visitas, só com a sua permissão. ' +
          '<a href="' + POLITICA + '">Saiba mais</a> · ' +
          '<button type="button" class="ck-link" data-ck="personalizar" aria-expanded="false" aria-controls="ck-opcoes">Personalizar</button></p>' +
        '<div class="ck-acoes">' +
          '<button type="button" class="ck-btn" data-ck="recusar">Recusar</button>' +
          '<button type="button" class="ck-btn" data-ck="aceitar">Aceitar</button>' +
        '</div>' +
      '</div>';
    // No começo do <body>: quem navega pelo teclado chega ao aviso logo no início (na tela ele fica fixo embaixo)
    document.body.insertBefore(box, document.body.firstChild);
    box.addEventListener("click", function (ev) {
      var b = ev.target.closest && ev.target.closest("[data-ck]");
      if (!b) return;
      var acao = b.getAttribute("data-ck");
      if (acao === "personalizar") return opcoes(box.querySelector(".ck-opcoes").hidden);
      if (acao === "aceitar") return escolher(true, true);
      if (acao === "recusar") return escolher(false, false);
      if (acao === "salvar") return escolher(box.querySelector("[name=ck-a]").checked, box.querySelector("[name=ck-m]").checked);
    });
    box.addEventListener("keydown", function (ev) { if (ev.key === "Escape" && !box.querySelector(".ck-opcoes").hidden) opcoes(false); });
  }

  function opcoes(abrir) {
    var painel = box.querySelector(".ck-opcoes"), btn = box.querySelector("[data-ck=personalizar]");
    painel.hidden = !abrir;
    btn.setAttribute("aria-expanded", String(abrir));
    if (abrir) box.querySelector("[name=ck-a]").focus(); else btn.focus();
    medir();
  }

  // Altura do aviso em --ck-h: o botão do WhatsApp sobe para não ficar por baixo
  function medir() { document.documentElement.style.setProperty("--ck-h", box && !box.hidden ? box.offsetHeight + "px" : "0px"); }

  function mostrar(comOpcoes) {
    if (!box) montar();
    var c = ler();
    box.querySelector("[name=ck-a]").checked = !!(c && c.a);
    box.querySelector("[name=ck-m]").checked = !!(c && c.m);
    box.hidden = false;
    document.documentElement.classList.add("ck-aberto");
    if (comOpcoes) opcoes(true); else medir();
  }

  function fechar() {
    var focoDentro = box.contains(document.activeElement);
    box.hidden = true;
    document.documentElement.classList.remove("ck-aberto");
    medir();
    if (focoDentro && abriuPor) abriuPor.focus({ preventScroll: true });
    abriuPor = null;
  }

  function escolher(a, m) {
    var antes = ler();
    aplicar(gravar(a, m), antes);
    fechar();
  }

  function iniciar() {
    var c = ler();
    if (c) aplicar(c, null); else mostrar(false);
    Array.prototype.forEach.call(document.querySelectorAll("[data-cookies]"), function (el) {
      el.addEventListener("click", function (ev) { ev.preventDefault(); abriuPor = el; mostrar(true); });
    });
    window.addEventListener("resize", medir);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", iniciar); else iniciar();
})();
