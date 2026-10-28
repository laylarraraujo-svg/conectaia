---
name: construtora
description: Setup do Motor de Conteúdo do vereador Alex Tailândia. Lê o perfil, entrevista o Alex em 3 fases e preenche o dossiê. Use quando o dossiê tiver campos [?], quando o Alex disser "vamos configurar", "setup", "me entrevista", ou quando estado-setup.md não estiver concluído. Retoma de onde parou.
---

# Construtora: setup do motor

## Regra principal
Antes de qualquer pergunta, leia `dossie/estado-setup.md` e continue da **próxima pergunta** registrada. Depois de cada bloco respondido, salve as respostas no arquivo do dossiê correspondente e atualize `estado-setup.md`. Assim a conversa pode parar a qualquer momento.

Faça **no máximo 3 perguntas por mensagem**. Quando a resposta for curta, peça um exemplo real.

## Fase 1: Leitura do perfil
1. Tente abrir `instagram.com/alex.tailandia` pela extensão do Chrome (com login). Se não houver acesso, peça ao Alex/assessor: links ou prints dos 10 posts mais vistos dos últimos 90 dias + print da tela de Insights.
2. Para cada post: formato, pilar, gancho dos 3 primeiros segundos, views/curtidas/comentários, comentário mais comum.
3. Escreva em `dossie/perfil.md` → "O que já funciona": os 3 padrões que se repetem nos melhores posts e os 2 dos piores.

## Fase 2: Entrevista
**2a. Mandato e pilares** (atualiza `perfil.md` e `pilares.md`)
- Partido, ano de início, 1º mandato? De onde vem o "Tailândia"?
- Dos 5 pilares em `pilares.md`, quais estão certos, quais faltam, qual é o carro-chefe?
- Quais projetos/requerimentos você tem hoje que valem conteúdo? (pedir números)
- Que temas você **não** quer tocar?

**2b. Voz e público** (atualiza `voz.md` e `publico.md`)
- Peça 2–3 vídeos de tribuna em que ele gostou da própria fala → transcreva e extraia bordões.
- Como você fala com o servidor? E com a mãe atípica? E com o morador?
- Palavras e tons proibidos (palavrão, ironia, ataque pessoal).
- Qual é o canal de demandas (WhatsApp do gabinete)?

**2c. Limites e aprovação** (atualiza `perfil.md` → Aprovação e `regras-e-limites.md`)
- Quem aprova, por qual canal, em quanto tempo?
- Existe jurídico do gabinete/partido para dúvidas? Modelo de autorização de imagem?
- Identidade visual: cores, fonte, foto padrão → criar `dossie/identidade-visual.md`.

## Fase 3: Motor e primeiro roteiro
1. Revise o dossiê: liste os `[?]` que ainda restam.
2. Proponha a primeira pauta com base no que ele contou e rode a skill `criar-conteudo` para ela.
3. Peça feedback do Alex no roteiro e registre em `aprendizados.md`.
4. Marque o setup como concluído em `estado-setup.md`.
