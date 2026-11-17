// Modal "Acessar o Balcão": qualquer link com data-lead abre o formulário (sem JavaScript, o link segue para o Balcão).
// Os dados vão para /api/lead (o Caddy repassa ao GO Balcão, no mesmo domínio): nada de cookie, nada de dado
// pessoal em URL ou em evento. Eventos de métrica: só o nome do evento, o botão clicado e a origem da campanha.
(function () {
  "use strict";
  var dlg = document.getElementById("lead-dlg");
  if (!dlg || typeof dlg.showModal !== "function") return; // navegador antigo: os links levam direto ao Balcão
  var form = document.getElementById("lead-form"), step1 = document.getElementById("lead-step1"), step2 = document.getElementById("lead-step2");
  var btn = form.querySelector("button[type=submit]"), alertBox = document.getElementById("lead-alert");
  var phone = form.elements.whatsapp, badge = document.getElementById("lead-badge"), sub = document.getElementById("lead-sub");
  var openedAt = 0, cta = "", lastFocus = null, sending = false;

  // Origem: utm_* da primeira página vista nesta aba e o domínio de quem mandou a pessoa ao site
  var KEY = "gmx_origem", origin = {};
  try { origin = JSON.parse(sessionStorage.getItem(KEY) || "{}"); } catch (e) { origin = {}; }
  var q = new URLSearchParams(location.search), utm = {};
  ["source", "medium", "campaign", "term", "content"].forEach(function (k) { var v = q.get("utm_" + k); if (v) utm[k] = v.slice(0, 80); });
  if (Object.keys(utm).length) origin.utm = utm;
  if (!origin.referrer && document.referrer) {
    try { var host = new URL(document.referrer).hostname; if (host && host !== location.hostname) origin.referrer = "https://" + host; } catch (e) {}
  }
  try { sessionStorage.setItem(KEY, JSON.stringify(origin)); } catch (e) {}
  var source = (origin.utm && origin.utm.source) || "";

  function track(e) {
    try {
      fetch("/api/lead/evento", { method: "POST", body: JSON.stringify({ e: e, cta: cta, utm: source }), keepalive: true,
        headers: { "Content-Type": "text/plain" }, credentials: "omit" }).catch(function () {});
    } catch (x) {}
  }

  // Texto da oferta: lido do Balcão (muda pelo painel, sem publicar o site de novo)
  var offerLoaded = false;
  function loadOffer() {
    if (offerLoaded) return;
    offerLoaded = true;
    fetch("/api/lead/oferta", { credentials: "omit" }).then(function (r) { return r.ok ? r.json() : null; }).then(function (o) {
      if (o && o.ativa) {
        badge.querySelector("span").textContent = "Grátis: " + o.plano + " · " + o.periodo;
        badge.hidden = false;
        sub.textContent = "Cadastre-se e receba agora o seu convite para o Telegram. A verificação de identidade do Balcão continua valendo para todos.";
      }
    }).catch(function () {});
  }

  // Máscara do WhatsApp: (11) 91234-5678 ou (11) 3333-4444
  function mask(v) {
    var d = v.replace(/\D/g, "");
    if (d.length > 11 && d.indexOf("55") === 0) d = d.slice(2);
    d = d.slice(0, 11);
    if (d.length <= 2) return d.length ? "(" + d : "";
    var rest = d.slice(2), cut = d.length === 11 ? 5 : 4;
    return "(" + d.slice(0, 2) + ") " + (rest.length > cut ? rest.slice(0, cut) + "-" + rest.slice(cut) : rest);
  }
  phone.addEventListener("input", function () { phone.value = mask(phone.value); });

  function setError(name, msg) {
    var el = form.elements[name], box = document.getElementById("lead-err-" + name);
    if (!el || !box) return;
    box.textContent = msg || "";
    if (msg) el.setAttribute("aria-invalid", "true"); else el.removeAttribute("aria-invalid");
  }
  function clearErrors() { ["nome", "whatsapp", "email", "perfil"].forEach(function (n) { setError(n, ""); }); alertBox.textContent = ""; }

  function check() {
    var errs = {}, nome = form.elements.nome.value.trim().replace(/\s+/g, " "), d = phone.value.replace(/\D/g, "");
    if (nome.length < 3 || /\d|@|https?:/i.test(nome)) errs.nome = "Informe seu nome completo (só letras).";
    if (!(d.length === 11 && d[2] === "9") && !(d.length === 10 && "2345".indexOf(d[2]) >= 0)) errs.whatsapp = "Informe um WhatsApp com DDD, ex.: (11) 91234-5678.";
    if (!/^[^@\s]+@[^@\s]+\.[a-z]{2,}$/i.test(form.elements.email.value.trim())) errs.email = "Informe um e-mail válido.";
    if (!form.elements.perfil.value) errs.perfil = "Escolha o seu perfil.";
    return errs;
  }

  function open(ev) {
    var a = ev.target.closest("[data-lead]");
    if (!a || ev.defaultPrevented || ev.button > 0 || ev.metaKey || ev.ctrlKey || ev.shiftKey) return;
    ev.preventDefault();
    cta = a.getAttribute("data-lead") || "cta";
    lastFocus = a;
    loadOffer();
    if (!dlg.open) {
      dlg.showModal();
      document.body.classList.add("lead-lock");
      openedAt = Date.now();
      track("lead_modal_open");
      setTimeout(function () { (step1.hidden ? step2.querySelector("a,button") : form.elements.nome).focus(); }, 30);
    }
  }
  document.addEventListener("click", open);

  function close() { if (dlg.open) dlg.close(); }
  dlg.addEventListener("close", function () {
    document.body.classList.remove("lead-lock");
    if (lastFocus) lastFocus.focus();
  });
  dlg.querySelector(".lead-x").addEventListener("click", close);
  dlg.addEventListener("click", function (e) { if (e.target === dlg) close(); }); // clique fora do cartão

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (sending) return;
    clearErrors();
    var errs = check(), first = null;
    Object.keys(errs).forEach(function (k) { setError(k, errs[k]); if (!first) first = form.elements[k]; });
    if (first) { first.focus(); track("lead_error"); return; }
    sending = true; btn.disabled = true; btn.textContent = "Enviando…";
    var body = {
      nome: form.elements.nome.value, whatsapp: phone.value, email: form.elements.email.value, perfil: form.elements.perfil.value,
      marketing: form.elements.marketing.checked, empresa_site: form.elements.empresa_site.value, t: Date.now() - openedAt,
      cta: cta, pagina: location.pathname, referrer: origin.referrer || "", utm: origin.utm || {}
    };
    fetch("/api/lead", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), credentials: "omit" })
      .then(function (r) { return r.json().catch(function () { return { ok: false }; }).then(function (j) { j.status = r.status; return j; }); })
      .then(function (j) {
        if (!j.ok) {
          if (j.erros) Object.keys(j.erros).forEach(function (k) { setError(k, j.erros[k]); });
          alertBox.textContent = j.mensagem || "Não foi possível enviar agora. Tente de novo em instantes.";
          track("lead_error");
          return;
        }
        done(j, body.nome.trim().split(/\s+/)[0]);
      })
      .catch(function () { alertBox.textContent = "Sem conexão com o servidor. Confira a internet e tente de novo."; track("lead_error"); })
      .then(function () { sending = false; btn.disabled = false; btn.textContent = "Receber meu acesso"; });
  });

  // Links para o Balcão (convite, pedido, planos) levam a origem do clique; os do Telegram (t.me) ficam como vieram
  function withUtm(link, content) {
    try {
      var u = new URL(link);
      if (u.hostname !== "balcao.gomilhasx.com" || u.searchParams.has("utm_source")) return link;
      u.searchParams.set("utm_source", "gomilhasx.com"); u.searchParams.set("utm_medium", "site"); u.searchParams.set("utm_content", content);
      return u.toString();
    } catch (e) { return link; }
  }

  function done(j, nome) {
    var t = document.getElementById("lead-ok-t"), p = document.getElementById("lead-ok-p"), go = document.getElementById("lead-go");
    var steps = document.getElementById("lead-steps");
    var safe = /^https:\/\/(t\.me|balcao\.gomilhasx\.com)\//.test(j.link || "");
    go.href = withUtm(safe ? j.link : "https://balcao.gomilhasx.com/", "modal_lead_balcao");
    if (j.tipo === "convite") {
      t.textContent = "Tudo certo, " + nome + "! Seu convite está pronto";
      p.textContent = "Você ganhou o " + j.plano + " · " + j.periodo + ". Abra o convite no Telegram para ativar (ele vale por " + j.validade_horas + " horas).";
      go.textContent = "Abrir convite no Telegram"; steps.hidden = false;
    } else if (j.tipo === "ja_tem_acesso") {
      t.textContent = "Você já tem acesso"; p.textContent = j.mensagem; go.textContent = "Abrir o Balcão no Telegram"; steps.hidden = true;
    } else if (j.tipo === "planos") {
      t.textContent = "Cadastro recebido, " + nome + "!"; p.textContent = j.mensagem; go.textContent = "Ver os planos do Balcão"; steps.hidden = true;
    } else { // resposta genérica
      t.textContent = "Cadastro recebido"; p.textContent = "Obrigado! Em breve você recebe novidades do Balcão."; go.textContent = "Conhecer o Balcão"; steps.hidden = true;
    }
    step1.hidden = true; step2.hidden = false;
    go.focus();
  }

  document.getElementById("lead-mgr-link").addEventListener("click", function () { track("manager_click"); });
})();
