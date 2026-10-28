/* Studio — editor de vídeo online (white-label). Fala com web/servidor.py. */
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const destaque = (s) => esc(s).replace(/\*(.+?)\*/g, "<em>$1</em>");
const fmt = (t) => { t = Math.max(0, t || 0); return `${Math.floor(t / 60)}:${String(Math.floor(t % 60)).padStart(2, "0")}`; };
const fmt1 = (t) => (Math.round((t || 0) * 10) / 10).toFixed(1).replace(".", ",");
const num = (v, d = 0) => { const n = parseFloat(String(v).replace(",", ".")); return Number.isFinite(n) ? n : d; };

const S = { modelos: [], modeloNovo: "reels", marca: {}, p: null, plano: {}, painel: "modelo", fonte: "cortado", sel: null, poll: null };
const player = $("#player");

// ------------------------------------------------------------------ API
async function api(metodo, url, corpo) {
  const op = { method: metodo, headers: {} };
  if (corpo instanceof FormData) op.body = corpo;
  else if (corpo !== undefined) { op.body = JSON.stringify(corpo); op.headers["Content-Type"] = "application/json"; }
  const r = await fetch(url, op);
  if (r.status === 401) { location.href = "/entrar"; throw new Error("Faça login de novo."); }
  const dados = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(dados.erro || `Erro ${r.status}`);
  return dados;
}
function enviar(url, form, aoProgresso) {
  return new Promise((ok, falha) => {
    const x = new XMLHttpRequest();
    x.open("POST", url);
    x.upload.onprogress = (e) => e.lengthComputable && aoProgresso && aoProgresso(e.loaded / e.total);
    x.onload = () => { if (x.status === 401) { location.href = "/entrar"; return; } let d = {}; try { d = JSON.parse(x.responseText); } catch (_) {} x.status < 300 ? ok(d) : falha(new Error(d.erro || `Erro ${x.status}`)); };
    x.onerror = () => falha(new Error("Falha de conexão"));
    x.send(form);
  });
}
let toastT;
function toast(msg, erro = false) {
  const t = $("#toast");
  t.textContent = msg; t.className = "toast on" + (erro ? " erro" : "");
  clearTimeout(toastT); toastT = setTimeout(() => (t.className = "toast"), 3200);
}

// ------------------------------------------------------------------ início
function cardModelo(m, ativo) {
  return `<button class="modelo ${ativo ? "ativo" : ""}" data-modelo="${m.id}">
    <span class="modelo-topo"><span class="amostra" style="background:${m.cor};color:${m.destaque}">Aa</span>${esc(m.nome)}</span>
    <p>${esc(m.descricao)}</p></button>`;
}
async function telaInicio() {
  pararPoll();
  player.pause();
  S.p = null;
  history.replaceState(null, "", "#");
  $("#tela-editor").hidden = true; $("#tela-inicio").hidden = false;
  $("#topo-projeto").hidden = true; $("#topo-acoes").hidden = true;
  $("#modelos-inicio").innerHTML = S.modelos.map((m) => cardModelo(m, m.id === S.modeloNovo)).join("");
  const lista = await api("GET", "/api/projetos");
  $("#lista-projetos").innerHTML = lista.length ? lista.map((p) => `
    <button class="projeto" data-id="${p.id}">
      <div class="thumb" style="${p.tem_capa ? `background-image:url('/arquivos/${p.id}/capa.jpg?v=${Date.now()}')` : ""}">${p.tem_capa ? "" : "sem capa ainda"}</div>
      <div class="info"><b>${esc(p.titulo)}</b><span>${esc((S.modelos.find((m) => m.id === p.modelo) || {}).nome || p.modelo)}${p.tem_final ? " · pronto" : ""}</span></div>
    </button>`).join("") : `<p class="vazio">Nenhum vídeo ainda. Envie o primeiro ao lado.</p>`;
}
$("#modelos-inicio").addEventListener("click", (e) => {
  const b = e.target.closest("[data-modelo]"); if (!b) return;
  S.modeloNovo = b.dataset.modelo;
  $$("#modelos-inicio .modelo").forEach((x) => x.classList.toggle("ativo", x === b));
});
$("#lista-projetos").addEventListener("click", (e) => { const b = e.target.closest("[data-id]"); if (b) abrir(b.dataset.id); });
$("#voltar-inicio").addEventListener("click", (e) => { e.preventDefault(); telaInicio(); });

function ligarDrop(zona, input, aoArquivos) {
  zona.addEventListener("dragover", (e) => { e.preventDefault(); zona.classList.add("sobre"); });
  zona.addEventListener("dragleave", () => zona.classList.remove("sobre"));
  zona.addEventListener("drop", (e) => { e.preventDefault(); zona.classList.remove("sobre"); if (e.dataTransfer.files.length) aoArquivos(e.dataTransfer.files); });
  input.addEventListener("change", () => { if (input.files.length) aoArquivos(input.files); input.value = ""; });
}
ligarDrop($("#drop-video"), $("#input-video"), async (files) => {
  const f = files[0];
  const fd = new FormData(); fd.append("video", f); fd.append("modelo", S.modeloNovo);
  fd.append("titulo", f.name.replace(/\.[^.]+$/, ""));
  const drop = $("#drop-video"); const original = drop.querySelector("strong").textContent;
  try {
    const p = await enviar("/api/projetos", fd, (x) => (drop.querySelector("strong").textContent = `Enviando… ${Math.round(x * 100)}%`));
    drop.querySelector("strong").textContent = original;
    await abrir(p.id);
    executar("preparar");
  } catch (err) { drop.querySelector("strong").textContent = original; toast(err.message, true); }
});

// ------------------------------------------------------------------ projeto
const modelo = () => S.modelos.find((m) => m.id === S.p?.modelo) || S.modelos[0] || {};
async function abrir(id) {
  const p = await api("GET", `/api/projetos/${id}`);
  S.p = p; S.plano = JSON.parse(JSON.stringify(p.plano || {})); S.sel = null;
  history.replaceState(null, "", `#${id}`);
  $("#tela-inicio").hidden = true; $("#tela-editor").hidden = false;
  $("#topo-projeto").hidden = false; $("#topo-acoes").hidden = false;
  $("#titulo-projeto").value = p.titulo || "";
  S.fonte = "cortado";   // abre na prévia editável; rascunho e final ficam no seletor acima do vídeo
  atualizarTudo(true);
  mostrarTarefa();
  if (p.tarefa?.estado === "rodando") iniciarPoll();
}
function atualizarTudo(trocarVideo) {
  const m = modelo();
  $("#chip-modelo").textContent = m.nome || "";
  document.documentElement.style.setProperty("--destaque", m.destaque || "#F9C700");
  document.documentElement.style.setProperty("--marca", m.cor || "#224289");
  $("#moldura").classList.toggle("horizontal", m.formato !== "9:16" && S.p?.horizontal);
  if (trocarVideo) trocarFonte(S.fonte);
  $$("#fontes button").forEach((b) => (b.disabled = !S.p.arquivos[b.dataset.fonte]));
  const pronto = !!S.p.frases.length;
  $("#btn-rascunho").disabled = $("#btn-final").disabled = !pronto || rodando();
  $("#estado-vazio").innerHTML = S.p.arquivos.cortado ? "" : rodando()
    ? `<strong>Analisando o vídeo…</strong><span>Transcrevendo a fala e cortando os silêncios. Isso leva cerca de 1 minuto.</span>`
    : `<strong>Vídeo enviado</strong><span>Clique para analisar: o sistema transcreve a fala e corta os silêncios.</span><button class="btn btn-primario" onclick="executar('preparar')">Analisar vídeo</button>`;
  desenharPainel(); desenharLinha(); previa();
}
const rodando = () => S.p?.tarefa?.estado === "rodando";
function trocarFonte(f) {
  if (!S.p.arquivos[f]) f = "cortado";
  S.fonte = f;
  $$("#fontes button").forEach((b) => b.classList.toggle("ativo", b.dataset.fonte === f));
  const nome = { cortado: "cortado.mp4", rascunho: "video-rascunho.mp4", final: "video-final.mp4" }[f];
  const t = player.currentTime || 0;
  if (S.p.arquivos[f]) { player.src = `/arquivos/${S.p.id}/${nome}?v=${S.p.versao}`; player.currentTime = t; }
  else player.removeAttribute("src");
  $("#previa").classList.toggle("oculta", f !== "cortado");
  $("#aviso-previa").style.visibility = f === "cortado" ? "visible" : "hidden";
}
$("#fontes").addEventListener("click", (e) => { const b = e.target.closest("button"); if (b && !b.disabled) trocarFonte(b.dataset.fonte); });
$("#titulo-projeto").addEventListener("change", (e) => api("PUT", `/api/projetos/${S.p.id}`, { titulo: e.target.value }));

let salvarT;
function salvar(redesenharLinha = true) {
  clearTimeout(salvarT);
  salvarT = setTimeout(async () => {
    try { const p = await api("PUT", `/api/projetos/${S.p.id}`, { plano: S.plano }); S.p.frases = p.frases; S.p.plano = p.plano; }
    catch (err) { toast(err.message, true); }
  }, 450);
  if (redesenharLinha) desenharLinha();
  previa();
}

// ------------------------------------------------------------------ tarefas
async function executar(etapa) {
  try {
    await api("POST", `/api/projetos/${S.p.id}/executar`, { etapa });
    S.p.tarefa = { estado: "rodando", progresso: 0, mensagem: "Começando…", etapa };
    mostrarTarefa(); iniciarPoll(); atualizarTudo(false);
  } catch (err) { toast(err.message, true); }
}
window.executar = executar;
$("#btn-rascunho").onclick = () => executar("rascunho");
$("#btn-final").onclick = () => executar("final");
$("#tarefa-cancelar").onclick = async () => { await api("POST", `/api/projetos/${S.p.id}/cancelar`); };
function mostrarTarefa() {
  const t = S.p.tarefa; const box = $("#tarefa");
  if (!t) { box.hidden = true; return; }
  box.hidden = t.estado === "ok" && Date.now() / 1000 - (t.fim || 0) > 6;
  box.classList.toggle("erro", t.estado === "erro");
  const nomes = { preparar: "Análise", rascunho: "Rascunho", final: "Vídeo final" };
  $("#tarefa-msg").textContent = t.estado === "erro" ? `${nomes[t.etapa] || ""}: ${t.mensagem}` : `${nomes[t.etapa] || ""} · ${t.mensagem}`;
  $("#tarefa-pct").textContent = `${t.progresso || 0}%`;
  $("#tarefa-barra").style.width = `${t.progresso || 0}%`;
  $("#tarefa-log").textContent = t.log || "";
  $("#tarefa-cancelar").hidden = t.estado !== "rodando";
  clearTimeout(mostrarTarefa.t);
  if (t.estado === "ok") mostrarTarefa.t = setTimeout(() => (box.hidden = true), 4000);
}
function iniciarPoll() {
  pararPoll();
  S.poll = setInterval(async () => {
    if (!S.p) return pararPoll();
    const p = await api("GET", `/api/projetos/${S.p.id}`).catch(() => null);
    if (!p) return;
    const antes = S.p.tarefa?.estado;
    S.p.tarefa = p.tarefa; mostrarTarefa();
    if (p.tarefa?.estado !== "rodando") {
      pararPoll();
      const etapa = p.tarefa?.etapa;
      Object.assign(S.p, p);
      if (antes === "rodando" && p.tarefa?.estado === "ok") {
        S.fonte = etapa === "final" ? "final" : etapa === "rascunho" ? "rascunho" : "cortado";
        toast(etapa === "preparar" ? "Vídeo analisado. Revise o texto." : etapa === "final" ? "Vídeo final pronto!" : "Rascunho pronto. Confira.");
        if (etapa === "preparar") S.painel = "texto";
        if (etapa === "final") S.painel = "exportar";
        $$("#trilho button").forEach((b) => b.classList.toggle("ativo", b.dataset.painel === S.painel));
      }
      atualizarTudo(true);
    }
  }, 1500);
}
function pararPoll() { clearInterval(S.poll); S.poll = null; }

// ------------------------------------------------------------------ painéis
$("#trilho").addEventListener("click", (e) => {
  const b = e.target.closest("button[data-painel]"); if (!b) return;
  S.painel = b.dataset.painel;
  $$("#trilho button").forEach((x) => x.classList.toggle("ativo", x === b));
  desenharPainel();
});
const agora = () => Math.round((player.currentTime || 0) * 10) / 10;
function desenharPainel() {
  const el = $("#painel");
  const f = { modelo: pModelo, texto: pTexto, elementos: pElementos, midias: pMidias, musica: pMusica, capa: pCapa, legenda: pLegenda, exportar: pExportar }[S.painel];
  el.innerHTML = f();
  (ligar[S.painel] || (() => {}))(el);
}
const precisaAnalisar = () => S.p.frases.length ? "" : `<div class="cartao"><b>Primeiro, analise o vídeo.</b><p class="dica" style="margin:6px 0 0">Depois disso aparecem o texto falado e a linha do tempo.</p></div>`;

function pModelo() {
  return `<h3>Modelo de edição</h3><p class="dica">Define cores, estilo da legenda, ritmo dos cortes, capa e cartão final. Pode trocar quando quiser.</p>
    <div class="modelos" style="grid-template-columns:1fr">${S.modelos.map((m) => cardModelo(m, m.id === S.p.modelo)).join("")}</div>`;
}
function pTexto() {
  const sub = S.plano.substituicoes || {};
  const trocas = Object.entries(sub);
  return `<h3>Texto falado</h3><p class="dica">Confira o que o sistema entendeu. <b>Clique numa palavra errada para corrigir</b>: a correção vale para a legenda. Clique no tempo para ir ao trecho.</p>
    ${precisaAnalisar()}
    ${trocas.length ? `<div style="margin-bottom:12px">${trocas.map(([a, b]) => `<div class="troca"><span><s>${esc(a)}</s> → <b>${esc(b)}</b></span><button class="btn-link" data-desfazer="${esc(a)}">desfazer</button></div>`).join("")}</div>` : ""}
    <div id="frases">${S.p.frases.map((f, i) => `<div class="frase" data-i="${i}"><time data-t="${f.inicio}">${fmt(f.inicio)}</time><div>${f.palavras.map((w) => `<span class="pal ${trocada(w.w) ? "trocada" : ""}" data-w="${esc(w.w)}" data-t="${w.t}">${esc(w.w)}</span>`).join(" ")}</div></div>`).join("")}</div>
    <hr class="separador"><label class="campo"><span>Nomes e termos difíceis (ajuda a transcrição na próxima análise)</span>
    <input id="vocab" value="${esc(S.plano.vocabulario || "")}" placeholder="Ex.: nome da empresa, nomes de pessoas, termos técnicos"></label>`;
}
const nucleo = (w) => w.replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, "");
const trocada = (w) => Object.values(S.plano.substituicoes || {}).some((v) => v.toLowerCase() === nucleo(w).toLowerCase());

function pElementos() {
  const m = modelo(); const ov = S.plano.overlays || [];
  const enc = S.plano.encerramento === undefined ? m.encerramento : S.plano.encerramento;
  const tipos = { title: "Título", stat: "Número", chart: "Gráfico", lower_third: "Nome na tela" };
  return `<h3>Elementos na tela</h3><p class="dica">Títulos, números e gráficos animados. Na linha do tempo, arraste o bloco amarelo para mudar o momento. <b>Use só números reais.</b></p>
    ${precisaAnalisar()}
    <label class="campo"><span>Gancho (título de abertura) — use *palavra* para destacar</span><input id="gancho" value="${esc(S.plano.gancho || "")}" placeholder="Ex.: 3 erros que *todo mundo* comete"></label>
    <div class="botoes-add">
      <button class="btn btn-pequeno" data-add="title">+ Título</button><button class="btn btn-pequeno" data-add="stat">+ Número</button>
      <button class="btn btn-pequeno" data-add="chart">+ Gráfico</button><button class="btn btn-pequeno" data-add="lower_third">+ Nome na tela</button>
    </div>
    ${ov.map((o, i) => `<div class="cartao" data-ov="${i}" ${S.sel === `ov${i}` ? 'style="border-color:var(--amarelo)"' : ""}>
      <div class="cartao-topo"><b>${tipos[o.type] || o.type}</b><span><button class="btn-link" data-ir="${o.start}">ir</button> · <button class="btn-link btn-perigo" data-del="${i}">remover</button></span></div>
      ${formOverlay(o)}
      <div class="linha3"><label class="campo"><span>Início (s)</span><div class="com-botao"><input data-k="start" value="${fmt1(o.start)}"><button class="btn btn-pequeno" data-agora title="Usar o tempo atual do vídeo">⏱</button></div></label>
      <label class="campo"><span>Duração (s)</span><input data-k="duration" value="${fmt1(o.duration)}"></label>
      ${o.type === "lower_third" ? "" : `<label class="campo"><span>Posição</span><select data-k="position">${["top", "center", "bottom"].map((p) => `<option value="${p}" ${o.position === p ? "selected" : ""}>${{ top: "Topo", center: "Centro", bottom: "Base" }[p]}</option>`).join("")}</select></label>`}</div>
    </div>`).join("")}
    <hr class="separador">
    <label class="alternar"><input type="checkbox" id="enc-on" ${enc ? "checked" : ""}> <b>Cartão final</b></label>
    ${enc ? `<label class="campo"><span>Chamada</span><input id="enc-texto" value="${esc(enc.texto || "")}"></label>
    <div class="linha2"><label class="campo"><span>Assinatura</span><input id="enc-sub" value="${esc(enc.subtexto || "")}"></label><label class="campo"><span>Duração (s)</span><input id="enc-dur" value="${fmt1(enc.duracao || 2.6)}"></label></div>` : ""}`;
}
function formOverlay(o) {
  const c = (k, rot, ph = "") => `<label class="campo"><span>${rot}</span><input data-k="${k}" value="${esc(Array.isArray(o[k]) ? o[k].join(", ") : o[k] ?? "")}" placeholder="${ph}"></label>`;
  if (o.type === "title") return c("text", "Texto (*palavra* destaca)");
  if (o.type === "stat") return `<div class="linha3">${c("prefix", "Antes", "+")}${c("value", "Número")}${c("suffix", "Depois", "%")}</div>${c("label", "Descrição", "clientes atendidos")}`;
  if (o.type === "chart") return `${c("title", "Título do gráfico")}${c("labels", "Rótulos (separe por vírgula)", "2024, 2025, 2026")}${c("values", "Valores (separe por vírgula)", "320, 380, 450")}<div class="linha2">${c("prefix", "Antes do valor")}${c("suffix", "Depois do valor")}</div>`;
  if (o.type === "lower_third") return `${c("title", "Nome")}${c("subtitle", "Papel", "Cliente desde 2022")}`;
  return "";
}
function pMidias() {
  const fixas = Object.fromEntries((S.plano.broll || []).map((b) => [b.arquivo, b]));
  const auto = Object.fromEntries(((S.p.resumo || {}).midias || []).map((b) => [b.arquivo, b]));
  return `<h3>Fotos e vídeos</h3><p class="dica"><b>O nome do arquivo diz quando ele entra.</b> Uma foto chamada <i>biblioteca</i> aparece quando alguém fala "biblioteca". Renomeie aqui ou fixe no tempo atual do vídeo.</p>
    <label class="drop mini" id="drop-midias"><input type="file" id="input-midias" accept="image/*,video/*" multiple hidden><strong>Adicionar fotos e vídeos</strong><span>arraste ou clique</span></label>
    <div class="grade-midias">${S.p.midias.map((m) => {
      const fx = fixas[m.nome], au = auto[m.nome];
      const src = `/arquivos/${S.p.id}/midias/${encodeURIComponent(m.nome)}`;
      return `<div class="midia" data-nome="${esc(m.nome)}"><div class="mthumb" ${m.tipo === "foto" ? `style="background-image:url('${src}')"` : ""}>${m.tipo === "video" ? `<video src="${src}#t=0.5" muted preload="metadata"></video>` : ""}
        <span class="tipo">${m.tipo}</span>${fx ? `<span class="quando">fixa em ${fmt1(fx.inicio)}s</span>` : au ? `<span class="quando">entrou em ${fmt1(au.inicio)}s</span>` : S.p.resumo && S.p.arquivos.rascunho ? `<span class="quando" style="color:var(--erro)">ficou de fora: sem espaço</span>` : ""}</div>
        <div class="mcorpo"><input value="${esc(m.nome.replace(/\.[^.]+$/, ""))}" data-renomear title="Nome = assunto">
        <div class="macoes">${fx ? `<button class="btn-link" data-soltar>automático</button>` : `<button class="btn-link" data-fixar title="Fixar no tempo atual">fixar aqui</button>`}<button class="btn-link btn-perigo" data-apagar>apagar</button></div></div></div>`;
    }).join("")}</div>
    ${S.p.midias.length ? "" : `<p class="dica" style="margin-top:12px">Sem mídias o vídeo fica só com a pessoa falando.</p>`}
    <hr class="separador"><label class="campo"><span>Formato das fotos</span><select id="layout">
      ${[["", "Padrão do modelo"], ["full", "Tela cheia"], ["janela", "Janela no topo (rosto continua visível)"]].map(([v, r]) => `<option value="${v}" ${(S.plano.broll_layout || "") === v ? "selected" : ""}>${r}</option>`).join("")}</select></label>`;
}
function pMusica() {
  const mm = { ...(modelo().musica || {}), ...(S.plano.musica || {}) };
  return `<h3>Música de fundo</h3><p class="dica">A música abaixa sozinha quando alguém fala. Use só trilhas livres de direitos autorais (ex.: Pixabay Music, YouTube Audio Library).</p>
    ${S.p.musica ? `<div class="cartao"><div class="cartao-topo"><b>${esc(S.p.musica)}</b><button class="btn-link btn-perigo" id="tirar-musica">remover</button></div>
      <audio controls src="/arquivos/${S.p.id}/musica/${encodeURIComponent(S.p.musica)}" style="width:100%"></audio></div>` : ""}
    <label class="drop mini" id="drop-musica"><input type="file" id="input-musica" accept="audio/*" hidden><strong>${S.p.musica ? "Trocar música" : "Adicionar música"}</strong><span>MP3, WAV, M4A</span></label>
    <hr class="separador">
    <label class="campo"><span>Volume da música: <b id="vol-txt">${Math.round((mm.volume ?? 0.14) * 100)}%</b></span><input type="range" id="vol" min="0" max="0.5" step="0.01" value="${mm.volume ?? 0.14}"></label>
    <label class="alternar"><input type="checkbox" id="ducking" ${mm.ducking !== false ? "checked" : ""}> Abaixar a música quando houver fala</label>`;
}
function pCapa() {
  const c = S.plano.capa || {}; const est = c.estilo || modelo().capa?.estilo || "faixa";
  return `<h3>Capa</h3><p class="dica">Título curto (até 6 palavras). Use *palavra* para destacar em amarelo. A capa é refeita a cada vídeo gerado.</p>
    <label class="campo"><span>Título da capa</span><input id="capa-titulo" value="${esc(c.titulo || "")}" placeholder="${esc(S.plano.gancho || "Ex.: Por dentro da *empresa*")}"></label>
    <span class="campo"><span>Estilo</span></span><div class="estilos">${["faixa", "impacto", "limpo"].map((e) => `<button class="estilo ${est === e ? "ativo" : ""}" data-estilo="${e}">${e[0].toUpperCase() + e.slice(1)}</button>`).join("")}</div>
    <label class="campo"><span>Quadro do vídeo</span><div class="com-botao"><input id="capa-tempo" value="${c.tempo != null ? fmt1(c.tempo) : ""}" placeholder="automático (o mais nítido)"><button class="btn btn-pequeno" id="capa-agora">Usar quadro atual</button></div></label>
    ${S.p.arquivos.capa ? `<img class="capa-img" src="/arquivos/${S.p.id}/capa.jpg?v=${S.p.versao}" alt="Capa gerada">` : `<p class="dica">A capa aparece aqui depois de gerar o rascunho.</p>`}`;
}
function pLegenda() {
  const txt = S.p.legenda || S.plano.legenda || "";
  return `<h3>Legenda do post</h3><p class="dica">Gerada automaticamente a cada vídeo. Edite aqui: sua versão fica salva e é mantida nos próximos vídeos. ${S.marca.voz ? "Tom da marca: " + esc(S.marca.voz) : ""}</p>
    <label class="campo"><textarea id="legenda" rows="14" placeholder="A legenda aparece aqui depois de gerar o rascunho.">${esc(txt)}</textarea></label>
    <div class="contador" id="contador">${txt.length} / 2.200</div>
    <div class="com-botao"><button class="btn btn-primario" id="salvar-legenda">Salvar</button><button class="btn" id="copiar-legenda">Copiar</button>${S.plano.legenda ? `<button class="btn-link" id="legenda-auto" style="margin-left:auto">voltar à automática</button>` : ""}</div>`;
}
function pExportar() {
  const a = S.p.arquivos, r = S.p.resumo;
  const item = (ok, url, nome, desc) => `<a class="download ${ok ? "" : "off"}" href="${url}?baixar=1&v=${S.p.versao}"><b>${nome}</b><span>${desc}</span></a>`;
  return `<h3>Baixar</h3><p class="dica">Gere o vídeo final para liberar os downloads. ${esc(S.marca.aviso_publicacao || "")}</p>
    <div class="downloads">
      ${item(a.final, `/arquivos/${S.p.id}/video-final.mp4`, "Vídeo final", a.final ? "MP4 1080p" : "ainda não gerado")}
      ${item(a.capa, `/arquivos/${S.p.id}/capa.jpg`, "Capa", "JPG")}
      ${item(a.legenda, `/arquivos/${S.p.id}/legenda.txt`, "Legenda do post", "TXT")}
      ${item(a.rascunho, `/arquivos/${S.p.id}/video-rascunho.mp4`, "Rascunho", "para conferir")}
    </div>
    ${r ? `<hr class="separador"><b>Resumo do último vídeo gerado</b><ul class="resumo-lista">
      <li>Duração: ${fmt1(r.duracao_s)}s · ${esc(r.resolucao)}</li>
      <li>Silêncio removido: ${fmt1(r.silencio_removido_s)}s em ${r.cortes} cortes</li>
      <li>Música: ${esc(r.musica || "sem música")}</li>
      ${(r.midias || []).map((m) => `<li>${esc(m.arquivo)} em ${fmt1(m.inicio)}s (${esc(m.por)})</li>`).join("")}</ul>` : ""}
    <hr class="separador"><button class="btn-link btn-perigo" id="apagar-projeto">Apagar este projeto</button>`;
}

const ligar = {
  modelo(el) {
    el.addEventListener("click", async (e) => {
      const b = e.target.closest("[data-modelo]"); if (!b || b.dataset.modelo === S.p.modelo) return;
      const antes = modelo().formato;
      const p = await api("PUT", `/api/projetos/${S.p.id}`, { modelo: b.dataset.modelo });
      Object.assign(S.p, p); atualizarTudo(false);
      if (S.p.frases.length && modelo().formato !== antes) { toast("Novo formato: reanalisando o vídeo…"); executar("preparar"); }
      else toast(`Modelo: ${modelo().nome}`);
    });
  },
  texto(el) {
    el.addEventListener("click", (e) => {
      const t = e.target.closest("time"); if (t) { player.currentTime = +t.dataset.t; return; }
      const d = e.target.closest("[data-desfazer]");
      if (d) { delete S.plano.substituicoes[d.dataset.desfazer]; salvarEAtualizarTexto(); return; }
      const w = e.target.closest(".pal"); if (!w) return;
      player.currentTime = +w.dataset.t;
      const velho = nucleo(w.dataset.w);
      const novo = prompt(`Corrigir "${velho}" para:`, velho);
      if (novo == null || !novo.trim() || novo.trim() === velho) return;
      S.plano.substituicoes = { ...(S.plano.substituicoes || {}), [velho.toLowerCase()]: novo.trim() };
      salvarEAtualizarTexto();
    });
    $("#vocab", el)?.addEventListener("input", (e) => { S.plano.vocabulario = e.target.value; salvar(false); });
  },
  elementos(el) {
    $("#gancho", el)?.addEventListener("input", (e) => { S.plano.gancho = e.target.value; salvar(); });
    el.addEventListener("click", (e) => {
      const add = e.target.closest("[data-add]");
      if (add) {
        const t = agora(), tipo = add.dataset.add;
        const base = { title: { text: "Novo *título*", duration: 2.5, position: "center" }, stat: { value: 100, label: "descrição", prefix: "+", duration: 3, position: "top" },
          chart: { kind: "bar", title: "Título", labels: ["A", "B", "C"], values: [1, 2, 3], duration: 3.5, position: "top" }, lower_third: { title: "Nome", subtitle: "Papel", duration: 3.5 } }[tipo];
        S.plano.overlays = [...(S.plano.overlays || []), { type: tipo, start: t, ...base }];
        S.sel = `ov${S.plano.overlays.length - 1}`; salvar(); desenharPainel(); return;
      }
      const del = e.target.closest("[data-del]");
      if (del) { S.plano.overlays.splice(+del.dataset.del, 1); S.sel = null; salvar(); desenharPainel(); return; }
      const ir = e.target.closest("[data-ir]"); if (ir) { player.currentTime = +ir.dataset.ir; return; }
      const ag = e.target.closest("[data-agora]");
      if (ag) { const c = ag.closest("[data-ov]"); S.plano.overlays[+c.dataset.ov].start = agora(); salvar(); desenharPainel(); }
    });
    el.addEventListener("input", (e) => {
      const c = e.target.closest("[data-ov]"); const k = e.target.dataset.k;
      if (!c || !k) return;
      const o = S.plano.overlays[+c.dataset.ov]; let v = e.target.value;
      if (["start", "duration", "value"].includes(k)) v = num(v, o[k]);
      if (k === "labels") v = v.split(",").map((x) => x.trim()).filter(Boolean);
      if (k === "values") v = v.split(",").map((x) => num(x)).filter((x) => Number.isFinite(x));
      o[k] = v; salvar();
    });
    $("#enc-on", el)?.addEventListener("change", (e) => {
      S.plano.encerramento = e.target.checked ? { ...(modelo().encerramento || { texto: S.marca.chamada_final || "", subtexto: S.marca.assinatura || "", duracao: 2.6 }) } : null;
      salvar(); desenharPainel();
    });
    const encAtual = () => (S.plano.encerramento ||= { ...(modelo().encerramento || {}) });
    $("#enc-texto", el)?.addEventListener("input", (e) => { encAtual().texto = e.target.value; salvar(); });
    $("#enc-sub", el)?.addEventListener("input", (e) => { encAtual().subtexto = e.target.value; salvar(); });
    $("#enc-dur", el)?.addEventListener("input", (e) => { encAtual().duracao = num(e.target.value, 2.6); salvar(); });
  },
  midias(el) {
    ligarDrop($("#drop-midias", el), $("#input-midias", el), async (files) => {
      const fd = new FormData(); [...files].forEach((f) => fd.append("arquivos", f));
      try { const p = await enviar(`/api/projetos/${S.p.id}/midias`, fd, (x) => ($("#drop-midias strong").textContent = `Enviando… ${Math.round(x * 100)}%`)); Object.assign(S.p, p); toast(`${p.salvos.length} arquivo(s) adicionados`); }
      catch (err) { toast(err.message, true); }
      desenharPainel(); desenharLinha();
    });
    el.addEventListener("change", async (e) => {
      if (e.target.id === "layout") {
        if (e.target.value) S.plano.broll_layout = e.target.value; else delete S.plano.broll_layout;
        salvar(false); return;
      }
      if (!e.target.matches("[data-renomear]")) return;
      const nome = e.target.closest("[data-nome]").dataset.nome;
      try {
        const p = await api("POST", `/api/projetos/${S.p.id}/midias/${encodeURIComponent(nome)}/renomear`, { nome: e.target.value });
        const novo = p.midias.find((m) => !S.p.midias.some((x) => x.nome === m.nome))?.nome;
        (S.plano.broll || []).forEach((b) => { if (b.arquivo === nome && novo) b.arquivo = novo; });
        Object.assign(S.p, p); salvar(); desenharPainel();
      } catch (err) { toast(err.message, true); }
    });
    el.addEventListener("click", async (e) => {
      const card = e.target.closest("[data-nome]"); if (!card) return;
      const nome = card.dataset.nome;
      if (e.target.closest("[data-fixar]")) {
        S.plano.broll = [...(S.plano.broll || []).filter((b) => b.arquivo !== nome), { arquivo: nome, inicio: agora() }];
        salvar(); desenharPainel(); toast(`${nome} fixada em ${fmt1(agora())}s`);
      } else if (e.target.closest("[data-soltar]")) {
        S.plano.broll = (S.plano.broll || []).filter((b) => b.arquivo !== nome); salvar(); desenharPainel();
      } else if (e.target.closest("[data-apagar]")) {
        if (!confirm(`Apagar ${nome}?`)) return;
        const p = await api("DELETE", `/api/projetos/${S.p.id}/midias/${encodeURIComponent(nome)}`);
        S.plano.broll = (S.plano.broll || []).filter((b) => b.arquivo !== nome);
        Object.assign(S.p, p); salvar(); desenharPainel();
      }
    });
  },
  musica(el) {
    ligarDrop($("#drop-musica", el), $("#input-musica", el), async (files) => {
      const fd = new FormData(); fd.append("arquivo", files[0]);
      try { Object.assign(S.p, await enviar(`/api/projetos/${S.p.id}/musica`, fd)); toast("Música adicionada"); } catch (err) { toast(err.message, true); }
      desenharPainel();
    });
    $("#tirar-musica", el)?.addEventListener("click", async () => { Object.assign(S.p, await api("DELETE", `/api/projetos/${S.p.id}/musica`)); desenharPainel(); });
    $("#vol", el).addEventListener("input", (e) => { S.plano.musica = { ...(S.plano.musica || {}), volume: +e.target.value }; $("#vol-txt").textContent = `${Math.round(e.target.value * 100)}%`; salvar(false); });
    $("#ducking", el).addEventListener("change", (e) => { S.plano.musica = { ...(S.plano.musica || {}), ducking: e.target.checked }; salvar(false); });
  },
  capa(el) {
    const capa = () => (S.plano.capa ||= {});
    $("#capa-titulo", el).addEventListener("input", (e) => { capa().titulo = e.target.value; salvar(false); });
    $("#capa-tempo", el).addEventListener("input", (e) => { const v = e.target.value.trim(); if (v) capa().tempo = num(v); else delete capa().tempo; salvar(false); });
    $("#capa-agora", el).addEventListener("click", () => { capa().tempo = agora(); salvar(false); desenharPainel(); toast(`Capa usará o quadro de ${fmt1(agora())}s`); });
    el.addEventListener("click", (e) => { const b = e.target.closest("[data-estilo]"); if (b) { capa().estilo = b.dataset.estilo; salvar(false); desenharPainel(); } });
  },
  legenda(el) {
    const ta = $("#legenda", el);
    ta.addEventListener("input", () => ($("#contador").textContent = `${ta.value.length} / 2.200`));
    $("#salvar-legenda", el).onclick = async () => {
      await api("PUT", `/api/projetos/${S.p.id}/legenda`, { texto: ta.value });
      S.plano.legenda = ta.value; S.p.legenda = ta.value; S.p.arquivos.legenda = true; toast("Legenda salva"); desenharPainel();
    };
    $("#copiar-legenda", el).onclick = async () => { try { await navigator.clipboard.writeText(ta.value); toast("Legenda copiada"); } catch (_) { ta.select(); document.execCommand("copy"); toast("Legenda copiada"); } };
    $("#legenda-auto", el)?.addEventListener("click", () => { delete S.plano.legenda; salvar(false); toast("A legenda volta a ser automática no próximo vídeo gerado"); desenharPainel(); });
  },
  exportar(el) {
    $("#apagar-projeto", el).onclick = async () => {
      if (!confirm("Apagar o projeto e todos os arquivos dele?")) return;
      try { await api("DELETE", `/api/projetos/${S.p.id}`); telaInicio(); } catch (err) { toast(err.message, true); }
    };
  },
};
function salvarEAtualizarTexto() {
  clearTimeout(salvarT);
  api("PUT", `/api/projetos/${S.p.id}`, { plano: S.plano }).then((p) => { S.p.frases = p.frases; desenharPainel(); desenharLinha(); previa(); });
}
// ------------------------------------------------------------------ linha do tempo
const duracao = () => S.p?.duracao || player.duration || 0;
function itensLinha() {
  const m = modelo(), d = duracao(), itens = [];
  if (S.plano.gancho) itens.push({ id: "gancho", nome: S.plano.gancho.replace(/\*/g, ""), ini: 0.15, dur: m.gancho?.duracao || 2.6, fixo: true });
  (S.plano.overlays || []).forEach((o, i) => itens.push({ id: `ov${i}`, nome: o.text || o.title || o.label || o.type, ini: o.start, dur: o.duration, ov: o }));
  const enc = S.plano.encerramento === undefined ? m.encerramento : S.plano.encerramento;
  if (enc && d) itens.push({ id: "fim", nome: "Cartão final", ini: Math.max(0.5, d - (enc.duracao || 2.6)), dur: enc.duracao || 2.6, fixo: true });
  return itens;
}
function midiasLinha() {
  const fixas = (S.plano.broll || []).map((b, i) => ({ id: `br${i}`, nome: b.arquivo, ini: b.inicio, dur: b.duracao || (/\.(mp4|mov|m4v|webm|mkv|avi)$/i.test(b.arquivo) ? modelo().broll?.duracao_video || 3.5 : modelo().broll?.duracao_foto || 2.6), br: b }));
  const nomesFixos = new Set(fixas.map((b) => b.nome));
  const auto = ((S.p.resumo || {}).midias || []).filter((b) => !nomesFixos.has(b.arquivo) && S.p.midias.some((m) => m.nome === b.arquivo))
    .map((b) => ({ id: `au-${b.arquivo}`, nome: `${b.arquivo} (auto)`, ini: b.inicio, dur: b.duracao, auto: true }));
  return [...fixas, ...auto];
}
function desenharLinha() {
  const d = duracao();
  if (!S.p || !d) { ["#faixa-fala", "#faixa-elementos", "#faixa-midias", "#regua"].forEach((s) => ($(s).innerHTML = "")); return; }
  const pct = (t) => `${(100 * t) / d}%`;
  const largura = $("#faixa-fala").offsetWidth || 800;
  const passo = [1, 2, 5, 10, 15, 30, 60, 120].find((x) => (largura * x) / d >= 46) || 300;
  let r = ""; for (let t = 0; t <= d; t += passo) r += `<span style="left:${pct(t)}">${fmt(t)}</span>`;
  $("#regua").innerHTML = r;
  $("#faixa-fala").innerHTML = S.p.frases.map((f) => `<div class="bloco fala" data-t="${f.inicio}" style="left:${pct(f.inicio)};width:${pct(Math.max(f.fim - f.inicio, 0.2))}" title="${esc(f.palavras.map((w) => w.w).join(" "))}">${esc(f.palavras.map((w) => w.w).join(" "))}</div>`).join("");
  $("#faixa-elementos").innerHTML = itensLinha().map((b) => `<div class="bloco el ${b.fixo ? "fixo" : ""} ${S.sel === b.id ? "sel" : ""}" data-id="${b.id}" style="left:${pct(b.ini)};width:${pct(b.dur)}" title="${esc(b.nome)}">${esc(b.nome)}</div>`).join("");
  $("#faixa-midias").innerHTML = midiasLinha().map((b) => `<div class="bloco md ${b.auto ? "auto" : ""}" data-id="${b.id}" style="left:${pct(b.ini)};width:${pct(b.dur)}" title="${esc(b.nome)}">${esc(b.nome)}</div>`).join("");
  moverCabeca();
}
function tempoDoEvento(e, trilha) {
  const r = trilha.getBoundingClientRect();
  return Math.max(0, Math.min(duracao(), ((e.clientX - r.left) / r.width) * duracao()));
}
let arrasto = null;
$("#linha").addEventListener("pointerdown", (e) => {
  const trilha = e.target.closest(".trilha") || (e.target.closest(".regua") && $("#faixa-fala"));
  if (!trilha || !duracao()) return;
  const bloco = e.target.closest(".bloco");
  if (bloco && (bloco.classList.contains("el") || bloco.classList.contains("md")) && !bloco.classList.contains("fixo") && !bloco.classList.contains("auto")) {
    const id = bloco.dataset.id;
    const alvo = id.startsWith("ov") ? S.plano.overlays[+id.slice(2)] : S.plano.broll[+id.slice(2)];
    const chave = id.startsWith("ov") ? "start" : "inicio";
    arrasto = { alvo, chave, x0: e.clientX, t0: alvo[chave], trilha, bloco, moveu: false };
    S.sel = id.startsWith("ov") ? id : null;
    bloco.setPointerCapture(e.pointerId);
    return;
  }
  if (bloco?.dataset.t) { player.currentTime = +bloco.dataset.t; return; }
  if (bloco?.dataset.id && itensLinha().find((x) => x.id === bloco.dataset.id)) { player.currentTime = itensLinha().find((x) => x.id === bloco.dataset.id).ini; return; }
  player.currentTime = tempoDoEvento(e, trilha);
});
$("#linha").addEventListener("pointermove", (e) => {
  if (!arrasto) return;
  const r = arrasto.trilha.getBoundingClientRect();
  const dt = ((e.clientX - arrasto.x0) / r.width) * duracao();
  if (Math.abs(e.clientX - arrasto.x0) > 3) arrasto.moveu = true;
  const t = Math.max(0, Math.min(duracao() - 0.5, Math.round((arrasto.t0 + dt) * 10) / 10));
  arrasto.alvo[arrasto.chave] = t;
  arrasto.bloco.style.left = `${(100 * t) / duracao()}%`;
  player.currentTime = t;
});
$("#linha").addEventListener("pointerup", () => {
  if (!arrasto) return;
  const { moveu } = arrasto; arrasto = null;
  if (moveu) salvar(); else desenharLinha();
  if (S.painel === "elementos" || S.painel === "midias") desenharPainel();
});
function moverCabeca() {
  const d = duracao(); const trilha = $("#faixa-fala");
  if (!d || !trilha.offsetWidth) return;
  const base = trilha.offsetLeft;
  $("#cabeca").style.left = `${base + (trilha.offsetWidth * (player.currentTime || 0)) / d - 1}px`;
}

// ------------------------------------------------------------------ prévia (aproximada) sobre o vídeo cortado
function previa() {
  if (!S.p) return;
  const t = player.currentTime || 0, m = modelo();
  $("#tempo").textContent = `${fmt(t)} / ${fmt(duracao())}`;
  moverCabeca();
  if (S.fonte !== "cortado") return;
  const itens = itensLinha();
  const ativo = (b) => t >= b.ini && t < b.ini + b.dur;
  const fim = itens.find((b) => b.id === "fim" && ativo(b));
  const enc = S.plano.encerramento === undefined ? m.encerramento : S.plano.encerramento;
  $("#pv-fim").style.display = fim ? "flex" : "none";
  if (fim) $("#pv-fim").innerHTML = `<div>${destaque(enc.texto || "")}</div><small>${esc(enc.subtexto || "")}</small>`;
  const g = itens.find((b) => b.id === "gancho" && ativo(b));
  const tit = itens.find((b) => b.ov?.type === "title" && ativo(b));
  const pvT = $("#pv-titulo");
  pvT.innerHTML = g ? destaque(S.plano.gancho) : tit ? destaque(tit.ov.text) : "";
  pvT.style.top = tit && !g ? ({ top: "10%", center: "42%", bottom: "74%" }[tit.ov.position] || "10%") : (m.gancho?.posicao === "center" ? "42%" : "10%");
  const el = itens.find((b) => b.ov && b.ov.type !== "title" && ativo(b));
  const pe = $("#pv-elemento");
  pe.className = "pv-elemento" + (el?.ov.type === "lower_third" ? " lower" : "");
  pe.style.display = el ? "block" : "none";
  if (el) {
    const o = el.ov;
    pe.innerHTML = o.type === "stat" ? `<b>${esc(o.prefix || "")}${Number(o.value).toLocaleString("pt-BR")}${esc(o.suffix || "")}</b><small>${esc(o.label || "")}</small>`
      : o.type === "chart" ? `<small>${esc(o.title || "")}</small><b style="font-size:3cqh">▂▄▆█</b><small>${esc((o.labels || []).join(" · "))}</small>`
      : `<b>${esc(o.title || "")}</b><small>${esc(o.subtitle || "")}</small>`;
    pe.style.top = o.type === "lower_third" ? "58%" : ({ top: "7%", center: "40%", bottom: "64%" }[o.position] || "7%");
  }
  // legenda: grupos de até 3 palavras (4 no estilo caixa)
  const estilo = m.legenda || "ref"; const max = estilo === "box" ? 4 : estilo === "clean" ? 7 : 3;
  const pv = $("#pv-legenda"); pv.className = `pv-legenda ${estilo}`;
  let txt = "";
  if (!fim) {
    const f = S.p.frases.find((x) => t >= x.inicio - 0.05 && t <= x.fim + 0.25);
    if (f) {
      let k = 0; for (let i = 0; i < f.palavras.length; i++) if (f.palavras[i].t <= t) k = i;
      const g0 = Math.floor(k / max) * max, grupo = f.palavras.slice(g0, g0 + max);
      const html = grupo.map((w, j) => {
        const destacar = estilo === "viral" ? g0 + j === k : /\d/.test(w.w) || (estilo === "ref" && j === grupo.length - 1 && w.w.length > 6);
        return destacar ? `<span class="k">${esc(w.w)}</span>` : esc(w.w);
      }).join(" ");
      txt = estilo === "box" ? `<span class="caixa">${html}</span>` : html;
    }
  }
  pv.innerHTML = txt;
  $$("#frases .frase").forEach((x) => x.classList.toggle("atual", !!S.p.frases[+x.dataset.i] && t >= S.p.frases[+x.dataset.i].inicio && t <= S.p.frases[+x.dataset.i].fim));
}
player.addEventListener("timeupdate", previa);
player.addEventListener("seeked", previa);
player.addEventListener("loadedmetadata", () => { $("#moldura").classList.toggle("horizontal", player.videoWidth > player.videoHeight); desenharLinha(); previa(); });
let raf; player.addEventListener("play", () => { const loop = () => { previa(); raf = requestAnimationFrame(loop); }; loop(); iconePlay(); });
player.addEventListener("pause", () => { cancelAnimationFrame(raf); iconePlay(); });
function iconePlay() { $("#btn-play").innerHTML = player.paused ? '<svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>' : '<svg viewBox="0 0 24 24"><path d="M7 5h4v14H7zM13 5h4v14h-4z"/></svg>'; }
$("#btn-play").onclick = () => (player.src ? (player.paused ? player.play() : player.pause()) : null);
$("#moldura").addEventListener("click", (e) => { if (!e.target.closest(".estado-vazio") && player.src) player.paused ? player.play() : player.pause(); });
document.addEventListener("keydown", (e) => {
  if (!S.p || e.target.closest("input, textarea, select")) return;
  if (e.code === "Space") { e.preventDefault(); $("#btn-play").click(); }
  if (e.code === "ArrowLeft") player.currentTime -= e.shiftKey ? 5 : 1;
  if (e.code === "ArrowRight") player.currentTime += e.shiftKey ? 5 : 1;
});
window.addEventListener("resize", () => { desenharLinha(); });

// ------------------------------------------------------------------ partida
function aplicarMarca(m) {
  S.marca = m;
  const nome = m.produto || "Studio";
  document.title = nome;
  $("#nome-produto").textContent = nome;
  document.documentElement.style.setProperty("--amarelo", m.destaque || "#F9C700");
  document.documentElement.style.setProperty("--navy", m.cor || "#224289");
  if (m.logo) $("#logo-marca").outerHTML = '<img src="/logo" alt="">';
  else $("#logo-marca").textContent = nome[0];
}
$("#btn-sair").onclick = async () => { await api("POST", "/api/sair"); location.href = "/entrar"; };

(async () => {
  aplicarMarca(await api("GET", "/api/marca"));
  const eu = await api("GET", "/api/eu");
  $("#btn-sair").hidden = !eu.login;
  S.modelos = await api("GET", "/api/modelos");
  const id = location.hash.slice(1);
  if (id) { try { await abrir(id); return; } catch (_) {} }
  telaInicio();
})();
