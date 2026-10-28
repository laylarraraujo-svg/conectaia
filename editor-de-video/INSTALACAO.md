# Instalação no servidor (uma instalação por cliente)

O Studio roda num servidor Linux e a equipe do cliente acessa pelo navegador, com login. Cada cliente tem a
própria instalação, com nome, logo, cores e textos dele.

## 1. Servidor

| Uso | Servidor sugerido |
|-----|-------------------|
| Teste / poucos vídeos por dia | 4 vCPU, 8 GB de RAM, 80 GB de disco |
| Uso diário da equipe | 8 vCPU, 16 GB de RAM, 160 GB de disco |

Ubuntu 22.04 ou 24.04. Qualquer VPS serve (Hostinger, Hetzner, DigitalOcean, Contabo...). Libere as portas 80 e 443.
Render de vídeo é pesado: um Reel de 30 s leva cerca de 2–3 min com 4 vCPU.

## 2. Copiar o sistema para o servidor

Só a pasta `editor-de-video/` vai para o servidor. Duas formas:

**a) Pelo GitHub (recomendado, facilita atualizar):** no servidor,

```bash
git clone https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git
```

```bash
cd SEU-REPOSITORIO/editor-de-video
```

Repositório privado: o GitHub pede usuário e um *token* (Settings → Developer settings → Personal access tokens) no lugar da senha.

**b) Por arquivo:** baixe o ZIP do repositório, envie a pasta `editor-de-video` para o servidor (ex.: com FileZilla/SFTP).

## 3. Instalar

Dentro da pasta `editor-de-video`, no servidor:

```bash
sudo ./instalar.sh
```

O instalador:
- instala o Docker se faltar;
- pergunta o **domínio** (ex.: `studio.cliente.com.br`). Deixe vazio para testar pelo IP do servidor;
- pergunta o **e-mail e a senha do primeiro login**;
- constrói e liga tudo. A primeira vez leva de 5 a 15 minutos (baixa o reconhecimento de voz e o navegador de render).

No fim ele mostra o endereço de acesso.

**Com domínio:** crie no DNS do domínio um registro **A** apontando para o IP do servidor *antes* de instalar.
O HTTPS (cadeado) é emitido sozinho.

**Sem domínio:** acesse `http://IP-DO-SERVIDOR`. Sem cadeado: use só para teste.

## 4. Colocar a marca do cliente

Edite `dados/config/marca.json` no servidor:

```json
{
  "produto": "Vida Studio",
  "empresa": "Clínica Vida",
  "assinatura": "CLÍNICA VIDA",
  "perfil": "@CLINICAVIDA",
  "logo": "logo.png",
  "cor": "#0F5C4A",
  "destaque": "#7CE0B5",
  "texto": "#FFFFFF",
  "fonte": "Montserrat",
  "chamada_final": "Agende sua *consulta*",
  "cta": "Agende sua avaliação pelo link da bio.",
  "hashtags": ["#ClinicaVida", "#Saude"],
  "substituicoes": {"vida": "Vida"},
  "voz": "Acolhedora e clara.",
  "aviso_publicacao": "Revise antes de publicar."
}
```

| campo | onde aparece |
|-------|--------------|
| `produto` | nome do sistema no topo e na tela de login |
| `empresa`, `assinatura`, `perfil` | cartão final e selo da capa |
| `logo` | arquivo (PNG com fundo transparente) dentro de `dados/config/`: topo da página, login, capa e cartão final |
| `cor`, `destaque`, `texto` | cores da página, das legendas, títulos, capa e cartão final |
| `fonte` | fonte dos vídeos e da capa (coloque o `.ttf` em `motor/fonts/` se não for Montserrat) |
| `chamada_final` | texto do cartão final (`*palavra*` destaca) |
| `cta`, `hashtags` | legenda automática do post |
| `substituicoes` | correções automáticas da transcrição (nomes da marca) |
| `voz`, `aviso_publicacao` | dicas mostradas para a equipe na página |

Depois de editar:

```bash
docker compose restart studio
```

Modelos próprios do cliente: copie um arquivo de `modelos/` para `dados/config/modelos/`, edite e reinicie.
Trilhas padrão: `dados/config/musicas/`.

## 5. Usuários

```bash
docker compose exec studio python web/acesso.py adicionar pessoa@cliente.com.br
```

```bash
docker compose exec studio python web/acesso.py listar
```

```bash
docker compose exec studio python web/acesso.py remover pessoa@cliente.com.br
```

Senhas ficam só como hash. Após 8 tentativas erradas, o IP espera 10 minutos.

## 6. Dia a dia

| Tarefa | Comando (na pasta `editor-de-video`) |
|--------|--------------------------------------|
| Ver se está rodando | `docker compose ps` |
| Ver o log | `docker compose logs -f studio` |
| Reiniciar | `docker compose restart` |
| Atualizar para a versão nova | `git pull` e depois `sudo ./instalar.sh` |
| Backup | copie a pasta `dados/` (marca, usuários e todos os vídeos) |

Vídeos ocupam espaço: cada projeto guarda o original, os cortes e os renders. Apague projetos antigos pela página
(Baixar → Apagar este projeto) ou aumente o disco.

## Licenças dos componentes

Whisper/faster-whisper e Flask (MIT), HyperFrames (Apache-2.0), FFmpeg (LGPL/GPL, usado como programa separado),
fonte Montserrat (OFL). O GSAP (animações) usa a licença gratuita da Webflow, que permite uso comercial, exceto em
ferramentas que concorram com o construtor visual de animações da Webflow. Antes de vender em escala, confirme com
a Webflow que o seu caso está coberto.
