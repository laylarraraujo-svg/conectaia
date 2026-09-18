## Guia de Implementação do Squad AI Colégio Conecta Araras

Este guia prático detalha os passos para colocar seu squad de agentes de IA em operação, automatizando as áreas de Vendas, Atendimento, Marketing, Financeiro e Gestão.

## 1. O que é o seu squad

Seu squad é um time de agentes de IA, cada um especializado em uma área do Colégio Conecta Araras (Vendas, Atendimento, Marketing, Financeiro, Gestão). Eles trabalham de forma colaborativa, orquestrados por um Gestor Central, para automatizar tarefas repetitivas, otimizar fluxos de trabalho e fornecer informações em tempo real para a tomada de decisão. O objetivo é liberar sua equipe humana para focar em atividades estratégicas e de maior valor, mantendo a comunicação premium e as regras da casa.

## 2. Onde rodar (harness)

Os agentes são projetados para rodar em um 'harness' como **Claude Code** ou **Cowork**. Estes ambientes fornecem a infraestrutura necessária para que os agentes executem suas tarefas, acessem seus contextos, memórias e skills, e interajam com as ferramentas.

1.  **Acessar o Harness:** Faça login no Claude Code ou Cowork.
2.  **Criar um Novo Workspace:** Crie um novo workspace e importe todos os arquivos deste projeto. A estrutura de pastas será:
    *   `sharedContext/`: Contém arquivos markdown com o contexto geral do negócio.
    *   `agents/`: Cada subpasta dentro de `agents/` representa um agente, contendo seu `claude.md`, `memory.md` e a pasta `skills/` com os `.md` das skills.
    *   `orchestrator.md`: O CLAUDE.md do gestor central.
    *   `mestre-starter-kit/`: O curso e skills de referência para construção.
3.  **Entender os Arquivos:**
    *   **`CLAUDE.md` (ou `claude.md`):** É o 'cérebro' do agente/orquestrador. Contém seu papel, contexto, regras, ferramentas e instruções. É o 'system prompt' persistente.
    *   **`memory.md`:** A memória de longo prazo do agente. Ele é instruído a se auto-atualizar com novos aprendizados.
    *   **`skills/`:** Pasta que contém arquivos `.md` com os 'SOPs' (Standard Operating Procedures) de cada tarefa que o agente pode executar. São chamados pelo agente quando necessário.

## 3. Conectar as ferramentas

Para que seus agentes funcionem, você precisará conectar as ferramentas da STACK PADRÃO. A maioria das integrações será feita via **n8n**.

1.  **n8n (Automação e Integração):**
    *   **Instalação:** Hospede o n8n em uma VPS (Hostinger ou HospedaInfo) ou use a versão cloud se preferir. Siga a documentação oficial para instalação.
    *   **APIs e Credenciais:** Para cada ferramenta abaixo, você precisará gerar chaves de API ou tokens de acesso e configurá-los como credenciais no n8n. Isso permite que o n8n atue como a ponte entre seus agentes e os sistemas.
2.  **Google Workspace (Gmail, Agenda, Planilhas, Docs, Drive):**
    *   **Criação de Conta de Serviço:** Para automações mais robustas e seguras, crie uma 'Conta de Serviço' no Google Cloud Platform e conceda a ela os acessos necessários (Gmail API, Google Calendar API, Google Sheets API, Google Docs API, Google Drive API). Baixe o arquivo JSON da chave e configure no n8n como uma credencial de 'Google Service Account'.
    *   **Alternativa (menos segura):** Para testes iniciais, você pode usar credenciais OAuth2 do Google no n8n, mas a conta de serviço é recomendada para produção.
3.  **Supabase (Banco de Dados e Memória):**
    *   **Configuração de Projeto:** Crie um novo projeto no Supabase. Você precisará de um banco de dados para armazenar:
        *   Dados de leads (Agente Vendas).
        *   Histórico de conversas do WhatsApp por contato (Agente Vendas, Agente Atendimento).
        *   Status de campanhas e métricas (Agente Marketing).
        *   Histórico de cobranças e inadimplência (Agente Financeiro).
        *   Status de metas e tarefas (Agente Gestão).
    *   **Chaves de API:** Obtenha a 'Project URL' e a 'anon public key' (ou 'service_role key' para operações de escrita) no painel do Supabase (Settings > API). Configure-as como credenciais HTTP Request ou Supabase no n8n.
4.  **GitHub (Versionamento):**
    *   **Criação de Repositório:** Crie um repositório privado no GitHub para hospedar seu workspace de agentes. Isso permitirá versionar o código, colaborar e implantar atualizações.
    *   **Token de Acesso Pessoal (PAT):** Gere um PAT no GitHub com permissões de `repo` para que o n8n (se precisar interagir com o GitHub) ou o harness possa clonar/atualizar o workspace. Configure no n8n como credencial.

## 4. Conectar os agentes no WhatsApp

Esta é uma etapa crucial, pois o WhatsApp é o principal canal de interação para Vendas e Atendimento.

1.  **Escolher o Provedor:**
    *   **Evolution API:** Solução open-source, auto-hospedada. Oferece mais controle e flexibilidade. Requer uma VPS para rodar o Docker.
    *   **Uazapi:** Solução gerenciada, mais simples de configurar, mas com menos controle sobre a infraestrutura. Pode ter custos associados.
    *   **Recomendação:** Para controle total e escalabilidade, a Evolution API em sua própria VPS é a melhor opção a longo prazo. Para iniciar rapidamente, Uazapi pode ser uma alternativa.
2.  **Subir a Evolution API (se escolhido):**
    *   **VPS:** Contrate uma VPS (Hostinger, HospedaInfo) com Docker instalado.
    *   **Instalação Evolution API:** Siga a documentação da Evolution API para subir a aplicação via Docker. Crie uma instância.
3.  **Conectar o Número:**
    *   Acesse a interface da Evolution API (ou Uazapi) e siga as instruções para conectar seu número de WhatsApp. Isso geralmente envolve escanear um QR Code com o WhatsApp do seu celular (Vá em 'Aparelhos conectados' no seu WhatsApp).
    *   **Número Dedicado:** Use um número de telefone **exclusivo** para a operação de IA. Nunca use seu número pessoal para evitar bloqueios e garantir profissionalismo.
4.  **Apontar o WEBHOOK da Evolution/Uazapi para o n8n:**
    *   No painel da Evolution API (ou Uazapi), configure o webhook de 'mensagem recebida' (`message.received`) para a URL do seu nó 'Webhook' no n8n. Este nó será o ponto de entrada para todas as mensagens recebidas.
5.  **Fluxo no n8n (Mensagem Recebida):**
    *   **Nó Webhook:** Recebe a mensagem do WhatsApp.
    *   **Identificar/Buscar Cliente:** Use o número de telefone do remetente para buscar o cliente/lead no Supabase. Se for um número novo, crie um registro.
    *   **Montar Contexto:** Recupere o histórico da conversa do Supabase (`memory.md` do contato), informações do lead/aluno, e qualquer outro contexto relevante para o agente.
    *   **Chamar o AGENTE (Harness):** Utilize um nó 'HTTP Request' no n8n para enviar o contexto montado e a mensagem do usuário para o endpoint da API do seu harness (Claude Code/Cowork) que executa o `CLAUDE.md` do Agente Vendas ou Agente Atendimento, dependendo da triagem inicial.
    *   **Pegar a Resposta:** O nó 'HTTP Request' receberá a resposta do agente de IA.
    *   **Enviar de Volta:** Use um nó 'HTTP Request' para chamar o endpoint de envio de mensagem da Evolution API (ex: `POST /message/sendText`) ou Uazapi, enviando a resposta do agente de volta para o cliente.
6.  **Memória por Contato (Supabase):**
    *   Para cada mensagem enviada e recebida, salve o histórico completo da conversa no Supabase, associado ao número de telefone do contato. Isso garante que os agentes 'lembrem' das conversas anteriores.
    *   Ao montar o contexto para o agente, sempre injete o histórico recente do Supabase.
7.  **Respeitar Horário Comercial:**
    *   No fluxo do n8n, adicione uma lógica para verificar o horário atual. Se estiver fora do horário de atendimento (24/7 para sua operação, mas para escalonamentos ou quando o agente não souber resolver):
        *   Envie a mensagem de fora do horário definida: "O Colégio Conecta Araras agradece seu contato. Estamos verificando internamente sua solicitação e responderemos no próximo dia útil."
        *   Pause as respostas automáticas para aquele contato até o próximo período de atendimento.
8.  **Escalonamento:**
    *   Quando um agente bater em um gatilho de 'parar' (ex: cliente reclamando, pedido urgente, gasto abusivo), o agente deve instruir o n8n (via sua resposta) a:
        *   Notificar o humano responsável (Layla, Graziele, Anne, Kelvin, Laura) via Gmail ou um grupo de WhatsApp interno (usando a Evolution API/Uazapi para um número interno).
        *   Pausar as respostas automáticas para aquele contato, aguardando a intervenção humana.
9.  **Boas Práticas Anti-Ban (WhatsApp):**
    *   **Número/Chip Dedicado:** Use um número de telefone exclusivo para a operação de IA.
    *   **Aquecimento Gradual:** Se o número for novo, comece com um volume baixo de mensagens e aumente gradualmente para evitar suspeitas do WhatsApp.
    *   **Ritmo Humano:** Configure delays (atrasos) entre as mensagens no n8n para simular um ritmo de conversa humano, evitando disparos em massa.
    *   **Opt-in:** Sempre que possível, garanta que os usuários deram 'opt-in' para receber mensagens. Para leads, a primeira interação já é um opt-in implícito.

## 5. Automatizar e agendar

O **n8n** será seu hub de automação e agendamento:

1.  **Orquestração de Skills:** Crie fluxos no n8n que chamam as skills dos agentes. Por exemplo:
    *   Um webhook do WhatsApp dispara o fluxo que chama o Agente Vendas.
    *   Um cron job no n8n pode chamar o Agente Financeiro para 'emitir-e-enviar-cobrancas' diariamente.
    *   Outro cron job pode chamar o Agente Marketing para 'monitorar-campanhas-e-metricas' semanalmente.
2.  **Agendamento (Cron):** Use os nós 'Cron' do n8n para agendar a execução periódica de skills, como relatórios diários/semanais/mensais, monitoramento de métricas, lembretes de cobrança, etc.
3.  **Integração entre Ferramentas:** Use o n8n para conectar Google Planilhas ao Gmail, Supabase ao WhatsApp, etc., criando fluxos de dados sem emendas.

## 6. Horário e fora do horário

Sua operação é 24 horas, todo dia. No entanto, para situações onde um agente não souber resolver ou precisar escalar:

*   **Durante o horário:** O agente escala imediatamente para o humano responsável, que deve ser notificado via canal interno (WhatsApp/Gmail).
*   **Fora do horário (para escalonamentos):** Se o agente precisar escalar para um humano e for fora do horário comercial humano, ele deve avisar o cliente: "Agradecemos seu contato. Sua solicitação é importante e já foi encaminhada para nossa equipe, que a verificará internamente e responderá no próximo dia útil. Agradecemos a compreensão."

## 7. Onde hospedar

Para rodar o n8n e a Evolution API (se escolhido) 24/7 de forma estável, você precisará de uma Virtual Private Server (VPS).

*   **Hostinger:** (https://www.hostinger.com.br/) Oferece planos de VPS com bom custo-benefício e interface amigável.
*   **HospedaInfo:** (https://hospedainfo.com/) Outra opção nacional com suporte de qualidade.

Escolha um plano com recursos adequados (RAM, CPU, armazenamento) para suportar o n8n e a Evolution API, idealmente com pelo menos 2GB de RAM e 2 vCPUs.

## 8. Primeiros 7 dias (Ordem de Implementação)

Siga esta ordem de implementação para garantir um rollout suave e com impacto rápido:

1.  **Dia 1-2: Infraestrutura Básica:**
    *   Configure a VPS (Hostinger/HospedaInfo).
    *   Instale o Docker e a Evolution API (ou configure Uazapi).
    *   Instale e configure o n8n na VPS.
    *   Crie o projeto Supabase e configure as tabelas iniciais (leads, histórico de conversas).
    *   Crie as credenciais do Google Workspace (Conta de Serviço) no n8n.
    *   Importe o workspace dos agentes para o Claude Code/Cowork e o GitHub.

2.  **Dia 3-4: Agente Vendas (Primeira Área):**
    *   Conecte o número de WhatsApp dedicado.
    *   Configure o webhook da Evolution API/Uazapi para o n8n.
    *   Crie o fluxo no n8n para o Agente Vendas (recepcionar, qualificar, agendar, atualizar Google Planilhas/Supabase).
    *   Teste o fluxo de ponta a ponta com leads de teste.
    *   Treine o Agente Vendas com exemplos e correções, atualizando seu `memory.md`.

3.  **Dia 5-6: Agente Atendimento:**
    *   Crie o fluxo no n8n para o Agente Atendimento (responder dúvidas comuns, triar chamados, coletar informações).
    *   Configure o acesso aos informativos de eventos no contexto do agente.
    *   Teste o fluxo de atendimento e escalonamento para a Anne.
    *   Garanta que a memória por contato no Supabase esteja funcionando.

4.  **Dia 7: Monitoramento e Ajustes Iniciais:**
    *   Monitore os primeiros atendimentos e agendamentos.
    *   Faça ajustes finos nos prompts, skills e fluxos do n8n com base no feedback.
    *   Comece a planejar a implementação do Agente Marketing, Agente Financeiro e Agente Gestão, seguindo a mesma lógica de conectar ferramentas, criar fluxos no n8n e testar as skills. Lembre-se: todo processo manual repetido vira uma skill.