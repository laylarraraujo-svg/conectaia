# Motor de Conteúdo — engenharia reversa (para o Alex Tailândia)

Análise do "Curso Motor de Conteúdo" (brunasantanna.com/sistema) para montar um sistema equivalente para o Alex.

> Seções 1–3: o sistema original. Seções 4–5: como ficou para o Alex. Seção 6: riscos.

> **Legenda:** ✅ = está escrito na página · 🔍 = dedução minha a partir do que a página mostra (a página não mostra arquivos, prompts ou código).

---

## 1. O que o sistema realmente é

Não é um software próprio. É um **workspace do Claude Code** (pasta + `CLAUDE.md` + skills + conectores). Dá para replicar sem programar.

| Peça | Evidência |
|---|---|
| Claude pago + aba **Code** + escolha de modelo + conectores | ✅ aulas 01–08 ("preparar o Claude: pasta, aba Code, modelo, conectores") |
| Skills instaláveis | ✅ aula "instalar as skills" e "o que é uma skill" |
| Google Drive como armazenamento | ✅ aula de Drive |
| Extensão do Chrome (Claude in Chrome) | ✅ aula própria. 🔍 Usada para ler perfis/concorrentes e operar o Metricool pela tela |
| **Metricool** como agendador e fonte de métricas | ✅ plano grátis: 20 posts/mês e sem LinkedIn |
| Sem n8n, Notion ou código próprio | ✅ não aparecem na página. 🔍 Tudo roda "na conversa" |

O preço de R$197 paga **prompts + skills + método**. A infraestrutura é o Claude e o Metricool.

---

## 2. Arquitetura (reconstruída)

```
                    ┌──────────────────────────────┐
  1ª vez ─────────▶ │  SKILL "CONSTRUTORA" (setup)  │  entrevista em 3 fases
                    │  salva progresso em arquivo   │  e retoma de onde parou
                    └──────────────┬───────────────┘
                                   ▼ gera
          ┌───────────────────────────────────────────────┐
          │  DOSSIÊ (arquivos de contexto)                 │
          │  perfil · público e dores · pilares · voz ·    │
          │  referências · estilo visual · estilo de edição│
          └──────────────┬────────────────────────────────┘
                         ▼ lido por todas as skills
 ┌──────────┐  ┌────────────────┐  ┌──────────┐  ┌───────────┐  ┌───────────────┐
 │ 1 RADAR  │─▶│ 2 CRIAÇÃO       │─▶│3 APROVA  │─▶│4 EDIÇÃO   │─▶│5 DISTRIBUIÇÃO │
 │ pesquisa │  │ 1 tema → Reel,  │  │ (humano) │  │ de vídeo  │  │ Metricool     │
 │ nicho +  │  │ carrossel,      │  │          │  │ cortes,   │  │ IG/TikTok/YT/ │
 │ números  │  │ LinkedIn, blog  │  │          │  │ legendas  │  │ Threads/LI    │
 └────▲─────┘  └────────────────┘  └──────────┘  └───────────┘  └──────┬────────┘
      │                                                                 ▼
      │                  ┌───────────────────────────────┐   ┌──────────────────┐
      └──────────────────│ 6 DASHBOARD (dados Metricool) │◀──│ métricas dos     │
                         └───────────────────────────────┘   │ posts            │
  fim de semana: NEWSLETTER compilada a partir dos posts      └──────────────────┘
```

---

## 3. Componente por componente

### 3.1 Skill "Construtora" (setup / onboarding) — a peça mais valiosa
- ✅ Entrevista a pessoa **uma vez** e monta um agente personalizado (público, dores). Lembra o progresso se a pessoa parar no meio.
- ✅ 3 fases: **leitura do perfil → pilares e entrevista → motor e primeiro roteiro**. Antes disso, "dossiê em 2 partes" e "encontrar referências".
- 🔍 **Como funciona por dentro:**
  1. **Leitura do perfil:** via extensão do Chrome, abre o Instagram, lê bio, os ~30 últimos posts e os mais vistos, e escreve `dossie/perfil.md` (temas, formatos, o que performa).
  2. **Entrevista:** perguntas em blocos (público, dores, oferta, tom, palavras proibidas, histórias pessoais). Cada resposta vai para um arquivo e um `estado-setup.md` marca a fase atual. É isso que permite "retomar de onde parou".
  3. **Motor:** com o dossiê pronto, escreve/ajusta o `CLAUDE.md` do agente de conteúdo e gera o primeiro roteiro como teste.
- **Por que importa:** a qualidade de tudo depende do dossiê. Um prompt de conteúdo genérico com um bom dossiê funciona melhor que um prompt sofisticado sem contexto.

### 3.2 Dossiê (engenharia de contexto)
- 🔍 Arquivos Markdown que todas as skills leem: `perfil`, `publico-e-dores`, `pilares`, `voz` (com exemplos reais de texto da pessoa), `referencias` (perfis que ela admira e por quê), `estilo-visual`, `estilo-de-edicao`.
- **No Alex:** `dossie/` com perfil, pilares, voz, público, formatos e regras-e-limites. As lacunas `[?]` são preenchidas pela skill `construtora`.

### 3.3 Skill 1 — Criação multiformato
- ✅ 1 tema → Reel + carrossel + post de LinkedIn + artigo, no tom da pessoa.
- 🔍 Estrutura provável do prompt:
  1. Lê o dossiê.
  2. Gera **um núcleo**: ideia central, 3 argumentos, 1 história, 1 CTA.
  3. Desdobra o núcleo por formato, cada um com seu template: Reel (gancho de 3s + roteiro falado + texto de tela), carrossel (capa + 6–8 slides + legenda), LinkedIn (texto longo), blog (artigo com SEO).
  4. Faz uma checagem de voz contra a lista de palavras proibidas.
- Tudo sai num único arquivo/pasta por pauta para aprovação.

### 3.4 Carrosséis em 6 estilos
- ✅ Estilos: clean/didático, dark/sóbrio, cor forte, editorial P&B, print de tela, mosaico. O design segue a marca da pessoa.
- 🔍 Técnica: Claude gera **HTML/CSS** de cada slide (1080×1350) com os tokens da marca e exporta em PNG (navegador headless). Por isso a página diz que "não precisa de Canva".
- **No Alex:** a skill `carrossel-instagram` da conta faz isso. A skill `gerar-carrossel` a chama com os estilos de mandato e a identidade visual dele.

### 3.5 Skill 2 — Edição de vídeo
- ✅ Grava bruto → pede na conversa cortes, legendas, títulos, animações. Remove silêncios, gaguejos e repetições, com legenda sincronizada palavra a palavra. Aula "ensinar seu estilo" e "animações".
- 🔍 Pipeline: **Whisper** (transcrição com tempo por palavra) → Claude decide os cortes pela transcrição → **FFmpeg** corta e queima a legenda → animações via HTML renderizado em vídeo. Por isso exige computador (Windows/Mac) e não celular.
- **No Alex:** a skill `video-editor` da conta já faz esse pipeline. `editar-video` e `cortes-da-tribuna` a usam com o estilo dele.

### 3.6 Distribuição
- ✅ Agenda e publica em várias redes no melhor horário, **nada sai sem aprovação**. Metricool.
- 🔍 Provavelmente via extensão do Chrome operando o Metricool pela tela, ou importação em lote. O "melhor horário" é o que o próprio Metricool sugere.
- **No Alex:** Metricool (como a Bruna) ou Windsor.ai. Impulsionar post político exige autorização da Meta para anúncios sobre política.

### 3.7 Dashboard, radar diário e newsletter
- ✅ Dashboard com dados do Metricool que se atualiza sozinho. Radar diário. Newsletter compilada dos posts quando pedida.
- 🔍
  - **Dashboard:** página HTML que lê as métricas e mostra alcance, seguidores e top posts.
  - **Radar:** tarefa agendada que pesquisa a web (tendências do nicho, notícias, concorrentes) e entrega 3–5 pautas com justificativa.
  - **Newsletter:** junta os posts aprovados da semana e reescreve num formato de e-mail.
- **No Alex:** a skill `relatorio-semanal` (Windsor.ai ou prints dos Insights + `instagram-analyzer`). O radar vira `radar-de-pautas`, com fontes oficiais da Câmara e da Prefeitura.

---

## 4. Como ficou para o Alex

| Peça da Bruna | No motor do Alex | Onde |
|---|---|---|
| Skill Construtora | entrevista sobre mandato, pilares, voz e limites | `.claude/skills/construtora` |
| Dossiê | perfil, pilares, voz, público, formatos, **regras e limites** | `dossie/` |
| Radar diário | radar semanal: Câmara, Diário Oficial, transparência, notícias locais | `.claude/skills/radar-de-pautas` |
| Criação multiformato | 1 pauta → tribuna, tela dividida, bairro, carrossel, legendas | `.claude/skills/criar-conteudo` |
| Edição de vídeo | edição + **cortes da tribuna** (1 sessão → 3–5 vídeos) | `.claude/skills/editar-video`, `cortes-da-tribuna` |
| Carrossel 6 estilos | 5 estilos de mandato: Documento, Explicando, Como votei, Antes/depois, Frase da tribuna | `.claude/skills/gerar-carrossel` |
| Dashboard | relatório de sexta com comentários que pedem ação | `.claude/skills/relatorio-semanal` |
| Newsletter | (opcional) resumo semanal para lista/canal de WhatsApp do gabinete | a criar |

**Adaptações para mandato:**
- toda afirmação precisa de fonte;
- regras eleitorais, de honra e de imagem de menores e famílias atípicas;
- vereador não promete obra;
- IA não fabrica imagem, voz nem cena de pessoa ou lugar real.

Detalhes em `dossie/regras-e-limites.md`.

## 5. Plano de construção

| Fase | Entrega | Status |
|---|---|---|
| 1. Estrutura | CLAUDE.md, dossiê com lacunas, 7 skills, modelo de pauta | ✅ feito |
| 2. Setup com o Alex | rodar `construtora` (cerca de 2 h, pode ser em partes) | ⬜ |
| 3. Identidade visual | cores, fonte, foto → `dossie/identidade-visual.md` | ⬜ |
| 4. Primeiro ciclo | radar → 3 pautas → conteúdo → aprovação → publicar | ⬜ |
| 5. Primeira sessão | `cortes-da-tribuna` com o vídeo de uma sessão real | ⬜ |
| 6. Agendamento e métricas | Metricool ou Windsor.ai + relatório de sexta | ⬜ |

## 6. Riscos e limites

- **Números da página são autodeclarados** (+19k seguidores em 30 dias, Reel de 498k views). O resultado vem do método e da consistência, não da ferramenta.
- **Publicação automática** no Instagram exige conta profissional ligada a uma página do Facebook. Vídeo/Reel por API tem mais restrições que imagem. Testar antes de prometer à equipe.
- **Dependência da extensão do Chrome:** automações que operam pela tela quebram quando o site muda. Preferir API/conector (Windsor.ai, Metricool) quando houver.
