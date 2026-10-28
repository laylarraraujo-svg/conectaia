#!/usr/bin/env python3
"""Usuários do Studio (login com e-mail e senha). As senhas ficam só como hash em config/usuarios.json.

Uso (no servidor):
  python web/acesso.py adicionar maria@cliente.com.br      # pede a senha
  python web/acesso.py remover maria@cliente.com.br
  python web/acesso.py listar
Com Docker:  docker compose exec studio python web/acesso.py adicionar maria@cliente.com.br
"""
import getpass
import json
import os
import secrets
import sys
import time
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

ROOT = Path(__file__).resolve().parent.parent
CONFIG = Path(os.environ.get("STUDIO_CONFIG", ROOT / "config"))
ARQ = CONFIG / "usuarios.json"
_falhas = {}                                   # ip -> [tentativas, desde]


def _ler():
    try:
        return json.loads(ARQ.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _gravar(d):
    CONFIG.mkdir(parents=True, exist_ok=True)
    tmp = ARQ.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    os.chmod(tmp, 0o600)
    tmp.replace(ARQ)


def existe_algum():
    return bool(_ler())


def adicionar(email, senha, nome=""):
    email = email.strip().lower()
    if "@" not in email or len(senha) < 8:
        raise ValueError("Use um e-mail válido e uma senha com pelo menos 8 caracteres.")
    d = _ler()
    d[email] = {"nome": nome or email.split("@")[0], "hash": generate_password_hash(senha), "criado": int(time.time())}
    _gravar(d)


def remover(email):
    d = _ler()
    d.pop(email.strip().lower(), None)
    _gravar(d)


def conferir(email, senha, ip=""):
    """True se a senha bate. Bloqueia o IP por 10 min depois de 8 erros seguidos."""
    n, desde = _falhas.get(ip, (0, time.time()))
    if time.time() - desde > 600:
        n, desde = 0, time.time()
    if n >= 8:
        raise PermissionError("Muitas tentativas. Espere 10 minutos.")
    u = _ler().get((email or "").strip().lower())
    ok = bool(u) and check_password_hash(u["hash"], senha or "")
    if ok:
        _falhas.pop(ip, None)
    else:
        _falhas[ip] = (n + 1, desde)
        time.sleep(0.6)
    return ok


def nome(email):
    return (_ler().get(email) or {}).get("nome", email)


def segredo():
    """Chave das sessões: STUDIO_SEGREDO ou um arquivo gerado na primeira vez."""
    if os.environ.get("STUDIO_SEGREDO"):
        return os.environ["STUDIO_SEGREDO"]
    p = CONFIG / ".segredo"
    if not p.exists():
        CONFIG.mkdir(parents=True, exist_ok=True)
        p.write_text(secrets.token_hex(32))
        os.chmod(p, 0o600)
    return p.read_text().strip()


def admin_inicial():
    """Cria o primeiro usuário a partir de STUDIO_ADMIN_EMAIL / STUDIO_ADMIN_SENHA, se ainda não existir."""
    email, senha = os.environ.get("STUDIO_ADMIN_EMAIL"), os.environ.get("STUDIO_ADMIN_SENHA")
    if email and senha and email.strip().lower() not in _ler():
        adicionar(email, senha, "Administrador")
        print(f"Usuário inicial criado: {email}")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("adicionar", "remover", "listar"):
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == "listar":
        for e, u in _ler().items():
            print(f"{e}  ({u.get('nome', '')})")
        return
    if len(sys.argv) < 3:
        sys.exit("Informe o e-mail.")
    if cmd == "remover":
        remover(sys.argv[2])
        print("Removido.")
        return
    senha = os.environ.get("NOVA_SENHA") or getpass.getpass("Senha (mín. 8 caracteres): ")
    try:
        adicionar(sys.argv[2], senha, sys.argv[3] if len(sys.argv) > 3 else "")
    except ValueError as e:
        sys.exit(str(e))
    print("Usuário salvo.")


if __name__ == "__main__":
    main()
