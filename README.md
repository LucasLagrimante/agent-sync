# agents-sync

Padronize configs de IA em todos os seus projetos com um único comando.

Escaneia um diretório com múltiplos projetos, mostra quais estão bem configurados e cria os symlinks canônicos para cada ferramenta de IA.

## Como funciona

O arquivo `AGENTS.md` na raiz do projeto é a **única fonte da verdade**. Todos os outros arquivos de config de IA são symlinks apontando para ele. Workflows e skills ficam em `.agents/` e são compartilhados entre todas as ferramentas via symlink direto:

```
projeto/
├── AGENTS.md                          ← canônico (Codex/OpenAI)
├── CLAUDE.md                          → AGENTS.md
├── GEMINI.md                          → AGENTS.md
├── .cursorrules                       → AGENTS.md   (Cursor)
├── .windsurfrules                     → AGENTS.md   (Windsurf)
├── .github/
│   ├── copilot-instructions.md        → ../AGENTS.md
│   ├── agents/                        → ../.agents/agents   (custom agents .agent.md)
│   └── prompts/                       → ../.agents/workflows (prompt files)
├── .gemini/
│   └── system.md                      → ../AGENTS.md (Gemini CLI)
├── .agents/
│   ├── workflows/                     ← fonte canônica de slash commands
│   ├── skills/                        ← fonte canônica de skills
│   ├── agents/                        ← fonte canônica de custom agents (.agent.md)
│   └── commands                       → workflows   (alias interno)
├── .claude/
│   ├── commands                       → ../.agents/workflows
│   ├── skills                         → ../.agents/skills
│   └── agents/                        → ../.agents/agents
└── .opencode/
    ├── commands                       → ../.agents/workflows
    └── skills                         → ../.agents/skills
```

> Symlinks de diretório apontam **diretamente** para o destino final (ex: `../.agents/workflows`), sem passar por aliases intermediários. Isso evita cadeias de symlinks que causam erros no Windows.

## Instalação

```bash
pip install rich
```

## Uso

Execute na raiz do diretório que contém seus projetos:

```bash
cd ~/Projects
python sync_agents.py
```

O script vai:

1. Escanear todos os subdiretórios e avaliar **18 itens canônicos** por projeto
2. Exibir uma tabela com o status de cada item (`✓` ok, `-` ausente, `↺` errado, `⚠` arquivo real)
3. Deixar você escolher qual(is) projeto(s) padronizar
4. Mostrar um preview das mudanças e pedir confirmação
5. Aplicar os symlinks e atualizar o `.gitignore`

```
agents-sync — Windows
Escaneando C:\Users\user\Projects...

  #  Projeto              AG  CL  GM  CU  WS  CP  GS  WF  SK  AA  AC  CC  CS  CA  OC  OS  GA  GP  Score
  1  meu-projeto           ✓   ✓   -   -   -   -   -   ✓   ✓   -   ↺   ↺   ↺   -   -   -   -   -   5/18
  2  outro-projeto         ✓   -   -   -   -   -   -   -   -   -   -   -   -   -   -   -   -   -   1/18

Selecione projeto(s) (número, 1-3, 1 3 5, all, q): 1

Mudanças para meu-projeto:
  + symlink   GEMINI.md → AGENTS.md
  + symlink   .cursorrules → AGENTS.md
  ↺ atualizar .agents/commands → workflows  (era: junction point)
  + symlink   .opencode/commands → ../.agents/workflows
  ...

Aplicar mudanças? (s/N): s
  .gitignore atualizado (3 entradas)
```

### Opções

| Flag | Descrição |
|---|---|
| `--path PATH` / `-p PATH` | Diretório pai com os projetos (padrão: `.`) |

### Seleção de projetos

| Entrada | Resultado |
|---|---|
| `1` | projeto número 1 |
| `1 3 5` | projetos 1, 3 e 5 |
| `1-4` | projetos 1 ao 4 |
| `all` | todos os projetos |
| `q` | sair |

## Legenda das colunas

| Col | Path | Ferramenta |
|---|---|---|
| AG | `AGENTS.md` | Codex / OpenAI (arquivo canônico) |
| CL | `CLAUDE.md` | Claude Code |
| GM | `GEMINI.md` | Gemini CLI (contexto) |
| CU | `.cursorrules` | Cursor (formato legacy) |
| WS | `.windsurfrules` | Windsurf (formato legacy) |
| CP | `.github/copilot-instructions.md` | GitHub Copilot — instruções globais |
| GS | `.gemini/system.md` | Gemini CLI (system prompt) |
| WF | `.agents/workflows/` | Pasta real — fonte dos slash commands |
| SK | `.agents/skills/` | Pasta real — fonte das skills |
| AA | `.agents/agents/` | Pasta real — fonte dos custom agents (`.agent.md`) |
| AC | `.agents/commands` | Alias interno `commands → workflows` |
| CC | `.claude/commands` | Claude Code — slash commands |
| CS | `.claude/skills` | Claude Code skills |
| CA | `.claude/agents/` | Claude Code / VS Code — sub-agents |
| OC | `.opencode/commands` | OpenCode — slash commands |
| OS | `.opencode/skills` | OpenCode skills |
| GA | `.github/agents/` | GitHub Copilot — custom agents (`.agent.md`) |
| GP | `.github/prompts/` | GitHub Copilot — prompt files (slash commands) |

## .gitignore automático

Ao sincronizar um projeto, o script adiciona automaticamente ao `.gitignore` as entradas de arquivos gerados por cada ferramenta:

| Ferramenta | Entradas ignoradas |
|---|---|
| OpenCode | `.opencode/node_modules/`, `.opencode/bun.lock`, `.opencode/package-lock.json` |
| Claude Code | `.claude/settings.local.json` |
| Gemini CLI | `.gemini/tmp/` |
| Cursor | `.cursor/chat/` |
| Geral | `.logs/`, `.agents/.logs/` |

## Windows

Symlinks no Windows exigem uma das opções:

- **Modo Desenvolvedor** (recomendado): Configurações → Sistema → Para Desenvolvedores
- **Executar como Administrador**

**Junction points** são detectados e substituídos por symlinks reais. Junctions não são rastreados pelo git como symlinks (modo `120000`), usam paths absolutos e não funcionam em outros sistemas operacionais.
