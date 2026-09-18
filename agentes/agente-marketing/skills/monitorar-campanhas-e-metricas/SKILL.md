## Skill: Monitorar Campanhas e Métricas

**Objetivo:** Acompanhar o desempenho das campanhas de marketing e publicações, identificando tendências e alertas.

**Disparo:** Diariamente ou semanalmente (via n8n cron) para campanhas ativas, ou mediante solicitação da Laura.

**Passos:**
1.  **Coletar Dados:** Utilize o n8n para conectar-se às APIs do Meta Ads e outras plataformas (se aplicável) para coletar métricas chave (engajamento, alcance, impressões, cliques, conversões, custo por resultado).
2.  **Analisar Desempenho:** Compare as métricas coletadas com as metas estabelecidas e com o histórico. Identifique:
    *   Campanhas com bom desempenho.
    *   Campanhas com desempenho abaixo do esperado.
    *   Aumento ou diminuição de gastos.
    *   Comentários ou interações relevantes (positivas ou negativas).
3.  **Gerar Relatório Resumido:** Compile um relatório conciso com os principais insights e alertas. Exemplo: 'Campanha X com CPA 20% acima do esperado, engajamento bom. Campanha Y com bom retorno, sugerir aumento de orçamento.'
4.  **Escalonar Alertas:** Se identificar comentários ruins, gasto abusivo ou campanha sem retorno, acione imediatamente o processo de escalonamento para a Laura, conforme as regras da casa.
5.  **Salvar Métricas:** Registre as métricas coletadas e o relatório resumido no Supabase para histórico e futuras análises.

**Pronto Quando:** As métricas são coletadas, analisadas, o relatório é gerado e alertas são escalonados (se necessário).