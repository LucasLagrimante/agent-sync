#!/usr/bin/env python3
"""
sync_agents.py — Padronização de configs de IA via AGENTS.md symlinks.
Execute na raiz de um diretório com projetos para escanear e padronizar.

Uso:
  python sync_agents.py              # escaneia o diretório atual
  python sync_agents.py --path /foo  # especifica diretório pai
"""

import os
import sys
import platform
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Literal

# Força UTF-8 no Windows para suportar caracteres Unicode (✓ ↺ ⚠)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from rich.console import Console
    from rich.table import Table
    from rich import box
    from rich.panel import Panel
except ImportError:
    print("Dependência necessária: pip install rich")
    sys.exit(1)

IS_WINDOWS = platform.system() == "Windows"

# No Windows, desativa o renderer legado para usar VT100 (suporta Unicode/UTF-8)
console = Console(legacy_windows=False)

# ─── Template mínimo de AGENTS.md ─────────────────────────────────────────────

AGENTS_MD_TEMPLATE = """\
# AGENTS.md

Instruções para agentes de IA trabalhando neste projeto.

## Visão Geral

<!-- Descreva o projeto brevemente -->

## Regras Gerais

- Sempre leia este arquivo antes de começar qualquer tarefa
- Prefira edições cirúrgicas a reescritas completas
- Não adicione comentários óbvios ao código

## Stack

<!-- Liste o stack técnico do projeto -->
"""

# ─── Definição canônica ───────────────────────────────────────────────────────

@dataclass
class CheckItem:
    key: str       # identificador único
    label: str     # nome da coluna na tabela
    path: str      # caminho do link/arquivo (relativo ao projeto)
    target: str | None  # target do symlink (relativo ao dir do link); None = pasta real
    is_dir: bool = False

# A ordem importa: pastas reais antes dos symlinks que dependem delas.
# Labels de 2 letras para caber em terminais estreitos.
CHECKS = [
    # Arquivo canônico (Codex/OpenAI)
    CheckItem("agents_md",     "AG",  "AGENTS.md",                        None,                  False),

    # Symlinks de arquivo — ferramentas de IA
    CheckItem("claude_md",     "CL",  "CLAUDE.md",                        "AGENTS.md",           False),
    CheckItem("gemini_md",     "GM",  "GEMINI.md",                        "AGENTS.md",           False),
    CheckItem("cursorrules",   "CU",  ".cursorrules",                     "AGENTS.md",           False),
    CheckItem("windsurfrules", "WS",  ".windsurfrules",                   "AGENTS.md",           False),
    CheckItem("copilot",       "CP",  ".github/copilot-instructions.md",  "../AGENTS.md",        False),
    CheckItem("gemini_sys",    "GS",  ".gemini/system.md",                "../AGENTS.md",        False),

    # Estrutura .agents — pastas reais
    CheckItem("agents_wf",     "WF",  ".agents/workflows",                None,                  True),
    CheckItem("agents_sk",     "SK",  ".agents/skills",                   None,                  True),

    # Symlink interno: .agents/commands → workflows (alias para Claude Code)
    CheckItem("agents_cmd",    "AC",  ".agents/commands",                 "workflows",           True),

    # Symlinks .claude → .agents
    CheckItem("claude_cmd",    "CC",  ".claude/commands",                 "../.agents/commands", True),
    CheckItem("claude_sk",     "CS",  ".claude/skills",                   "../.agents/skills",   True),
]

Status = Literal["ok", "missing", "wrong_target", "regular_file"]

@dataclass
class ProjectStatus:
    path: Path
    items: dict[str, Status] = field(default_factory=dict)

    @property
    def score(self) -> int:
        return sum(1 for s in self.items.values() if s == "ok")

    @property
    def total(self) -> int:
        return len(CHECKS)

    @property
    def name(self) -> str:
        return self.path.name


# ─── Scanning ─────────────────────────────────────────────────────────────────

def _get_link_target(path: Path) -> str | None:
    """
    Retorna o target de um symlink ou junction (Windows).
    Junction points: os.readlink() funciona mas is_symlink() retorna False.
    Retorna None se não é um link.
    """
    try:
        return os.readlink(path)
    except OSError:
        return None


def _paths_equivalent(link_path: Path, target_str: str, actual_raw: str) -> bool:
    """Compara target esperado (relativo) com o lido (pode ser absoluto no Windows)."""
    actual = Path(actual_raw)
    expected_relative = Path(target_str)

    if actual.is_absolute():
        # Junction point ou symlink absoluto — compara paths resolvidos
        # Remove prefixo \\?\ do Windows (extended-length path)
        actual_str = actual_raw
        if actual_str.startswith("\\\\?\\"):
            actual_str = actual_str[4:]
        try:
            expected_abs = (link_path.parent / target_str).resolve()
            actual_abs = Path(actual_str).resolve()
            return expected_abs == actual_abs
        except Exception:
            return False
    else:
        return actual == expected_relative


def _is_real_symlink(path: Path) -> bool:
    """Retorna True apenas para symlinks reais (não junction points do Windows)."""
    return path.is_symlink()


def check_item(project_root: Path, item: CheckItem) -> Status:
    link_path = project_root / item.path
    actual_raw = _get_link_target(link_path)

    if item.target is None:
        # Deve ser arquivo ou pasta real (não link)
        if actual_raw is not None:
            return "wrong_target"
        if item.is_dir and link_path.is_dir():
            return "ok"
        if not item.is_dir and link_path.is_file():
            return "ok"
        return "missing"

    # Deve ser symlink REAL apontando para item.target.
    # Junction points (is_symlink()=False mas readlink funciona) são considerados
    # wrong_target — git não os rastreia como symlinks e usam paths absolutos.
    if actual_raw is not None:
        if not _is_real_symlink(link_path):
            # É junction point — precisa ser substituído por symlink real
            return "wrong_target"
        if _paths_equivalent(link_path, item.target, actual_raw):
            return "ok"
        return "wrong_target"
    if link_path.exists():
        return "regular_file"
    return "missing"


def scan_projects(root: Path) -> list[ProjectStatus]:
    projects = []
    for entry in sorted(root.iterdir()):
        if not entry.is_dir() or entry.name.startswith('.'):
            continue
        status = ProjectStatus(path=entry)
        for item in CHECKS:
            status.items[item.key] = check_item(entry, item)
        projects.append(status)

    projects.sort(key=lambda p: p.score, reverse=True)
    return projects


# ─── Render ───────────────────────────────────────────────────────────────────

STATUS_ICON = {
    "ok":           "[green]✓[/]",
    "missing":      "[dim]-[/dim]",
    "wrong_target": "[yellow]↺[/yellow]",
    "regular_file": "[red]⚠[/red]",
}

LEGEND = (
    "AG=AGENTS  CL=CLAUDE  GM=GEMINI  CU=CURSOR  WS=WINDSURF  CP=COPILOT  GS=GEMINI/system\n"
    "WF=.agents/workflows  SK=.agents/skills  AC=.agents/commands  CC=.claude/commands  CS=.claude/skills"
)

def render_table(projects: list[ProjectStatus]) -> None:
    table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold", padding=(0, 1))
    table.add_column("#",       style="dim", width=3, no_wrap=True)
    table.add_column("Projeto", min_width=20, no_wrap=True)

    for item in CHECKS:
        table.add_column(item.label, justify="center", width=3, no_wrap=True)

    table.add_column("Score", justify="right", width=6, no_wrap=True)

    for i, proj in enumerate(projects, 1):
        score = proj.score
        total = proj.total
        ratio = score / total if total else 0
        color = "green" if ratio == 1 else "yellow" if ratio >= 0.6 else "red"

        row = [str(i), proj.name]
        for item in CHECKS:
            row.append(STATUS_ICON[proj.items[item.key]])
        row.append(f"[{color}]{score}/{total}[/]")
        table.add_row(*row)

    console.print()
    console.print(table)
    console.print(
        "[dim]Status: [green]✓[/green]=ok  -=ausente  [yellow]↺[/yellow]=symlink errado  [red]⚠[/red]=arquivo real[/dim]"
    )
    console.print(f"[dim]{LEGEND}[/dim]")
    console.print()


# ─── Seleção ──────────────────────────────────────────────────────────────────

def select_projects(projects: list[ProjectStatus]) -> list[ProjectStatus]:
    while True:
        raw = console.input(
            "[bold]Selecione projeto(s)[/] [dim](número, 1-3, 1 3 5, all, q)[/dim]: "
        ).strip().lower()

        if raw in ("q", "quit", "sair"):
            return []
        if raw in ("all", "todos"):
            return list(projects)

        selected: list[ProjectStatus] = []
        valid = True

        for part in raw.replace(",", " ").split():
            if "-" in part:
                try:
                    a, b = part.split("-", 1)
                    for n in range(int(a), int(b) + 1):
                        if 1 <= n <= len(projects):
                            selected.append(projects[n - 1])
                        else:
                            console.print(f"[red]Número {n} fora do intervalo.[/]")
                            valid = False
                            break
                except ValueError:
                    console.print(f"[red]Intervalo inválido: {part}[/]")
                    valid = False
            else:
                try:
                    n = int(part)
                    if 1 <= n <= len(projects):
                        selected.append(projects[n - 1])
                    else:
                        console.print(f"[red]Número {n} fora do intervalo (1–{len(projects)}).[/]")
                        valid = False
                except ValueError:
                    console.print(f"[red]Entrada inválida: {part}[/]")
                    valid = False

        if valid and selected:
            seen: set[int] = set()
            result: list[ProjectStatus] = []
            for p in selected:
                if id(p) not in seen:
                    seen.add(id(p))
                    result.append(p)
            return result


# ─── Mudanças ─────────────────────────────────────────────────────────────────

Action = Literal["mkdir", "symlink", "update", "skip", "create_file"]

@dataclass
class Change:
    action: Action
    item: CheckItem
    description: str


def list_changes(proj: ProjectStatus) -> list[Change]:
    changes: list[Change] = []

    # Se AGENTS.md não existe, criar arquivo (não symlink)
    if proj.items["agents_md"] == "missing":
        changes.append(Change("create_file", CHECKS[0], "AGENTS.md  [dim](template mínimo)[/]"))

    for item in CHECKS:
        if item.key == "agents_md":
            continue  # já tratado acima
        status = proj.items[item.key]
        if status == "ok":
            continue

        link_path = proj.path / item.path

        if item.target is None:
            if status in ("missing", "wrong_target"):
                changes.append(Change("mkdir", item, item.path))
        else:
            if status == "missing":
                changes.append(Change("symlink", item, f"{item.path} → {item.target}"))
            elif status == "wrong_target":
                actual = os.readlink(link_path)
                changes.append(Change("update", item, f"{item.path} → {item.target}  [dim](era: {actual})[/]"))
            elif status == "regular_file":
                changes.append(Change("skip", item, f"{item.path}  [red](arquivo real — remova manualmente para criar symlink)[/]"))

    return changes


def preview_changes(proj: ProjectStatus) -> bool:
    changes = list_changes(proj)
    if not changes:
        console.print(f"[green]✓ {proj.name} já está totalmente padronizado.[/]")
        return False

    console.print(f"\n[bold]Mudanças para [cyan]{proj.name}[/cyan]:[/]")
    for c in changes:
        if c.action == "mkdir":
            console.print(f"  [blue]mkdir[/]       {c.description}")
        elif c.action == "create_file":
            console.print(f"  [green]+[/] criar     {c.description}")
        elif c.action == "symlink":
            console.print(f"  [green]+[/] symlink   {c.description}")
        elif c.action == "update":
            console.print(f"  [yellow]↺[/] atualizar {c.description}")
        elif c.action == "skip":
            console.print(f"  [red]⚠ pular[/]    {c.description}")
    return True


# ─── Symlinks (multi-OS) ──────────────────────────────────────────────────────

def make_symlink(link_path: Path, target: str, is_dir: bool) -> None:
    """
    Cria symlink com tratamento específico por OS.
    Windows exige Developer Mode ativo ou execução como Administrador.
    Junction points existentes são removidos antes de recriar como symlink.
    """
    link_path.parent.mkdir(parents=True, exist_ok=True)

    if link_path.is_symlink():
        link_path.unlink()
    elif IS_WINDOWS and _get_link_target(link_path) is not None:
        # Junction point: is_symlink() = False mas os.readlink() funciona
        link_path.rmdir()

    try:
        if IS_WINDOWS:
            link_path.symlink_to(target, target_is_directory=is_dir)
        else:
            link_path.symlink_to(target)
    except OSError as e:
        if IS_WINDOWS and getattr(e, "winerror", None) == 1314:
            console.print(Panel(
                "[red]Sem permissão para criar symlinks no Windows.[/]\n\n"
                "Ative o Modo Desenvolvedor:\n"
                "  Configurações → Sistema → Para Desenvolvedores → Modo Desenvolvedor\n\n"
                "Ou execute o script como Administrador.",
                title="Erro de permissão",
                border_style="red",
            ))
            sys.exit(1)
        raise


def apply_changes(proj: ProjectStatus) -> None:
    changes = list_changes(proj)
    created = 0
    skipped = 0

    for c in changes:
        link_path = proj.path / c.item.path

        if c.action == "create_file":
            link_path.write_text(AGENTS_MD_TEMPLATE, encoding="utf-8")
            console.print(f"  [green]+[/]  AGENTS.md criado")
            created += 1

        elif c.action == "mkdir":
            link_path.mkdir(parents=True, exist_ok=True)
            console.print(f"  [blue]mkdir[/]  {c.item.path}")
            created += 1

        elif c.action in ("symlink", "update"):
            make_symlink(link_path, c.item.target, c.item.is_dir)
            verb = "criado" if c.action == "symlink" else "atualizado"
            console.print(f"  [green]+[/]  {c.item.path} → {c.item.target}  [dim]({verb})[/]")
            created += 1

        elif c.action == "skip":
            console.print(f"  [red]⚠[/]  {c.item.path}  [dim](pulado)[/]")
            skipped += 1

    console.print(f"\n  [green]{created} alterações aplicadas[/]", end="")
    if skipped:
        console.print(f", [yellow]{skipped} puladas[/]", end="")
    console.print()


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Padroniza configs de IA via AGENTS.md symlinks"
    )
    parser.add_argument(
        "--path", "-p", default=".",
        help="Diretório pai com os projetos (padrão: diretório atual)"
    )
    args = parser.parse_args()

    root = Path(args.path).resolve()

    os_label = f"Windows {'(Developer Mode necessário para symlinks)' if IS_WINDOWS else ''}" \
        if IS_WINDOWS else platform.system()
    console.print(f"\n[bold]agents-sync[/] — [dim]{os_label}[/]")
    console.print(f"Escaneando [cyan]{root}[/cyan]...\n")

    projects = scan_projects(root)
    if not projects:
        console.print("[red]Nenhum projeto encontrado.[/]")
        return

    render_table(projects)

    selected = select_projects(projects)
    if not selected:
        console.print("[dim]Saindo.[/]")
        return

    has_changes = False
    for proj in selected:
        if preview_changes(proj):
            has_changes = True

    if not has_changes:
        return

    console.print()
    confirm = console.input("[bold]Aplicar mudanças?[/] [dim](s/N)[/dim]: ").strip().lower()
    if confirm not in ("s", "sim", "y", "yes"):
        console.print("[dim]Cancelado.[/]")
        return

    console.print()
    for proj in selected:
        console.print(f"[bold cyan]{proj.name}[/bold cyan]")
        apply_changes(proj)
        console.print()

    console.print("[green]Concluído.[/]")


if __name__ == "__main__":
    main()
