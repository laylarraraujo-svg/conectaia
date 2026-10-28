#!/usr/bin/env python3
"""Studio: editor de vídeo online (white-label; nome, cores e logo vêm de config/marca.json).

Página web por cima do editar.py: envia o vídeo, escolhe o modelo, revisa o texto, posiciona elementos,
gera rascunho/final e baixa vídeo, capa e legenda.

Uso:
  pip install -r requirements.txt
  python web/acesso.py adicionar voce@empresa.com      # cria o primeiro login
  python web/servidor.py                               # abre em http://localhost:8080
  python web/servidor.py --porta 9000 --publico        # aceita acesso de outros computadores

Variáveis: STUDIO_CONFIG (marca, logo, usuários, modelos), STUDIO_PROJETOS (vídeos), STUDIO_HTTPS=1 (cookie seguro),
STUDIO_SEM_LOGIN=1 (só para testes locais), STUDIO_ADMIN_EMAIL/STUDIO_ADMIN_SENHA (cria o primeiro login).
"""
import argparse
import json
import re
import subprocess
import sys
import threading
import time
import unicodedata
import uuid
from pathlib import Path

import os
from datetime import timedelta

from flask import Flask, abort, jsonify, redirect, request, send_from_directory, session

ROOT = Path(__file__).resolve().parent.parent          # editor-de-video/
PROJ = Path(os.environ.get("STUDIO_PROJETOS", ROOT / "projetos"))
STATIC = Path(__file__).resolve().parent / "static"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "motor" / "scripts"))

import editar  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
import acesso  # noqa: E402

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 ** 3        # até 4 GB por envio
app.config.update(SECRET_KEY=acesso.segredo(), SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  SESSION_COOKIE_SECURE=os.environ.get("STUDIO_HTTPS") == "1", PERMANENT_SESSION_LIFETIME=timedelta(days=30))
SEM_LOGIN = os.environ.get("STUDIO_SEM_LOGIN") == "1"
LIVRES = {"/entrar", "/api/entrar", "/api/marca", "/fonte.ttf", "/logo", "/saude"}
LOCK = threading.Lock()
RODANDO = {}                                            # id do projeto -> Popen

ETAPAS = [("Preparando", 5, "Preparando o vídeo"), ("Transcrevendo", 12, "Transcrevendo a fala"),
          ("Silêncio removido", 40, "Cortes prontos"), ("Renderizando", 45, "Montando o vídeo"),
          ("Mixando", 90, "Mixando a trilha"), ("Pronto", 100, "Pronto")]


# --------------------------------------------------------------------------- utilidades
def nome_seguro(nome):
    nome = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    base, ext = Path(nome).stem, Path(nome).suffix.lower()
    base = re.sub(r"[^A-Za-z0-9]+", "-", base).strip("-").lower() or "arquivo"
    return base[:60] + re.sub(r"[^a-z0-9.]", "", ext)


def pasta(pid):
    if not re.fullmatch(r"[a-z0-9-]{4,80}", pid or ""):
        abort(404)
    p = PROJ / pid
    if not p.exists():
        abort(404)
    return p


def ler(p, padrao=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def gravar(p, obj):
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def projeto_info(pid):
    p = pasta(pid)
    meta = ler(p / "projeto.json", {})
    saida = p / "saida"
    corte = ler(saida / "_trabalho" / "corte.json")
    plano = ler(p / "plano.json", {})
    frases = []
    duracao = None
    if corte:
        repl = {**(editar.carregar_modelo(meta.get("modelo", "reels"))["edicao"].get("replacements") or {}),
                **plano.get("substituicoes", {})}
        words = editar.apply_replacements(corte["words"], repl)
        duracao = corte["stats"]["final_s"]
        for f in _frases_com_palavras(words):
            frases.append(f)
    arquivos = {k: (saida / v).exists() for k, v in
                {"cortado": "_trabalho/cortado.mp4", "rascunho": "video-rascunho.mp4", "final": "video-final.mp4",
                 "capa": "capa.jpg", "legenda": "legenda.txt"}.items()}
    legenda = (saida / "legenda.txt").read_text(encoding="utf-8") if arquivos["legenda"] else ""
    musica = sorted((p / "musica").glob("*"))
    return {
        "id": pid, **meta, "plano": plano, "frases": frases, "duracao": duracao,
        "corte": corte["stats"] if corte else None,
        "midias": [{"nome": f.name, "tipo": "video" if f.suffix.lower() in editar.VID_EXT else "foto"}
                   for f in sorted((p / "midias").glob("*")) if f.suffix.lower() in editar.IMG_EXT | editar.VID_EXT],
        "musica": musica[0].name if musica else None,
        "arquivos": arquivos, "legenda": legenda, "resumo": ler(saida / "resumo.json"),
        "tarefa": ler(p / "tarefa.json"), "versao": int(time.time()),
    }


def _frases_com_palavras(words):
    out, cur = [], []
    for i, w in enumerate(words):
        if cur and (w["start"] - words[cur[-1]]["end"] > 0.6 or len(cur) >= 14):
            out.append(cur)
            cur = []
        cur.append(i)
        if w["word"].rstrip().endswith((".", "!", "?")):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return [{"inicio": words[f[0]]["start"], "fim": words[f[-1]]["end"],
             "palavras": [{"t": words[i]["start"], "w": words[i]["word"]} for i in f]} for f in out]


# --------------------------------------------------------------------------- tarefas (rodam o editar.py)
def executar(pid, etapa):
    p = PROJ / pid
    meta = ler(p / "projeto.json", {})
    cmd = [sys.executable, "-u", str(ROOT / "editar.py"), str(p / meta["video"]), "--modelo", meta.get("modelo", "reels"),
           "--saida", str(p / "saida"), "--plano", str(p / "plano.json")]
    if any((p / "midias").iterdir()):
        cmd += ["--midias", str(p / "midias")]
    musica = sorted((p / "musica").glob("*"))
    if musica:
        cmd += ["--musica", str(musica[0])]
    if etapa == "preparar":
        cmd.append("--preparar")
    elif etapa == "rascunho":
        cmd.append("--rascunho")
    tarefa = {"etapa": etapa, "estado": "rodando", "inicio": time.time(), "progresso": 0, "mensagem": "Começando...", "log": ""}
    gravar(p / "tarefa.json", tarefa)
    log_path = p / "saida" / "log.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as log:
        proc = subprocess.Popen(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, text=True)
        RODANDO[pid] = proc
        while proc.poll() is None:
            time.sleep(1)
            _atualizar(p, tarefa, log_path)
    RODANDO.pop(pid, None)
    _atualizar(p, tarefa, log_path)
    tarefa["estado"] = "ok" if proc.returncode == 0 else "erro"
    if proc.returncode == 0:
        tarefa["progresso"], tarefa["mensagem"] = 100, "Pronto"
    else:
        linhas = [l for l in tarefa["log"].splitlines() if l.strip() and "HF Hub" not in l]
        tarefa["mensagem"] = linhas[-1][:300] if linhas else "Falhou"
    tarefa["fim"] = time.time()
    gravar(p / "tarefa.json", tarefa)


def _atualizar(p, tarefa, log_path):
    txt = log_path.read_text(encoding="utf-8", errors="ignore")
    tarefa["log"] = "\n".join(l for l in txt.splitlines() if "HF Hub" not in l)[-4000:]
    for chave, pct, msg in ETAPAS:
        if chave in txt and pct >= tarefa["progresso"]:
            tarefa["progresso"], tarefa["mensagem"] = pct, msg
    if "Renderizando" in txt and "Mixando" not in txt and "Pronto" not in txt:
        # render: estima pelo tempo (≈ 5x a duração do vídeo em CPU; rascunho um pouco menos)
        corte = ler(p / "saida" / "_trabalho" / "corte.json")
        dur = corte["stats"]["final_s"] if corte else 30
        t0 = tarefa.setdefault("inicio_render", time.time())
        est = dur * (4.5 if tarefa["etapa"] == "rascunho" else 5.5)
        tarefa["progresso"] = min(88, 45 + int(43 * (time.time() - t0) / max(est, 1)))
        tarefa["mensagem"] = "Montando o vídeo (legendas, fotos, gráficos)"
    gravar(p / "tarefa.json", tarefa)


# --------------------------------------------------------------------------- acesso
@app.before_request
def exigir_login():
    if SEM_LOGIN or request.path in LIVRES or request.path.startswith("/static/") or session.get("usuario"):
        return None
    if request.path.startswith(("/api/", "/arquivos/")):
        return jsonify(erro="Faça login de novo."), 401
    return redirect("/entrar")


@app.after_request
def cabecalhos(r):
    r.headers.setdefault("X-Content-Type-Options", "nosniff")
    r.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    r.headers.setdefault("Referrer-Policy", "same-origin")
    return r


@app.get("/entrar")
def pagina_entrar():
    return send_from_directory(STATIC, "entrar.html")


@app.post("/api/entrar")
def entrar():
    d = request.get_json(force=True, silent=True) or {}
    ip = request.remote_addr or ""          # atrás do proxy, o waitress já põe o IP real aqui
    try:
        ok = acesso.conferir(d.get("email"), d.get("senha"), ip)
    except PermissionError as e:
        return jsonify(erro=str(e)), 429
    if not ok:
        return jsonify(erro="E-mail ou senha incorretos." if acesso.existe_algum()
                       else "Nenhum usuário criado ainda. Veja o LEIA-ME (web/acesso.py adicionar)."), 401
    session.clear()
    session.permanent = True
    session["usuario"] = d["email"].strip().lower()
    return jsonify(ok=True)


@app.post("/api/sair")
def sair():
    session.clear()
    return jsonify(ok=True)


@app.get("/api/eu")
def eu():
    u = session.get("usuario")
    return jsonify(email=u, nome=acesso.nome(u) if u else "", login=not SEM_LOGIN)


@app.get("/saude")
def saude():
    return jsonify(ok=True)


@app.get("/api/marca")
def api_marca():
    m = editar.marca()
    campos = ("produto", "empresa", "cor", "destaque", "voz", "aviso_publicacao", "assinatura", "chamada_final")
    return jsonify({k: m.get(k) for k in campos} | {"logo": bool(m.get("logo_path"))})


@app.get("/logo")
def logo():
    lp = editar.marca().get("logo_path")
    if not lp:
        abort(404)
    return send_from_directory(Path(lp).parent, Path(lp).name, max_age=300)


# --------------------------------------------------------------------------- rotas
@app.get("/")
def index():
    return send_from_directory(STATIC, "index.html")


@app.get("/static/<path:arq>")
def estatico(arq):
    return send_from_directory(STATIC, arq)


@app.get("/fonte.ttf")
def fonte():
    return send_from_directory(ROOT / "motor" / "fonts", "Montserrat-ExtraBold.ttf")


@app.get("/api/modelos")
def modelos():
    out = []
    for mid in editar.arquivos_modelos():
        m = editar.carregar_modelo(mid)
        th = (m.get("edicao") or {}).get("theme") or {}
        out.append({"id": mid, "nome": m.get("nome", mid), "descricao": m.get("descricao", ""), "formato": m.get("formato"),
                    "cor": th.get("brand", "#224289"), "destaque": th.get("accent", "#F9C700"),
                    "legenda": ((m.get("edicao") or {}).get("subtitles") or {}).get("style", "ref"),
                    "musica": m.get("musica") or {}, "capa": m.get("capa") or {}, "encerramento": m.get("encerramento"),
                    "gancho": m.get("gancho") or {}, "broll": m.get("broll") or {}, "hashtags": (m.get("legenda") or {}).get("hashtags", [])})
    out.sort(key=lambda x: (x["id"] != "reels", x["nome"]))
    return jsonify(out)


@app.get("/api/projetos")
def listar():
    PROJ.mkdir(exist_ok=True)
    itens = []
    for p in sorted(PROJ.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        meta = ler(p / "projeto.json")
        if meta:
            itens.append({"id": p.name, **meta, "tem_final": (p / "saida" / "video-final.mp4").exists(),
                          "tem_capa": (p / "saida" / "capa.jpg").exists()})
    return jsonify(itens)


@app.post("/api/projetos")
def criar():
    f = request.files.get("video")
    if not f or not f.filename:
        return jsonify(erro="Envie um arquivo de vídeo."), 400
    nome = nome_seguro(f.filename)
    if Path(nome).suffix not in editar.VID_EXT:
        return jsonify(erro="Formato não suportado. Use MP4, MOV, M4V, WEBM, MKV ou AVI."), 400
    pid = f"{Path(nome).stem[:40]}-{uuid.uuid4().hex[:6]}"
    p = PROJ / pid
    (p / "midias").mkdir(parents=True)
    (p / "musica").mkdir()
    f.save(p / f"original{Path(nome).suffix}")
    titulo = request.form.get("titulo") or Path(f.filename).stem
    gravar(p / "projeto.json", {"titulo": titulo, "video": f"original{Path(nome).suffix}",
                                "modelo": request.form.get("modelo", "reels"), "criado": time.time()})
    gravar(p / "plano.json", {})
    return jsonify(projeto_info(pid))


@app.get("/api/projetos/<pid>")
def ver(pid):
    return jsonify(projeto_info(pid))


@app.delete("/api/projetos/<pid>")
def apagar(pid):
    import shutil
    if pid in RODANDO:
        return jsonify(erro="Espere a tarefa terminar."), 409
    shutil.rmtree(pasta(pid))
    return jsonify(ok=True)


@app.put("/api/projetos/<pid>")
def atualizar(pid):
    p = pasta(pid)
    dados = request.get_json(force=True)
    meta = ler(p / "projeto.json", {})
    for k in ("titulo", "modelo"):
        if k in dados:
            meta[k] = dados[k]
    gravar(p / "projeto.json", meta)
    if "plano" in dados:
        plano = {k: v for k, v in dados["plano"].items() if v not in (None, "", [], {})}
        if "encerramento" in dados["plano"] and dados["plano"]["encerramento"] is None:
            plano["encerramento"] = None
        gravar(p / "plano.json", plano)
    return jsonify(projeto_info(pid))


@app.post("/api/projetos/<pid>/midias")
def subir_midias(pid):
    p = pasta(pid)
    salvos = []
    for f in request.files.getlist("arquivos"):
        nome = nome_seguro(f.filename)
        if Path(nome).suffix in editar.IMG_EXT | editar.VID_EXT:
            f.save(p / "midias" / nome)
            salvos.append(nome)
    return jsonify(projeto_info(pid) | {"salvos": salvos})


@app.post("/api/projetos/<pid>/midias/<nome>/renomear")
def renomear_midia(pid, nome):
    p = pasta(pid)
    src = p / "midias" / nome_seguro(nome)
    novo = nome_seguro((request.get_json(force=True).get("nome") or "") + src.suffix)
    if not src.exists() or not novo:
        abort(404)
    src.rename(p / "midias" / novo)
    return jsonify(projeto_info(pid))


@app.delete("/api/projetos/<pid>/midias/<nome>")
def apagar_midia(pid, nome):
    (pasta(pid) / "midias" / nome_seguro(nome)).unlink(missing_ok=True)
    return jsonify(projeto_info(pid))


@app.post("/api/projetos/<pid>/musica")
def subir_musica(pid):
    p = pasta(pid)
    f = request.files.get("arquivo")
    nome = nome_seguro(f.filename) if f else ""
    if Path(nome).suffix not in editar.AUD_EXT:
        return jsonify(erro="Use MP3, WAV, M4A, AAC, OGG ou FLAC."), 400
    for old in (p / "musica").glob("*"):
        old.unlink()
    f.save(p / "musica" / nome)
    return jsonify(projeto_info(pid))


@app.delete("/api/projetos/<pid>/musica")
def apagar_musica(pid):
    for old in (pasta(pid) / "musica").glob("*"):
        old.unlink()
    return jsonify(projeto_info(pid))


@app.put("/api/projetos/<pid>/legenda")
def salvar_legenda(pid):
    p = pasta(pid)
    texto = request.get_json(force=True).get("texto", "")
    (p / "saida").mkdir(exist_ok=True)
    (p / "saida" / "legenda.txt").write_text(texto, encoding="utf-8")
    plano = ler(p / "plano.json", {})
    plano["legenda"] = texto                     # próximos renders mantêm o texto editado
    gravar(p / "plano.json", plano)
    return jsonify(ok=True)


@app.post("/api/projetos/<pid>/executar")
def rodar(pid):
    pasta(pid)
    etapa = (request.get_json(force=True) or {}).get("etapa", "rascunho")
    if etapa not in ("preparar", "rascunho", "final"):
        abort(400)
    with LOCK:
        if RODANDO:
            outro = next(iter(RODANDO))
            return jsonify(erro="Já tem um vídeo sendo processado" + ("" if outro == pid else " em outro projeto") + ". Aguarde terminar."), 409
        RODANDO[pid] = None
    threading.Thread(target=executar, args=(pid, etapa), daemon=True).start()
    return jsonify(ok=True)


@app.post("/api/projetos/<pid>/cancelar")
def cancelar(pid):
    proc = RODANDO.get(pid)
    if proc:
        proc.terminate()
    return jsonify(ok=True)


@app.get("/arquivos/<pid>/<path:arq>")
def arquivo(pid, arq):
    p = pasta(pid)
    permitidos = {"cortado.mp4": "saida/_trabalho/cortado.mp4", "video-rascunho.mp4": "saida/video-rascunho.mp4",
                  "video-final.mp4": "saida/video-final.mp4", "capa.jpg": "saida/capa.jpg", "legenda.txt": "saida/legenda.txt"}
    if arq in permitidos:
        alvo = p / permitidos[arq]
        return send_from_directory(alvo.parent, alvo.name, conditional=True,
                                   as_attachment=request.args.get("baixar") == "1",
                                   download_name=f"{slug_titulo(p)}-{arq}")
    if arq.startswith("midias/") or arq.startswith("musica/"):
        sub, nome = arq.split("/", 1)
        return send_from_directory(p / sub, nome_seguro(nome), conditional=True)
    abort(404)


def slug_titulo(p):
    return editar.slug((ler(p / "projeto.json", {}) or {}).get("titulo", "video"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--porta", type=int, default=8080)
    ap.add_argument("--publico", action="store_true", help="aceita acesso de outros computadores (0.0.0.0)")
    a = ap.parse_args()
    PROJ.mkdir(exist_ok=True)
    # tarefas que estavam rodando quando o servidor caiu ficam marcadas como interrompidas
    for t in PROJ.glob("*/tarefa.json"):
        d = ler(t, {})
        if d.get("estado") == "rodando":
            d.update(estado="erro", mensagem="Interrompido (o servidor foi reiniciado). Rode de novo.")
            gravar(t, d)
    acesso.admin_inicial()
    if not SEM_LOGIN and not acesso.existe_algum():
        print("AVISO: nenhum usuário criado. Rode: python web/acesso.py adicionar voce@empresa.com")
    host = "0.0.0.0" if a.publico else "127.0.0.1"
    print(f"{editar.marca().get('produto', 'Studio')} em http://{'localhost' if host == '127.0.0.1' else host}:{a.porta}")
    try:
        from waitress import serve
        serve(app, host=host, port=a.porta, threads=12, max_request_body_size=app.config["MAX_CONTENT_LENGTH"],
              channel_timeout=600, **({"trusted_proxy": "*", "trusted_proxy_count": 1, "trusted_proxy_headers": "x-forwarded-for x-forwarded-proto"}
                 if os.environ.get("STUDIO_ATRAS_DE_PROXY") == "1" else {}))
    except ImportError:
        app.run(host=host, port=a.porta, threaded=True)


if __name__ == "__main__":
    main()
