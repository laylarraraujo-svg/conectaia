## Skill: Recepcionar e Qualificar Lead

**Objetivo:** Iniciar a interação com um novo lead via WhatsApp, coletar informações essenciais e prepará-lo para o agendamento.

**Disparo:** Nova mensagem de um número não identificado como cliente ou lead em andamento no WhatsApp (via webhook do n8n).

**Passos:**
1.  **Saudação Premium:** Envie uma mensagem de boas-vindas calorosa e profissional, utilizando a voz da marca. Exemplo: "Olá! Que alegria ter você conectado ao Colégio Conecta Araras. Estamos aqui para ajudar a construir um futuro brilhante para seu filho(a)."
2.  **Coleta de Dados Iniciais:** Solicite as seguintes informações para iniciar a qualificação:
    *   Nome completo do responsável.
    *   Nome do aluno(a).
    *   Idade ou turma de interesse (ex: Educação Infantil, Fundamental I, Ensino Médio).
    *   Escola atual do aluno(a).
    *   Você pode perguntar: "Para que possamos direcionar melhor nosso atendimento, poderia nos informar seu nome completo, o nome e a idade/turma de interesse do(a) aluno(a), e a escola em que ele(a) estuda atualmente?"
3.  **Apresentação Breve da Proposta:** Com base nas informações coletadas, apresente de forma concisa e motivadora a proposta de ensino do Colégio Conecta Araras, destacando o programa bilíngue e a preparação além do currículo. Utilize o contexto de `sobre-a-empresa.md` e `voz-da-marca.md`.
4.  **Direcionamento para Agendamento:** Informe que o próximo passo ideal é um encontro com um especialista para detalhar a proposta e discutir valores. Exemplo: "Para que você possa conhecer em detalhes nossa metodologia, nossa estrutura e entender como podemos potencializar o desenvolvimento do seu filho(a), o ideal é agendarmos um encontro exclusivo com um de nossos especialistas. Nele, poderemos apresentar todas as informações, inclusive sobre mensalidades e condições."
5.  **Invocar Skill de Agendamento:** Proponha ao lead a execução da skill `agendar-encontro-especialista`.
6.  **Registro no Supabase:** Salve todas as informações coletadas e o histórico da conversa no Supabase, associado ao número de WhatsApp do lead.

**Pronto Quando:** O lead fornece as informações solicitadas e aceita a proposta de agendamento.