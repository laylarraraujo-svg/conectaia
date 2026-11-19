# Bot de postagem automática no Instagram — Agente Notícias

Publica cada notícia de Mogi Guaçu das edições (6h52, 10h52, 15h52) como **um post de imagem por notícia**.

## Contas (via Windsor.ai, conector `instagram`)
- @mogiguacualerta — account id `17841457552030480`
- @direitaonlinemogiguacu — account id `17841411353795737`
- NÃO postar em @posicionamentoparacorretores.

## Fluxo por edição
1. Monta a edição normalmente (skill `resumir-noticias-mogi-guacu`).
2. Para cada notícia, classifica:
   - **Precisa de aprovação** se for:
     - política de Mogi Guaçu: Prefeitura, prefeito, secretários, Câmara, vereadores, partidos, denúncias contra gestores;
     - urgente: ocorrência em andamento, morte, crime grave recente ou alerta da Defesa Civil.
   - **Publica direto** nos demais casos: obras, serviços, trânsito comum, saúde, empregos, eventos, clima.
3. Gera as artes no **mesmo visual dos dashboards** (DASH NOTÍCIA – MOGI GUAÇU ALERTA e DASH NOTÍCIA – DIREITA ONLINE):
   - `render-alerta.html` e `render-direita.html` usam o código de desenho copiado dos dashboards (logo, cores, cenas por tema).
   - Monte um JSON com `arquivo`, `manchete`, `linha_fina`, `chapeu`, `destaque`, `urgente`, `categoria` e rode `node bot-instagram/renderizar.js <noticias.json> posts/AAAA-MM-DD/`.
   - Sai um JPEG por conta: `<arquivo>-alerta.jpg` (para @mogiguacualerta) e `<arquivo>-direita.jpg` (para @direitaonlinemogiguacu).
   - Se os dashboards mudarem o visual, leia os artifacts de novo e rode `python3 -I bot-instagram/extrair_artes.py <html_alerta> <html_direita>`.
   - Salva em `posts/AAAA-MM-DD/`, faz commit e push no branch `claude/vibrant-sagan-064z2o`.
   - URL pública da imagem: `https://raw.githubusercontent.com/laylarraraujo-svg/conectaia/claude/vibrant-sagan-064z2o/agentes/agente-noticias/posts/AAAA-MM-DD/<arquivo>.jpg` (o repositório é público).
4. Itens que **publicam direto**: `execute_action` connector `instagram`, action `create_image_post`, nas 2 contas, com `image_url`, `caption` e `alt_text`.
5. Itens que **precisam de aprovação**: não publica. Lista no chat e no e-mail da edição, em uma seção "Aguardando sua aprovação para o Instagram", com o card e a legenda. Só publica quando a Layla responder no chat aprovando (ex.: "aprovo 1 e 3").
6. Registra no arquivo da edição o que foi publicado (link/ID) e o que ficou aguardando.

## Legenda (modelo)
```
<Título>

<Resumo em 2–4 frases, com palavras próprias>

📍 Mogi Guaçu · <dd/mm/aaaa>
Fonte: <portal> (@perfil)

#MogiGuaçu #NotíciasMogiGuaçu #<categoria>
```

## Cuidados
- Nunca copiar texto do portal; sempre resumir e citar a fonte.
- Não identificar menores (nome, escola, endereço) nem vítimas de violência.
- Acusação ainda não apurada vai sempre para aprovação.
- Se o Windsor falhar ao publicar, informa no chat e segue com o resto.
