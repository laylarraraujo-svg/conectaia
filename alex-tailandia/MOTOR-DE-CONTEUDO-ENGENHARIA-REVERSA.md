# Motor de Conteúdo — engenharia reversa (para o Alex Tailândia)

Análise do "Curso Motor de Conteúdo" (brunasantanna.com/sistema) para montar um sistema equivalente para o Alex.

> ⚠️ **Rascunho:** as seções 1–3 e 8 explicam o sistema da Bruna e valem para o Alex. As seções 4–7 ainda estão escritas para o Colégio Conecta e serão reescritas quando tivermos o @, o nicho e os formatos do Alex.

> **Legenda:** ✅ = está escrito na página · 🔍 = dedução minha a partir do que a página mostra (a página não mostra arquivos, prompts ou código).

---

## 1. O que o sistema realmente é

Não é um software próprio. É um **workspace do Claude Code** (pasta + `CLAUDE.md` + skills + conectores), o mesmo formato que o squad do Conecta já usa.

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
- **No Conecta, metade já existe:** `contexto/voz-da-marca.md`, `contexto/sobre-a-empresa.md`, `contexto/regras-da-casa.md`, `contexto/sazonalidade.md`, `design-system/`. Faltam pilares, público/dores (visão de conteúdo), referências e um "banco de histórias" da escola.

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
- **Atalho para o Conecta:** a skill `carrossel-instagram` já está disponível nesta conta e faz exatamente isso. Basta alimentá-la com `design-system/tokens.md`. Também há conector do **Canva**, se a Laura preferir editar lá.

### 3.5 Skill 2 — Edição de vídeo
- ✅ Grava bruto → pede na conversa cortes, legendas, títulos, animações. Remove silêncios, gaguejos e repetições, com legenda sincronizada palavra a palavra. Aula "ensinar seu estilo" e "animações".
- 🔍 Pipeline: **Whisper** (transcrição com tempo por palavra) → Claude decide os cortes pela transcrição → **FFmpeg** corta e queima a legenda → animações via HTML renderizado em vídeo. Por isso exige computador (Windows/Mac) e não celular.
- **Atalho:** a skill `video-editor` desta conta já faz esse pipeline (Whisper local + corte de silêncio + legendas estilo Reels + títulos/gráficos animados). Falta só um arquivo `estilo-de-edicao.md` do Conecta.

### 3.6 Distribuição
- ✅ Agenda e publica em várias redes no melhor horário, **nada sai sem aprovação**. Metricool.
- 🔍 Provavelmente via extensão do Chrome operando o Metricool pela tela, ou importação em lote. O "melhor horário" é o que o próprio Metricool sugere.
- **No Conecta:** o agente de marketing hoje prevê n8n para isso (`agentes/agente-marketing/skills/planejar-e-agendar-publicacoes`). O conector n8n **falhou ao conectar nesta sessão**. Alternativas: Metricool (como a Bruna) ou o conector **Windsor.ai**, que já está ligado e consegue publicar posts de imagem no Instagram.

### 3.7 Dashboard, radar diário e newsletter
- ✅ Dashboard com dados do Metricool que se atualiza sozinho. Radar diário. Newsletter compilada dos posts quando pedida.
- 🔍
  - **Dashboard:** página HTML que lê as métricas e mostra alcance, seguidores e top posts.
  - **Radar:** tarefa agendada que pesquisa a web (tendências do nicho, notícias, concorrentes) e entrega 3–5 pautas com justificativa.
  - **Newsletter:** junta os posts aprovados da semana e reescreve num formato de e-mail.
- **No Conecta:** Windsor.ai lê Instagram, Meta Ads e GA4, o que dá dados reais para o dashboard. A skill `instagram-analyzer` faz a análise de top/piores posts. Tarefas agendadas do Claude podem rodar o radar sem n8n.

---

## 4. O que já temos e o que falta

| Peça do Motor | Situação no Conecta | Ação |
|---|---|---|
| Workspace + CLAUDE.md por agente | ✅ existe (`agentes/agente-marketing`) | estender |
| Dossiê / contexto | 🟡 voz, empresa, regras, sazonalidade, design system | criar pilares, público/dores, referências, banco de histórias |
| Skill de setup/entrevista | ❌ | criar `construtora` (só precisa rodar 1 vez) |
| Criação multiformato | 🟡 `criar-conteudo-para-redes` (genérica, 1 formato) | reescrever: 1 tema → 4 formatos |
| Carrossel visual | 🟡 skill `carrossel-instagram` disponível | plugar no design system, definir 2–3 estilos da marca |
| Ganchos | 🟡 skills `hooks-magneticos`, `gancho-dos-3-segundos` | usar dentro da criação |
| Edição de vídeo | 🟡 skill `video-editor` disponível | criar `estilo-de-edicao.md` |
| Agendamento | 🟡 previsto via n8n (desconectado) | decidir: Metricool ou Windsor.ai |
| Métricas/dashboard | 🟡 `monitorar-campanhas-e-metricas` (via n8n) | trocar fonte para Windsor.ai |
| Radar | 🟡 `analisar-concorrencia-e-tendencias` | virar tarefa agendada semanal |
| Newsletter para pais | ❌ | nova skill (ótimo para retenção de famílias matriculadas) |

---

## 5. Estrutura de pastas proposta

```
agentes/agente-marketing/
├── CLAUDE.md                     ← ganha a seção "Motor de Conteúdo" e o loop semanal
├── memory.md
├── dossie/
│   ├── estado-setup.md           ← em que fase a entrevista parou
│   ├── perfil-instagram.md       ← leitura do @ da escola (temas, formatos, top posts)
│   ├── publico-e-dores.md        ← pais de 1–17 anos: medos, desejos, objeções
│   ├── pilares.md                ← 4–5 pilares (ex.: bilíngue, desenvolvimento integral, rotina/bastidores, parceria família-escola, prova social)
│   ├── referencias.md            ← perfis de escolas/marcas admiradas e o porquê
│   ├── banco-de-historias.md     ← casos reais (com autorização de imagem)
│   └── estilo-de-edicao.md       ← ritmo, legenda, cores, vinhetas
├── pautas/
│   └── AAAA-MM-DD-tema/          ← 1 pasta por pauta
│       ├── nucleo.md
│       ├── reel.md  carrossel.md  linkedin.md  blog.md
│       ├── carrossel/slide-01.png …
│       └── status.md             ← rascunho → aprovado (Laura) → agendado → publicado
└── skills/
    ├── construtora/              ← NOVA: setup em 3 fases
    ├── criar-conteudo-para-redes/← REESCRITA: 1 tema → 4 formatos
    ├── gerar-carrossel/          ← NOVA: chama carrossel-instagram com o design system
    ├── editar-video/             ← NOVA: chama video-editor com estilo-de-edicao.md
    ├── planejar-e-agendar-publicacoes/
    ├── monitorar-campanhas-e-metricas/
    ├── analisar-concorrencia-e-tendencias/  ← vira o "radar"
    └── newsletter-familias/      ← NOVA
```

---

## 6. Adaptações obrigatórias para uma escola

A Bruna vende para criador de conteúdo pessoa física. Escola tem regras que o curso não cobre:

1. **Imagem de menores (ECA + LGPD):** nenhuma foto/vídeo de aluno sem autorização de uso de imagem assinada. A skill deve checar isso no `status.md` antes de liberar a aprovação.
2. **Regras da casa em todos os prompts:** nunca prometer resultado acadêmico, nunca citar valores ou descontos, nunca comparar com outras escolas. A checagem de voz da skill de criação deve validar isso.
3. **Voz Premium e Motivadora:** sem gírias. O "tom da pessoa" da Bruna aqui é o tom institucional de `voz-da-marca.md`.
4. **CTA único:** todo conteúdo de captação leva para "agende uma visita". Esse lead cai no **Agente Vendas**, que tem prioridade máxima no squad.
5. **Aprovação humana:** Laura ou Layla (já definido no CLAUDE.md do marketing).
6. **Sazonalidade:** de julho a dezembro, o radar e a criação priorizam pautas de matrícula. Em janeiro, pautas de boas-vindas e rotina para pais.
7. **Quem grava:** a "pessoa na câmera" pode ser coordenação, professores ou alunos (com autorização). O motor deve gerar roteiros curtos para quem não é criador profissional.

---

## 7. Plano de construção em fases

| Fase | Entrega | Esforço |
|---|---|---|
| **1. Dossiê** | Rodar a skill `construtora` uma vez com a Laura: lê o Instagram da escola e entrevista sobre pilares, público e histórias | 1 tarde |
| **2. Criação** | Reescrever `criar-conteudo-para-redes` para gerar 1 tema → 4 formatos em `pautas/` | 1–2 h |
| **3. Visual** | `gerar-carrossel` com 2–3 estilos da marca (sobre o design system) | 1–2 h |
| **4. Vídeo** | `editar-video` + `estilo-de-edicao.md`, testado com 1 vídeo bruto real | 1–2 h |
| **5. Distribuição + métricas** | Escolher Metricool ou Windsor.ai, ligar agendamento e dashboard | 1 tarde |
| **6. Rotina** | Tarefas agendadas: radar segunda de manhã, relatório sexta, newsletter para famílias quinzenal | 30 min |

**Rotina-alvo (igual à da Bruna):** segunda o radar entrega pautas → Laura escolhe 3 → o motor gera tudo → Laura aprova em ~30–40 min/semana → agendamento → sexta o relatório entra no resumo executivo do Orquestrador.

**Custos:** Claude (já pago). Metricool é opcional: o plano grátis tem 20 posts/mês e não tem LinkedIn, e o pago custa a partir de US$20/mês, segundo a página. Windsor.ai já está conectado nesta conta (confirmar o plano).

---

## 8. Riscos e limites

- **Números da página são autodeclarados** (+19k seguidores em 30 dias, Reel de 498k views). O resultado vem do método e da consistência, não da ferramenta.
- **Publicação automática** no Instagram exige conta profissional ligada a uma página do Facebook. Vídeo/Reel por API tem mais restrições que imagem. Testar antes de prometer à equipe.
- **Dependência da extensão do Chrome:** automações que operam pela tela quebram quando o site muda. Preferir API/conector (Windsor.ai, Metricool) quando houver.
- **n8n está desconectado nesta sessão** (erro 404 ao conectar). Se quiser manter o n8n como orquestrador, é preciso reconectar.
- **`mestre-starter-kit/` está vazio:** só tem o `COMECE-AQUI.md`, e o zip do curso não foi descompactado. Quando for descompactado, vale revisar este plano contra as skills `tutor-*`.
