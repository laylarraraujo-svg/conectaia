## Skill: Resumir Notícias de Mogi Guaçu

**Objetivo:** Entregar à Layla um resumo curto e priorizado das notícias mais recentes de Mogi Guaçu (SP).

**Disparo:** 6h52, 10h52 e 15h52 (horário de Brasília), ou quando a Layla pedir.

**Fontes:**
*   Sites
    *   Mogi Guaçu Acontece — https://mogiguacuacontece.com.br/
    *   Câmara Municipal — https://camaramogiguacu.sp.gov.br/pautas-das-sessoes/ (destacar sessões previstas e projetos em votação; abrir o PDF da pauta mais recente)
*   Instagram
    *   https://www.instagram.com/conexaomogiana/
    *   https://www.instagram.com/zatumnoticias/
    *   https://www.instagram.com/mogi.guacuacontece/
    *   https://www.instagram.com/mogiguacu.noticias/
    *   https://www.instagram.com/portaltribunadoguacu/
    *   https://www.instagram.com/portalvozdoguacu/
*   **Como ler o Instagram:** conector Windsor.ai `instagram_public` → `get_data` com os campos `account_name`, `media_timestamp`, `media_caption`, `media_permalink`, `media_type` e `date_from`/`date_to` cobrindo a janela. Horários vêm em UTC (subtrair 3h). Use o `media_permalink` como link da fonte.
*   **Filtro do Instagram:** esses perfis postam muito sobre outras cidades (Campinas, Indaiatuba, Valinhos) e política nacional. Mantenha só o que é de Mogi Guaçu ou afeta a cidade (ex.: SP-340).
*   Complemento (se uma fonte falhar): busca na web por "Mogi Guaçu" + data.

**Passos:**
1.  **Definir a janela:** manhã (6h52) = últimas 24h; meio da manhã (10h52) = desde 6h52; tarde (15h52) = desde 10h52. Consulte `edicoes/` para não repetir itens.
2.  **Coletar:** leia cada fonte. Se falhar, anote o motivo e siga.
3.  **Juntar repetidas:** a mesma notícia em várias fontes vira um único item, citando a fonte principal.
4.  **Filtrar e priorizar:** segurança e ocorrências > trânsito e obras > saúde > serviços públicos (água, energia, coleta) > prefeitura e Câmara > economia local > eventos > clima que afete a cidade. Ignore propaganda, colunas de opinião e posts sem notícia.
5.  **Escrever:** do mais ao menos importante.
6.  **Entregar:** no chat e por e-mail (laylarraraujo@gmail.com, alextailandiacontato@gmail.com e alextailandia.redesociais@hotmail.com, assunto "Notícias de Mogi Guaçu — <edição> <data>"). Salve em `edicoes/AAAA-MM-DD-<edicao>.md`.

**Formato:**
```
📰 Edição da <manhã|meio da manhã|tarde> — <dd/mm/aaaa>, <hh:mm>

1. **<Título em uma frase>**
   <Resumo de 1 a 2 linhas, com suas palavras.>
   Fonte: [<nome>](<link>)

⚠️ Falhas: <fonte> — <o que falhou> (uma linha por falha)
```
Se não houver nada novo relevante: "Nada novo relevante em Mogi Guaçu desde a última edição."

**Pronto Quando:** o resumo foi entregue no chat, enviado por e-mail (ou a falha foi informada) e salvo em `edicoes/`.
