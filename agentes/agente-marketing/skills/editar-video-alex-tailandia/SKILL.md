---
name: editar-video-alex-tailandia
description: Edita vídeos do vereador Alex Tailândia (@alextailandia, Câmara de Mogi Guaçu) no padrão aprovado — tela dividida com o Alex em cima e painel animado embaixo, cor de cinema, 1,2x mais rápido, legenda em duas camadas acima da divisória, animações sincronizadas com a fala, efeitos sonoros, música suspense, cartão final preto e capa de faixas azul/verde/amarelo. Use sempre que pedirem para editar, cortar ou fazer Reels/capa de um vídeo do Alex Tailândia ou de uma sessão da Câmara com ele.
---

## Skill: Editar vídeo do Alex Tailândia (padrão aprovado em 03/11/2026)

**Objetivo:** transformar uma fala do vereador Alex Tailândia em um Reels 9:16 pronto, no padrão que a Layla aprovou no vídeo das ambulâncias: vídeo final, capa e legenda do post.

**Ferramentas:** `editor-de-video/editar.py` com o modelo **`alex-tela-dividida`** e a marca do cliente em `editor-de-video/clientes/alex-tailandia/`. Rode tudo de dentro de `editor-de-video/` com `STUDIO_CONFIG=clientes/alex-tailandia`.

**Leia antes:** `editor-de-video/clientes/alex-tailandia/REGRAS.md`. O plano completo aprovado do vídeo das ambulâncias, para copiar a estrutura, está em `editor-de-video/clientes/alex-tailandia/plano-referencia-ambulancias.json`.

---

### Regras que nunca mudam

1. **Nunca colocar texto, título ou gráfico no rosto do Alex.** Isso vale para o vídeo, a capa e o cartão final. O gancho vai no painel de baixo (animação `alerta`), nunca em cima.
2. **Sem fonte serifada.** Tudo em Inter Display (pesada). Palavras de destaque mudam **só de cor**: amarelo `#FFDF00`, ou vermelho na faixa amarela da capa.
3. **Sem recortes de notícia.** As animações saem só da fala dele. Nunca criar manchete de jornal.
4. **Números só se ele falou ou se a equipe passou.** Quando ele citar um dado de fora (economia, pesquisa), avise a Layla antes de animar.
5. **Aprovação em duas etapas, sempre:**
   - (a) roteiro do painel em tabela;
   - (b) quadros de prévia de cada animação.
   
   Só depois disso gere o vídeo completo.
6. O nome é **Alex Tailândia** (Vereador · Mogi Guaçu). O perfil é **@alextailandia**.

### Configurações do padrão (já estão no modelo `alex-tela-dividida`)

| Item | Configuração |
|------|--------------|
| Formato | 1080×1920. Tela dividida: o Alex ocupa a metade de cima, recortado do vídeo 16:9. Embaixo fica o painel |
| Velocidade | **1,2×**, com a voz no tom normal (`velocidade: 1.2`) |
| Cor | `cinema`: mais contraste, saturação menor, leve vinheta |
| Cortes | Silêncio a partir de -32 dB e 0,3 s, com respiro de 0,06 s. Palavras transcritas nunca são cortadas |
| Zoom | A cada corte, só na metade de cima: 100% → 108% → 100% → 114% |
| Legenda | Estilo `camadas`: frase de apoio pequena (Inter Display SemiBold, branco 82%) em cima e palavras principais grandes (Inter Display Black) embaixo. A palavra-chave fica em amarelo e cada palavra entra desfocada → nítida. Posição: pé do vídeo de cima, logo acima da divisória (`pos_y: 0.445`), com sombra suave para leitura |
| Painel de baixo | Fundo azul-noite quase preto, sem faixa amarela na divisória. Ícones em traço fino e glitch nas palavras de impacto |
| Música | `suspense.mp3` (pasta do cliente), volume 0,16. Abaixa sozinha quando há fala |
| Efeitos sonoros | Ligados, sintetizados (sem direitos autorais): whoosh nas entradas, pop nos ícones, impacto + glitch no carimbo e no número, tique nos X, ding no cartão final |
| Cartão final | **Depois** da última fala, por 2,6 s, com fundo **preto**: "Siga **@alextailandia**" e "VEREADOR ALEX TAILÂNDIA" embaixo |
| Capa | Estilo `faixas` (ver abaixo) |

### Passo a passo

1. **Receber o vídeo.** Normalmente vem de um link do Drive com a gravação da sessão. Baixe numa pasta nova (`python3 -m gdown --folder <link> -O <pasta>`). As sessões costumam ter vários cortes ("CORTES CMMG[n]").
2. **Transcrever o vídeo inteiro** (`motor/scripts/transcribe.py`) e propor à Layla de 3 a 5 trechos de 30 a 90 s, um por tema, em tabela: tempo, assunto e gancho sugerido.
3. **Cortar o trecho escolhido** com `ffmpeg -ss INICIO -to FIM` (comece na primeira palavra forte e tire saudações como "Sr. Presidente"). Se der, reaproveite a transcrição do vídeo inteiro, deslocando os tempos, porque ela é mais precisa que a de um trecho curto.
4. **Preparar:**
   ```bash
   STUDIO_CONFIG=clientes/alex-tailandia python3 editar.py trecho.mp4 --modelo alex-tela-dividida --saida <saida> --preparar
   ```
   Isso acelera 1,2×, aplica a cor, transcreve e corta. Leia `<saida>/transcricao.txt` (tempos já no vídeo final) e o `corte.json` para pegar o tempo exato das palavras-chave.
5. **Conferir o texto.** Corrija com `substituicoes` (a marca já corrige "Mogi Guaçu", "INSS", "pátria" e similares).
6. **Montar o roteiro do painel** e mandar para aprovação, em tabela: tempo | ele fala | embaixo aparece. Use as animações abaixo, cada uma entrando na palavra que ela ilustra.
7. **Escrever o plano** (`plano.json`) com `overlays`, `capa.faixas` e `legenda` (veja o modelo de plano abaixo).
8. **Prévia quadro a quadro:**
   ```bash
   STUDIO_CONFIG=clientes/alex-tailandia python3 editar.py trecho.mp4 --modelo alex-tela-dividida --saida <saida> --plano plano.json --montar
   ```
   ```bash
   NODE_PATH=$(npm root -g) node motor/scripts/previa_quadros.js <saida>/_trabalho/hf <saida>/previa T1 T2 T3...
   ```
   Monte uma tira por animação (4 a 7 quadros cobrindo a entrada) e envie para aprovação.
9. **Render final** (cerca de 8 min para 50 s):
   ```bash
   STUDIO_CONFIG=clientes/alex-tailandia python3 editar.py trecho.mp4 --modelo alex-tela-dividida --saida <saida> --plano plano.json
   ```
   Confira de 6 a 9 quadros do `video-final.mp4` (`ffmpeg -ss T -frames:v 1`) e o volume (`volumedetect`: picos abaixo de 0 dB e a voz na frente).
10. **Entregar** `video-final.mp4`, `capa.jpg` e o texto de `legenda.txt`. A legenda do post é escrita na voz dele, direta e firme, com 3 ou 4 hashtags (`#MogiGuacu #CamaraMogiGuacu` + tema). Não publicar: a Layla aprova.

### Animações do painel (tipo → quando usar)

| Tipo | Campos | Uso |
|------|--------|-----|
| `alerta` | `texto`, `sub` | **Abertura com o gancho** (0,1 s até ~6 s). Ex.: "Pela *4ª vez*, sem ambulâncias", com sub "Atenção, Mogi Guaçu · Vereador Alex Tailândia" |
| `icones` | `n`, `rotulo`, `apagado` | Quando ele cita quantidades de coisas. Com `apagado: true` mostra o que "não chegou" |
| `carimbo` | `texto`, `batidas: [t1, t2]` | Palavra de condenação (IMPUGNADA, VETADO, CANCELADO), batendo na hora em que ele fala |
| `palavra` | `texto`, `apoio` | Uma palavra forte sozinha ("retrocesso"), com seta |
| `lista_x` | `itens: [{texto, inicio}]` | Críticas em sequência ("Não avança", "Não faz o básico") |
| `tentativas` | `n`, `marcas`, `rotulo`, `rotulo_em`, `sub`, `sub_em` | Contagens de vezes ("4ª vez"), com um X a cada tentativa |
| `faixas` | `itens: [{texto, inicio}]` | Fechamento com 2 frases, alternando esquerda e direita |

Nos textos, `*palavra*` sai em **amarelo**. Os tempos são do vídeo final (após aceleração e cortes): pegue no `corte.json` e entre cerca de 0,1 s antes da palavra. Não deixe duas animações ao mesmo tempo, com uma exceção: o carimbo pode ficar sobre `icones`.

### Capa de faixas (modelo da Layla)

- **Em cima:** o Alex, com o rosto livre (quadro automático ou `capa.imagem`).
- **No meio, sobre a divisória:** 3 faixas empilhadas com leve desalinhamento, em Montserrat ExtraBold e caixa alta:
  1. Azul `#1C3B95` com letra amarela `#FCE300`: quem fala/age ("ALEX TAILÂNDIA COBRA", "ALEX TAILÂNDIA PEDE")
  2. Verde `#0B7D3B` com letra branca: o assunto principal, grande
  3. Amarelo `#F7D115` com letra azul `#1C3B95`: o complemento, em 1 ou 2 linhas
- **Embaixo (opcional):** ícones, por exemplo `"icones": {"tipo": "ambulancia_x", "n": 3}`.
- Use `\n` para quebrar linha. O tamanho encolhe sozinho até caber.

### Modelo de plano

```json
{
  "substituicoes": {"falsetti": "Falsetti"},
  "overlays": [
    {"type": "alerta", "texto": "Pela *4ª vez*, sem ambulâncias", "sub": "Atenção, Mogi Guaçu · Vereador Alex Tailândia", "start": 0.1, "duration": 6.0},
    {"type": "icones", "n": 3, "rotulo": "3 *ambulâncias*", "start": 6.2, "duration": 8.2},
    {"type": "carimbo", "texto": "IMPUGNADA", "start": 11.2, "duration": 3.2, "batidas": [11.25, 12.8]},
    {"type": "palavra", "texto": "retrocesso", "apoio": "Esse é o", "start": 14.5, "duration": 3.0},
    {"type": "lista_x", "itens": [{"texto": "Não avança", "inicio": 19.0}, {"texto": "Não faz *o básico*", "inicio": 23.9}], "start": 17.55, "duration": 7.4},
    {"type": "tentativas", "n": 4, "marcas": [29.5, 29.75, 30.0, 30.25], "rotulo": "4ª *vez*", "rotulo_em": 30.5, "sub": "IMPUGNADA · CANCELADA", "sub_em": 32.4, "start": 25.0, "duration": 8.95},
    {"type": "icones", "n": 3, "apagado": true, "rotulo": "3 ambulâncias que *não chegaram*", "start": 34.0, "duration": 6.0},
    {"type": "faixas", "itens": [{"texto": "*Prejuízo* para a população", "inicio": 40.9}, {"texto": "Retrocesso *administrativo*", "inicio": 44.0}], "start": 40.05, "duration": 8.2}
  ],
  "capa": {"faixas": [
    {"texto": "Alex Tailândia cobra", "fundo": "#1C3B95", "cor": "#FCE300", "tam": 62},
    {"texto": "4ª vez sem\nambulâncias", "fundo": "#0B7D3B", "cor": "#FFFFFF", "tam": 86},
    {"texto": "Licitação impugnada\nde novo em Mogi Guaçu", "fundo": "#F7D115", "cor": "#1C3B95", "tam": 58}],
    "icones": {"tipo": "ambulancia_x", "n": 3}},
  "legenda": "Texto do post..."
}
```

Para mudar algo só neste vídeo, coloque a chave no plano: `"velocidade": 1.0`, `"efeitos_sonoros": false`, `"musica": {"volume": 0.12}`, `"encerramento": {...}`.

**Pronto quando:** roteiro e quadros aprovados, vídeo final conferido em quadros e no volume, e capa e legenda entregues.

**Aprendizados:** quando a Layla corrigir algo do estilo, atualize esta skill, o `REGRAS.md` do cliente e o modelo `clientes/alex-tailandia/modelos/alex-tela-dividida.json`.
