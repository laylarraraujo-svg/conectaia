## Skill: Triar Chamados e Escalar para Humano

**Objetivo:** Entender demandas complexas ou específicas de pais de alunos e coletar informações para escalonar para a equipe humana.

**Disparo:** Mensagem de um pai de aluno com uma demanda que não pode ser resolvida com respostas comuns ou que exige intervenção de um setor específico (ex: coordenação, financeiro, secretaria).

**Passos:**
1.  **Reconhecer Demanda Complexa:** Identifique que a solicitação do pai vai além das dúvidas frequentes e requer atenção humana.
2.  **Coletar Informações Detalhadas:** Faça perguntas direcionadas para obter todos os dados necessários para o humano responsável. Exemplo:
    *   "Para que eu possa direcionar sua solicitação da melhor forma, poderia me dar mais detalhes sobre [ponto principal da demanda]?"
    *   "Qual o nome completo do(a) aluno(a) e a turma?"
    *   "Desde quando essa situação ocorre?"
    *   "Você já tentou contato com quem sobre isso?"
3.  **Resumir e Preparar para Escalonamento:** Organize as informações coletadas em um formato claro e objetivo para a Anne (Recepcionista) ou a coordenação. Inclua:
    *   Nome do pai/responsável.
    *   Nome e turma do aluno.
    *   Resumo da demanda do pai.
    *   Informações adicionais coletadas.
    *   Sugestão de setor para o qual a demanda deve ser encaminhada (ex: 'Para Coordenação Infantil', 'Para Financeiro').
4.  **Notificar Humano:** Envie um alerta interno (via n8n para um canal de comunicação da equipe, ex: grupo de WhatsApp interno ou e-mail) com o resumo do chamado e a sugestão de encaminhamento, marcando a Anne como responsável pela próxima ação.
5.  **Comunicar ao Cliente:** Informe ao pai que a demanda foi recebida e está sendo encaminhada internamente para o setor responsável. Exemplo: "Entendido, [Nome do Pai]. Sua solicitação sobre [resumo da demanda] foi registrada e já encaminhada para nossa equipe interna. Em breve, entraremos em contato com a solução ou os próximos passos."
6.  **Registro no Supabase:** Salve todo o histórico da triagem e o status de escalonamento no Supabase.

**Pronto Quando:** As informações são coletadas, resumidas, o humano é notificado e o cliente é informado sobre o encaminhamento.