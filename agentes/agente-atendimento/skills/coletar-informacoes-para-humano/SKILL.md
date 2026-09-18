## Skill: Coletar Informações para Humano

**Objetivo:** Coletar dados específicos de um pai de aluno para subsidiar uma resposta ou ação que será finalizada por um membro da equipe humana.

**Disparo:** Identificação de que uma resposta ou ação requer dados adicionais do cliente antes de ser processada ou enviada pelo humano (invocado pela skill `triar-chamados-e-escalar` ou outras).

**Passos:**
1.  **Identificar Dados Faltantes:** Com base na demanda do pai e no contexto, determine quais informações específicas são necessárias (ex: número de matrícula, data de um evento específico, detalhes de uma ocorrência, etc.).
2.  **Solicitar Informações:** Faça perguntas claras e diretas ao pai via WhatsApp para coletar os dados. Exemplo: "Para que a Anne possa te ajudar da melhor forma, você poderia nos informar o número de matrícula do(a) aluno(a) e a data exata em que [evento/situação] ocorreu?"
3.  **Validar Resposta:** Se o pai fornecer as informações, valide se estão completas e compreensíveis. Se necessário, peça esclarecimentos.
4.  **Organizar Dados para Humano:** Compile as informações coletadas em um formato conciso e fácil de usar para a Anne ou o setor responsável. Inclua o contexto da conversa e a demanda original do pai.
5.  **Notificar Humano (se aplicável):** Se a coleta completar um chamado pendente, notifique a Anne que as informações necessárias foram obtidas.
6.  **Registro no Supabase:** Salve as informações coletadas no histórico da conversa do pai no Supabase.

**Pronto Quando:** As informações necessárias são coletadas do pai e organizadas para o humano.