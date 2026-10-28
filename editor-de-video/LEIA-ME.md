# Studio — editor de vídeo automático (white-label)

> **Para instalar num servidor para um cliente, veja [INSTALACAO.md](INSTALACAO.md).** A marca (nome, logo, cores e textos) fica em `config/marca.json`.

Você manda o vídeo, escolhe o modelo, e o sistema devolve **o vídeo 100% editado, a capa e a legenda do post**.

O que ele faz sozinho:

- corta silêncios e pausas
- legenda animada sincronizada com a fala (com palavra-chave em amarelo)
- título de abertura (gancho), números e gráficos animados
- insere suas **fotos e vídeos** (b-roll) na hora em que o assunto é falado
- trilha sonora que **abaixa sozinha** quando alguém fala (ducking)
- zoom a cada corte, cartão final com chamada
- **capa** 1080×1920 na identidade da marca
- **legenda do post** com gancho, texto, chamada e hashtags

## Como usar (pela página)

Um editor online que roda no computador ou no servidor (VPS) da escola.

```bash
pip install -r requirements.txt     # uma vez; precisa também de FFmpeg e Node.js 22+
```

```bash
python web/acesso.py adicionar voce@empresa.com
```

```bash
python web/servidor.py
```

Abra **http://localhost:8080**. Para a equipe acessar de outros computadores da rede, use `python web/servidor.py --publico`
e abra `http://<ip-do-computador>:8080` (na internet, coloque atrás de um acesso com senha, como um proxy com login).

Na página:

1. **Arraste o vídeo** e escolha o modelo. A análise (transcrição + corte de silêncio) começa sozinha.
2. **Texto:** clique numa palavra errada para corrigir.
3. **Elementos:** gancho, títulos, números, gráficos, nome na tela e cartão final. Arraste os blocos amarelos na linha do tempo.
4. **Mídias:** envie fotos e vídeos. O nome do arquivo diz quando entra; ou clique em "fixar aqui" no momento do vídeo.
5. **Música:** envie a trilha e ajuste o volume.
6. **Capa:** título, estilo e quadro.
7. **Gerar rascunho**, confira no seletor "Rascunho", e depois **Gerar vídeo final**.
8. **Legenda** e **Baixar:** edite/copie a legenda do post e baixe vídeo, capa e legenda.

A prévia em cima do vídeo é aproximada; o vídeo gerado é o oficial. Um vídeo é processado por vez (os outros esperam).
Os projetos ficam em `projetos/` (fora do git).

## Como usar (pelo chat)

Fale com o Agente Marketing (ou com o orquestrador):

> "Edita esse vídeo no modelo **Reels da marca**. As fotos estão nesta pasta e usa esta música."

Envie o vídeo no chat, coloque em `editor-de-video/entrada/` ou mande o link do Google Drive. O agente segue a skill
`agentes/agente-marketing/skills/editar-video/SKILL.md`: transcreve, mostra o texto para você conferir, monta o plano
(gancho, gráficos, onde entra cada foto, capa, legenda), faz um rascunho, confere e entrega o final.
**Nada é publicado sem aprovação da Laura ou da Layla.**

## Modelos

| id | Para quê |
|----|----------|
| `reels` *(padrão)* | Reels/TikTok nas cores da marca, legenda central, zoom nos cortes, fotos em tela cheia, cartão "Agende sua visita" |
| `viral-dinamico` | Dicas rápidas: cortes secos, legenda grande em caixa alta com palavra falada destacada, fotos em janela no topo |
| `institucional` | Vídeos da escola, eventos, comunicados: pausas naturais, legenda discreta, sem zoom, trilha mais presente. Mantém o formato original (serve para horizontal) |
| `depoimento` | Pais, alunos e professores: legenda em caixa escura, nome e papel da pessoa na tela |
| `referencia` | Estilo talking head com amarelo #F9D41A e palavra-chave na 2ª linha |

Criar um modelo novo: copie um `.json` de `modelos/`, mude o nome e os valores. Os campos estão descritos abaixo.

## Como usar (linha de comando)

```bash
pip install faster-whisper matplotlib pillow numpy      # uma vez; precisa também de FFmpeg e Node.js 22+
```

```bash
python editar.py --listar-modelos
```

```bash
python editar.py entrada/video.mp4 --modelo reels --preparar
```

```bash
python editar.py entrada/video.mp4 --modelo reels --midias entrada/fotos --musica musicas/trilha.mp3 --plano entrada/video.plano.json --rascunho
```

```bash
python editar.py entrada/video.mp4 --modelo reels --midias entrada/fotos --musica musicas/trilha.mp3 --plano entrada/video.plano.json
```

1. `--preparar` transcreve e corta. Gera `saida/<video>/transcricao.txt` com o tempo de cada frase **já no vídeo editado**.
2. `--rascunho` renderiza rápido para conferir.
3. Sem `--rascunho`: versão final.

Resultado em `saida/<nome-do-video>/`: `video-final.mp4`, `capa.jpg`, `legenda.txt`, `transcricao.txt`, `resumo.json`.

### Fotos e vídeos extras

Coloque numa pasta e passe `--midias pasta/`. **Dê às fotos o nome do assunto**: `biblioteca.jpg`, `robotica-aula.mp4`,
`quadra-esporte.jpg`. Quando a palavra "biblioteca" for falada, a foto da biblioteca entra. Arquivos sem nome
reconhecido são espalhados nos trechos livres. Para posição exata, use `broll` no plano.

### Música

`--musica arquivo.mp3` (ou uma pasta: sorteia uma). Guarde trilhas livres de direitos autorais em `musicas/`.
Sem música, o vídeo sai só com a voz. Volume e ducking ficam no modelo (`musica.volume`, `musica.ducking`).

## Plano do vídeo (opcional)

Um JSON com os ajustes deste vídeo. Todos os campos são opcionais. Tempos em segundos no vídeo **já editado**
(veja `transcricao.txt`).

```json
{
  "substituicoes": {"gente": "Agende"},
  "vocabulario": "Nome da empresa, nomes de pessoas, termos técnicos",
  "gancho": "3 erros que *todo mundo* comete",
  "pessoa": {"nome": "Mariana Souza", "papel": "Mãe do Pedro, 5º ano"},
  "overlays": [
    {"type": "stat", "value": 3000, "label": "livros na biblioteca", "prefix": "+", "start": 6.4, "duration": 2.8, "position": "top"},
    {"type": "chart", "kind": "bar", "title": "Alunos por ano", "labels": ["2024", "2025", "2026"], "values": [320, 380, 450], "start": 12, "duration": 3.5}
  ],
  "broll": [{"arquivo": "fachada.jpg", "inicio": 8.2, "duracao": 2.5, "layout": "janela"}],
  "encerramento": {"texto": "Matrículas *abertas*", "subtexto": "COLÉGIO CONECTA ARARAS", "duracao": 2.6},
  "capa": {"titulo": "Por dentro da *empresa*", "estilo": "faixa", "tempo": 3.4},
  "legenda": "Texto final do post...",
  "edicao": {"subtitles": {"style": "viral"}}
}
```

- `*palavra*` pinta de amarelo (gancho, capa, cartão final).
- `overlays`: títulos, lower thirds, gráficos (`chart`, `stat`, `pillars`, `cards`, `steps`, `numbered_title`).
  Formato completo em `motor/references/spec.md` e `motor/references/padrao.md`. **Nunca invente números**: use só dados reais.
- `capa.tempo` escolhe o quadro da capa; sem ele, o sistema escolhe o quadro mais nítido. `capa.imagem` usa uma foto sua.
  Estilos: `faixa`, `impacto`, `limpo`.
- `encerramento: null` tira o cartão final.
- `edicao` sobrescreve qualquer campo do modelo só para este vídeo.

## Campos de um modelo

| campo | o que controla |
|-------|----------------|
| `formato` | `"9:16"` recorta o centro e entrega 1080×1920; `"original"` mantém |
| `edicao` | motor: `font`, `theme` (cores), `silence` (corte), `subtitles` (estilo `ref`/`viral`/`clean`/`box`), `punch_in` (zoom), `replacements` |
| `gancho` | duração e posição do título de abertura |
| `broll` | `duracao_foto`, `duracao_video`, `layout` (`full`/`janela`), `evitar_inicio`, `evitar_fim`, `intervalo_min` |
| `musica` | `volume` (0–1), `ducking`, `fade_in`, `fade_out`, `arquivo` (padrão em `musicas/`) |
| `encerramento` | texto, subtexto e duração do cartão final (`null` = sem cartão) |
| `capa` | `estilo` e `selo` |
| `legenda` | `cta` e `hashtags` usados no rascunho automático |

## Estrutura

```
editor-de-video/
  editar.py        programa principal (vídeo + modelo -> vídeo final, capa, legenda)
  web/             a página do editor (servidor.py, acesso.py = login, static/)
  config/          marca.exemplo.json (copie para marca.json e edite: nome, logo, cores, textos)
  Dockerfile, docker-compose.yml, Caddyfile, instalar.sh   instalação no servidor (ver INSTALACAO.md)
  projetos/        projetos criados pela página (não vão para o git)
  modelos/         modelos de edição (.json)
  musicas/         trilhas livres de direitos (coloque aqui)
  entrada/         vídeos e fotos brutos (não vão para o git)
  saida/           resultados (não vão para o git)
  motor/           motor de edição: Whisper, corte de silêncio, composição HyperFrames (HTML+GSAP), fontes
```

## Limites conhecidos

- Render em CPU leva cerca de 5–6× a duração do vídeo (um Reel de 30 s leva uns 3 minutos).
- Fala com muito ruído de fundo: ajuste `silence.threshold_db` no plano (`-26` com ruído, `-38` se cortar fala baixa).
- Whisper erra nomes próprios. Por isso o fluxo sempre mostra a transcrição antes do render; corrija com `substituicoes`.
- A fonte da marca no motor é Montserrat (licença OFL, em `motor/fonts/`). Para outra, coloque o `.ttf` em `motor/fonts/` e mude `edicao.font` no modelo.
