import json
import typer
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

from shellmate.core.config import (
    load_config, save_config, get_config_value, set_config_value, is_setup_complete, CONFIG_DIR
)
from shellmate.core.customs import (
    load_customs, save_customs, add_custom, get_custom, remove_custom
)
from shellmate.core.ai import query_ai
from shellmate.core.agent import run_agent
from shellmate.core.executor import run_command
from shellmate.utils.models import FREE, PAID, get_all_models, get_model_by_id

app = typer.Typer(help="Shellmate: AI-powered terminal assistant", no_args_is_help=True)
custom_app = typer.Typer(help="Manage custom commands")
model_app = typer.Typer(help="Manage AI models")
config_app = typer.Typer(help="Manage configuration")
project_app = typer.Typer(help="Manage project contexts")

app.add_typer(custom_app, name="custom")
app.add_typer(model_app, name="model")
app.add_typer(config_app, name="config")
app.add_typer(project_app, name="project")

console = Console()

def check_setup():
    if not is_setup_complete():
        console.print(Panel("[yellow]Shellmate is not set up yet. Please run `shellmate setup` first.[/yellow]"))
        raise typer.Exit(1)

@app.callback()
def main_callback():
    """Shellmate: AI-powered terminal assistant"""
    pass

@app.command("ask", hidden=True)
def ask(query: str = typer.Argument(..., help="Ask Shellmate a question directly.")):
    """Ask Shellmate a question directly."""
    check_setup()
    console.print("[dim]Thinking...[/dim]")
    response = query_ai(query, is_agent=False)
    if response:
        cmd = response.get("command", "")
        exp = response.get("explanation", "")
        alts = response.get("alternatives", [])
        
        console.print(Panel(exp, title="[blue]Explanation[/blue]", border_style="blue"))
        if cmd:
            console.print(Panel(f"[bold green]{cmd}[/bold green]", title="[green]Suggested Command[/green]", border_style="green"))
        
        if alts:
            console.print("[dim]Alternatives:[/dim]")
            for alt in alts:
                console.print(f"  - {alt}")

def run():
    import sys
    SUBCOMMANDS = {
        "explain", "agent", "setup", "profile-setup", 
        "custom", "model", "config", "project", 
        "__popup", "--help", "-h", "--install-completion", "--show-completion"
    }
    if len(sys.argv) > 1 and sys.argv[1] not in SUBCOMMANDS and not sys.argv[1].startswith("-"):
        sys.argv.insert(1, "ask")
    app()


@app.command()
def explain(error_text: str = typer.Argument(..., help="The error text to explain.")):
    """Explain an error and suggest a fix."""
    check_setup()
    console.print("[dim]Analyzing error...[/dim]")
    prompt = f"Explain this error and suggest a fix command: {error_text}"
    response = query_ai(prompt, is_agent=False)
    if response:
        cmd = response.get("command", "")
        exp = response.get("explanation", "")
        
        console.print(Panel(exp, title="[red]Error Explanation[/red]", border_style="red"))
        if cmd:
            console.print(Panel(f"[bold green]{cmd}[/bold green]", title="[green]Suggested Fix[/green]", border_style="green"))

@app.command()
def agent(goal: str = typer.Argument(..., help="The goal for the agent to achieve."), dry_run: bool = typer.Option(False, "--dry-run", help="Show all planned steps but never execute subprocess.")):
    """Run the agentic loop to plan and execute multi-step terminal tasks."""
    check_setup()
    if dry_run:
        set_config_value("dry_run", True)
    
    try:
        run_agent(goal)
    finally:
        if dry_run:
            set_config_value("dry_run", False) # Revert dry run

@app.command()
def setup():
    """Full first-time wizard."""
    console.print(Panel("[bold cyan]Welcome to Shellmate Setup![/bold cyan]", border_style="cyan"))
    
    name = Prompt.ask("What is your name?", default="Developer")
    shell = Prompt.ask("Preferred shell", choices=["bash", "zsh", "fish"], default="bash")
    editor = Prompt.ask("Preferred editor", choices=["code", "vim", "nano", "nvim"], default="code")
    branch = Prompt.ask("Default git branch", default="main")
    
    console.print("\n[yellow]OpenRouter is recommended because it aggregates many free models.[/yellow]")
    provider = Prompt.ask("AI Provider", choices=["openrouter", "anthropic", "openai", "gemini"], default="openrouter")
    
    api_key = Prompt.ask(f"Enter your {provider} API key", password=True)
    
    # Model selection
    console.print("\n[bold]Available Free Models:[/bold]")
    for m in FREE:
        console.print(f"- {m['id']} ({m['provider']}) - {m['best_for']}")
        
    quick_model = Prompt.ask("Choose quick_model for inline suggestions", default=FREE[0]['id'])
    agent_model = Prompt.ask("Choose agent_model for complex tasks", default=FREE[1]['id'])
    
    config = {
        "name": name,
        "preferred_shell": shell,
        "editor": editor,
        "default_branch": branch,
        "provider": provider,
        "api_key": api_key,
        "quick_model": quick_model,
        "agent_model": agent_model,
        "theme": "dark",
        "always_confirm_destructive": True,
        "dry_run": False
    }
    save_config(config)
    
    # Shell hook installation
    home = Path.home()
    if shell == "bash":
        rc_path = home / ".bashrc"
    elif shell == "zsh":
        rc_path = home / ".zshrc"
    elif shell == "fish":
        rc_path = home / ".config" / "fish" / "config.fish"
        if not rc_path.parent.exists():
            rc_path.parent.mkdir(parents=True, exist_ok=True)
    
    hook = '\nalias sm="shellmate"\nshellmate-daemon &\n'
    if rc_path.exists():
        with open(rc_path, "r", encoding="utf-8") as f:
            content = f.read()
        if "shellmate-daemon" not in content:
            with open(rc_path, "a", encoding="utf-8") as f:
                f.write(hook)
    else:
        with open(rc_path, "w", encoding="utf-8") as f:
            f.write(hook)
            
    console.print(Panel(
        f"[green]Setup complete![/green]\n"
        f"Config saved to ~/.shellmate/config.yaml\n"
        f"Added `sm` alias and daemon auto-start to {rc_path}",
        title="Success"
    ))

@app.command()
def profile_setup():
    """Interactive prompts for name, shell, editor, default branch."""
    check_setup()
    config = load_config()
    config["name"] = Prompt.ask("Name", default=config.get("name"))
    config["preferred_shell"] = Prompt.ask("Preferred shell", choices=["bash", "zsh", "fish"], default=config.get("preferred_shell"))
    config["editor"] = Prompt.ask("Preferred editor", choices=["code", "vim", "nano", "nvim"], default=config.get("editor"))
    config["default_branch"] = Prompt.ask("Default git branch", default=config.get("default_branch"))
    save_config(config)
    console.print("[green]✓ Profile updated.[/green]")

# --- CUSTOM APP ---

@custom_app.command("add")
def custom_add():
    """Add a custom command template."""
    check_setup()
    name = Prompt.ask("Command name")
    desc = Prompt.ask("Description")
    cmd = Prompt.ask("Command template (use {var} for variables)")
    
    # Simple parsing for {variables}
    import re
    vars_found = re.findall(r"\{(\w+)\}", cmd)
    vars_unique = list(set(vars_found))
    
    custom = {
        "name": name,
        "description": desc,
        "command": cmd,
        "variables": vars_unique
    }
    
    add_custom(custom)
    console.print(f"[green]✓ Custom command '{name}' added successfully.[/green]")

@custom_app.command("list")
def custom_list():
    """List all custom commands."""
    check_setup()
    customs = load_customs()
    if not customs:
        console.print("No custom commands found.")
        return
        
    table = Table(title="Custom Commands")
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    table.add_column("Command", style="green")
    table.add_column("Variables")
    
    for c in customs:
        table.add_row(c.get("name"), c.get("description"), c.get("command"), ", ".join(c.get("variables", [])))
        
    console.print(table)

@custom_app.command("edit")
def custom_edit(name: str = typer.Argument(..., help="Name of the custom command to edit")):
    """Edit an existing custom command."""
    check_setup()
    c = get_custom(name)
    if not c:
        console.print(f"[red]Custom command '{name}' not found.[/red]")
        return
        
    new_name = Prompt.ask("Command name", default=c.get("name"))
    new_desc = Prompt.ask("Description", default=c.get("description"))
    new_cmd = Prompt.ask("Command template", default=c.get("command"))
    
    import re
    vars_found = re.findall(r"\{(\w+)\}", new_cmd)
    
    # Remove old and add new
    remove_custom(name)
    add_custom({
        "name": new_name,
        "description": new_desc,
        "command": new_cmd,
        "variables": list(set(vars_found))
    })
    console.print(f"[green]✓ Custom command '{new_name}' updated.[/green]")

@custom_app.command("remove")
def custom_remove(name: str = typer.Argument(..., help="Name of the custom command to remove")):
    """Remove a custom command."""
    check_setup()
    if Prompt.ask(f"Are you sure you want to delete '{name}'?", choices=["y", "n"]) == "y":
        if remove_custom(name):
            console.print(f"[green]✓ Removed '{name}'[/green]")
        else:
            console.print(f"[red]Command '{name}' not found.[/red]")

@custom_app.command("run", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def custom_run(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Name of the custom command to run")
):
    """Run a custom command. Pass variables as --name value or name=value."""
    check_setup()
    c = get_custom(name)
    if not c:
        console.print(f"[red]Custom command '{name}' not found.[/red]")
        return
        
    var_map = {}
    i = 0
    while i < len(ctx.args):
        arg = ctx.args[i]
        if arg.startswith("--"):
            key = arg[2:]
            if i + 1 < len(ctx.args) and not ctx.args[i+1].startswith("-"):
                var_map[key] = ctx.args[i+1]
                i += 2
            else:
                var_map[key] = "true"
                i += 1
        elif "=" in arg:
            k, v = arg.split("=", 1)
            var_map[k.strip()] = v.strip()
            i += 1
        else:
            i += 1
            
    cmd_template = c.get("command", "")
    required_vars = c.get("variables", [])
    
    for var_name in required_vars:
        if var_name not in var_map:
            val = Prompt.ask(f"Enter value for variable '{var_name}'")
            var_map[var_name] = val
        cmd_template = cmd_template.replace(f"{{{var_name}}}", var_map[var_name])
        
    console.print(f"[dim]Running custom command: {cmd_template}[/dim]")
    run_command(cmd_template)


# --- MODEL APP ---

@model_app.command("list")
def model_list():
    """List all available models."""
    check_setup()
    config = load_config()
    current_quick = config.get("quick_model")
    current_agent = config.get("agent_model")
    
    table = Table(title="Available AI Models")
    table.add_column("Tier")
    table.add_column("Status")
    table.add_column("Name", style="cyan")
    table.add_column("Provider")
    table.add_column("Speed")
    table.add_column("Best For")
    
    for m in FREE:
        status = []
        if m["id"] == current_quick: status.append("● Quick")
        if m["id"] == current_agent: status.append("● Agent")
        
        table.add_row("FREE", ", ".join(status), m["id"], m["provider"], m["speed"], m["best_for"])
        
    for m in PAID:
        status = []
        if m["id"] == current_quick: status.append("● Quick")
        if m["id"] == current_agent: status.append("● Agent")
        
        table.add_row("PAID", ", ".join(status), m["id"], m["provider"], m["speed"], m["best_for"])
        
    console.print(table)

@model_app.command("set")
def model_set(model_name: str = typer.Argument(..., help="Model ID to set as quick_model")):
    """Update quick_model in config."""
    check_setup()
    m = get_model_by_id(model_name)
    if m:
        set_config_value("quick_model", model_name)
        console.print(f"[green]✓ quick_model updated to {model_name}.[/green]")
        console.print(f"[dim]Tip: This model is best for {m['best_for']}.[/dim]")
    else:
        console.print(f"[red]Model '{model_name}' not found. Showing available list...[/red]")
        model_list()

# --- CONFIG APP ---

@config_app.command("set")
def config_set(key: str, value: str):
    """Update any single config value."""
    check_setup()
    set_config_value(key, value)
    console.print(f"[green]✓ Config '{key}' updated.[/green]")

@config_app.command("list")
def config_list():
    """List all current settings."""
    check_setup()
    config = load_config()
    
    table = Table(title="Configuration")
    table.add_column("Key", style="cyan")
    table.add_column("Value")
    
    for k, v in config.items():
        if k == "api_key" and v:
            display_val = f"***{v[-6:]}" if len(v) > 6 else "***"
        else:
            display_val = str(v)
        table.add_row(k, display_val)
        
    console.print(table)

# --- PROJECT APP ---

PROJECTS_DIR = CONFIG_DIR / "projects"

@project_app.command("add")
def project_add():
    """Add a new project context."""
    check_setup()
    if not PROJECTS_DIR.exists():
        PROJECTS_DIR.mkdir(parents=True)
        
    name = Prompt.ask("Project name")
    stack = Prompt.ask("Tech stack (e.g. django + react)")
    
    scripts = {}
    console.print("Add project scripts (leave script name empty to finish):")
    while True:
        s_name = Prompt.ask("Script name (e.g. start, test)")
        if not s_name:
            break
        s_cmd = Prompt.ask(f"Command for '{s_name}'")
        scripts[s_name] = s_cmd
        
    proj = {
        "project": name,
        "stack": stack,
        "scripts": scripts
    }
    
    import yaml
    with open(PROJECTS_DIR / f"{name}.yaml", "w") as f:
        yaml.dump(proj, f)
        
    console.print(f"[green]✓ Project '{name}' saved successfully to ~/.shellmate/projects/{name}.yaml[/green]")

@project_app.command("list")
def project_list():
    """Show all saved project contexts."""
    check_setup()
    if not PROJECTS_DIR.exists():
        console.print("No projects saved.")
        return
        
    import yaml
    table = Table(title="Saved Projects")
    table.add_column("Name", style="cyan")
    table.add_column("Stack")
    table.add_column("Scripts")
    
    for p_file in PROJECTS_DIR.glob("*.yaml"):
        with open(p_file, "r") as f:
            data = yaml.safe_load(f)
            if data:
                scripts_str = ", ".join(data.get("scripts", {}).keys())
                table.add_row(data.get("project", p_file.stem), data.get("stack", ""), scripts_str)
                
    console.print(table)

# For testing tui alone
@app.command(hidden=True)
def __popup():
    from shellmate.tui.popup import run_popup
    run_popup()

if __name__ == "__main__":
    run()
