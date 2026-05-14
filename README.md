# agents-sync

Padronize configs de IA em todos os seus projetos com um único comando.

Escaneia um diretório com múltiplos projetos, mostra quais estão bem configurados e cria os symlinks canônicos para cada ferramenta de IA.

## Como funciona

O arquivo `AGENTS.md` na raiz do projeto é a **única fonte da verdade**. Todos os outros arquivos de config de IA são symlinks apontando para ele:

```
projeto/
├── AGENTS.md                          ← canônico (Codex/OpenAI)
├── CLAUDE.md                          → AGENTS.md
├── GEMINI.md                          → AGENTS.md
├── .cursorrules                       → AGENTS.md   (Cursor)
├── .windsurfrules                     → AGENTS.md   (Windsurf)
├── .github/
│   └── copilot-instructions.md        → ../AGENTS.md (GitHub Copilot)
├── .gemini/
│   └── system.md                      → ../AGENTS.md (Gemini CLI)
├── .agents/
│   ├── workflows/                     ← slash commands / workflows (fonte canônica)
│   ├── skills/                        ← skills customizadas (fonte canônica)
│   └── commands                       → workflows
├── .claude/
│   ├── commands                       → ../.agents/commands
│   └── skills                         → ../.agents/skills
└── .opencode/
    ├── commands                       → ../.agents/commands
    └── skills                         → ../.agents/skills
```

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

1. Escanear todos os subdiretórios e avaliar 12 itens canônicos por projeto
2. Exibir uma tabela com o status de cada item (`✓` ok, `-` ausente, `↺` errado, `⚠` arquivo real)
3. Deixar você escolher qual(is) projeto(s) padronizar
4. Mostrar um preview das mudanças e pedir confirmação
5. Aplicar os symlinks

```
agents-sync — Windows
Escaneando /home/user/Projects...

  #  Projeto              AG  CL  GM  CU  WS  CP  GS  WF  SK  AC  CC  CS  Score
  1  meu-projeto           ✓   ✓   -   -   -   -   -   ✓   ✓   ↺   ↺   ↺   5/12
  2  outro-projeto         ✓   -   -   -   -   -   -   -   -   -   -   -   1/12

Selecione projeto(s) (número, 1-3, 1 3 5, all, q): 1

Mudanças para meu-projeto:
  + symlink   GEMINI.md → AGENTS.md
  + symlink   .cursorrules → AGENTS.md
  ...
  ↺ atualizar .agents/commands → workflows  (era: junction point)

Aplicar mudanças? (s/N): s
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
| CP | `.github/copilot-instructions.md` | GitHub Copilot |
| GS | `.gemini/system.md` | Gemini CLI (system prompt) |
| WF | `.agents/workflows/` | Pasta de workflows |
| SK | `.agents/skills/` | Pasta de skills |
| AC | `.agents/commands` | Symlink interno `commands → workflows` |
| CC | `.claude/commands` | Claude Code slash commands |
| CS | `.claude/skills` | Claude Code skills |
| OC | `.opencode/commands` | OpenCode slash commands |
| OS | `.opencode/skills` | OpenCode skills |

## Windows

Symlinks no Windows exigem uma das opções:

- **Modo Desenvolvedor** (recomendado): Configurações → Sistema → Para Desenvolvedores
- **Executar como Administrador**

> **Junction points** são detectados e substituídos por symlinks reais. Junctions não são rastreados pelo git como symlinks e usam paths absolutos, o que os torna frágeis e não portáveis.
