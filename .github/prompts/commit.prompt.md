---
description: Realiza commits Git automaticamente com análise de diff, geração inteligente de mensagem e conformidade com padrões do projeto.
---

Realize o commit das alterações atuais seguindo o fluxo abaixo:

## 1️⃣ Validação Inicial e Preparação

// turbo

1. Execute `git status` para verificar **TODAS** as mudanças:
   - **Modified**: arquivos modificados (tracked)
   - **Staged**: arquivos já adicionados ao stage
   - **Untracked**: arquivos novos não rastreados
2. Identifique arquivos sensíveis que NÃO devem ser commitados:
   - `.env`, `.env.*`, `secrets.*`, `credentials.json`, chaves privadas, etc
3. Adicione os arquivos seguros **individualmente**, um por um:
   - `git add <arquivo1>`
   - `git add <arquivo2>`
   - etc.
   - **NUNCA use `git add .` ou `git add -A`** — isso pode incluir arquivos sensíveis acidentalmente
4. Se houver arquivos sensíveis, avise o desenvolvedor e NÃO os adicione
5. Execute `git status` novamente para confirmar o que está no stage

## 2️⃣ Análise de Código (OTIMIZADA)

**⚠️ IMPORTANTE: O comando `git diff --cached` pode ter output truncado.**

**Estratégia de análise otimizada:**

// turbo

1. Execute `git diff --cached --stat` para obter estatísticas gerais:
   - Lista de arquivos modificados
   - Quantidade de linhas adicionadas/removidas por arquivo
   - Visão geral do tamanho das mudanças

2. Execute `git diff --cached --name-only` para listar apenas os nomes dos
   arquivos modificados

3. **Para cada arquivo individualmente**, execute:
   ```powershell
   git diff --cached -- <caminho/arquivo.ext>
   ```
   Isso evita truncamento de output que ocorre ao analisar todos de uma vez.

4. Analise os arquivos modificados para inferir:
   - **Tipo**: feat, fix, refactor, docs, style, test, chore, perf, build
   - **Escopo**: área afetada (ir, carteira, dividendos, score, api, ui, android, etc)
   - **Descrição**: resumo objetivo do que foi alterado

5. **Agrupe arquivos relacionados** que compartilham o mesmo escopo/funcionalidade

## 3️⃣ Decisão de Agrupamento de Commits

**PREFIRA commitar múltiplos arquivos juntos quando:**

- ✅ Arquivos pertencem à **mesma feature/funcionalidade**
- ✅ Mudanças compartilham o **mesmo escopo** (ex: todos relacionados a "ir")
- ✅ Alterações são **logicamente acopladas** (uma depende da outra)
- ✅ Fazem parte da **mesma história de desenvolvimento**

**Separe em múltiplos commits quando:**

- ✅ Existirem mudanças em **escopos/funcionalidades completamente diferentes**
  (ex: feature de IR + fix de UI + bump de versão Android)
- ✅ Mudanças forem **semanticamente desacopladas** (ex: nova feature + refactor
  de código antigo não relacionado)
- ✅ Facilitar **review, bisect e reversões seletivas** fizer sentido
- ✅ Houver mudanças muito grandes (> 200-300 linhas) em áreas distintas

**NÃO separe quando:**

- ❌ Mudanças forem relacionadas à mesma feature/fix
- ❌ Uma mudança depender da outra para funcionar
- ❌ Arquivos fazem parte da mesma implementação lógica

**Exemplos de Agrupamento Adequado:**

```
✅ BOM - Múltiplos arquivos em um commit (mesma feature):
Commit: feat(ir): adicionar painel de Proventos a Receber
- src/hooks/useImpostoRendaData.ts
- src/pages/ImpostoRenda.tsx
- supabase/functions/get-ir-data/index.ts

✅ BOM - Separação por escopo diferente (3 commits distintos):
Commit 1: feat(ir): adicionar painel de Proventos a Receber
Commit 2: fix(ui): corrigir duplicação de subtítulo em mobile
Commit 3: chore(android): incrementar versionCode para 29
```

## 4️⃣ Execução de Commits (Workflow de Múltiplos Commits)

**Se decidir separar em múltiplos commits:**

// turbo

1. Execute `git reset` para limpar o stage
2. Para cada grupo de arquivos relacionados:
   - `git add <arquivo1> <arquivo2> ...` (apenas arquivos do mesmo escopo)
   - `git commit -m "<mensagem>"` com a mensagem apropriada
3. Repita até commitar todos os arquivos

**Formato da mensagem de commit (obrigatório):**

```
<tipo>(<escopo>): <mensagem curta>

- Mudança 1
- Mudança 2
- Mudança 3
```

**Exemplo:**

```
feat(ir): adicionar painel de Proventos a Receber

- Adicionar seção 'Proventos a Receber' na página de Imposto de Renda
- Implementar lógica de cálculo de receivableIncome no hook useImpostoRendaData
- Incluir receivableIncome no payload da Edge Function get-ir-data
```

## 5️⃣ Validação dos Commits

// turbo

1. Execute `git log -<N> --format=%B` (onde N = número de commits criados)
2. Verifique se todas as mensagens estão corretas
3. Se pre-commit hooks modificarem arquivos:
   - Execute `git add <arquivo1> <arquivo2> ...` (cada arquivo individualmente) + `git commit --amend --no-edit`

## 6️⃣ Push Automático

// turbo

1. Execute `git push` para enviar os commits para o repositório remoto
2. Se o push falhar por divergência, avise o desenvolvedor e NÃO faça force push
3. Valide o sucesso com a mensagem de confirmação do git

## ✅ Checklist Obrigatório

- [ ] Verificou `git status` para listar TODAS as mudanças
- [ ] Adicionou TODOS os arquivos seguros individualmente com `git add <arquivo>` (NUNCA `git add .`)
- [ ] Analisou `git diff --cached --stat` para visão geral
- [ ] Analisou `git diff --cached -- <arquivo>` individualmente para cada arquivo
- [ ] Identificou escopos distintos e decidiu separação de commits
- [ ] Se múltiplos escopos: executou `git reset` e commitou por grupo
- [ ] Gerou mensagem(ns) seguindo formato obrigatório
- [ ] Validou sucesso com `git log`
- [ ] Executou push automático

## ⚠️ Proteções Mantidas

- ❌ NUNCA commiteará arquivos sensíveis (.env, credentials, secrets)
- ❌ NUNCA fará force push em caso de divergência
- ❌ NUNCA editará arquivos a não ser que seja para corrigir erros de lint
- ✅ SEMPRE valida sucesso do commit
- ✅ SEMPRE faz push automático após validação
