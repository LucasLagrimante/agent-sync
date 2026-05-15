---
description: Instruções para realização de commits Git seguindo workflow padronizado
---

Quando solicitado a realizar commits Git neste workspace, siga o workflow detalhado em commit.md, que inclui:

- Validação inicial com git status para identificar todas as mudanças
- Análise otimizada de diffs usando git diff --cached --stat e diffs individuais por arquivo
- Decisão de agrupamento baseada em escopo e funcionalidade compartilhada
- Execução de commits com mensagens padronizadas no formato <tipo>(<escopo>): <descrição>
- Validação dos commits e push automático

Proteções importantes:
- Nunca commite arquivos sensíveis (.env, credentials, etc.)
- Nunca use git add . ou git add -A
- Nunca faça force push em caso de divergência

Esta é uma preferência que pode ser substituída se explicitamente solicitado.
