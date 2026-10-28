# Motor de Conteúdo do Alex Tailândia: comece aqui

Sistema inspirado no "Motor de Conteúdo" da Bruna Santanna, adaptado para o mandato de um vereador. A análise do sistema original está em `MOTOR-DE-CONTEUDO-ENGENHARIA-REVERSA.md`.

## Como usar
1. Abra **esta pasta** (`alex-tailandia/`) no Claude Code (aba Code, no computador). O `CLAUDE.md` e as skills carregam sozinhos.
2. Mande: **"vamos configurar"**. A skill `construtora` entrevista o Alex (umas 2 horas, pode ser em partes) e completa o dossiê.
3. Depois, toda semana:
   - **segunda:** "radar de pautas"
   - **depois da sessão:** mande o vídeo, "cortes da tribuna"
   - **pauta escolhida:** "cria o conteúdo de [pauta]"
   - **vídeo gravado:** mande o arquivo, "edita"
   - **sexta:** "relatório da semana"

## O que tem aqui
| Pasta/arquivo | Para quê |
|---|---|
| `CLAUDE.md` | instruções do motor (ciclo semanal e regras) |
| `dossie/` | quem é o Alex, voz, público, pilares, formatos, **regras e limites** |
| `pautas/_modelo/` | modelo de pasta para cada conteúdo |
| `.claude/skills/` | construtora, radar-de-pautas, criar-conteudo, cortes-da-tribuna, gerar-carrossel, editar-video, relatorio-semanal |

## Pré-requisitos
- Claude pago, no computador (Windows/Mac) com Claude Code.
- Skills da conta ativas: `carrossel-instagram`, `video-editor`, `hooks-magneticos`, `gancho-dos-3-segundos`, `instagram-analyzer`.
- Opcional: extensão do Chrome (ler o Instagram), Metricool (agendar), Windsor.ai (métricas).

## Diferenças em relação ao sistema da Bruna
- **Fontes obrigatórias:** todo fato precisa de documento.
- **Regras eleitorais, de honra e de imagem de menores** (`dossie/regras-e-limites.md`).
- **Formatos de mandato:** cortes da tribuna, tela dividida com documento e série "Voltei no bairro".
- **IA não fabrica imagem, voz nem cena de pessoa ou lugar real.**
