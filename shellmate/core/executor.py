import subprocess
from rich.console import Console
from rich.panel import Panel

console = Console()

DESTRUCTIVE_PATTERNS = [
    "rm -rf", "rm -r", "sudo rm",
    "mkfs", "dd if=",
    "chmod 777", "chmod -R",
    "> /dev/", "format",
    ":(){:|:&};:",  # fork bomb
    "sudo su", "passwd"
]

def classify_command(command: str) -> str:
    """Classifies a command as 'safe' or 'destructive'."""
    cmd_lower = command.lower()
    for pattern in DESTRUCTIVE_PATTERNS:
        if pattern in cmd_lower:
            return "destructive"
            
    # Additional flag check for sudo with destructive operations
    if "sudo " in cmd_lower and any(word in cmd_lower for word in ["rm", "delete", "format", "wipe"]):
        return "destructive"
        
    return "safe"

def run_command(command: str, dry_run: bool = False) -> dict:
    """
    Executes a shell command. 
    If dry_run is True, prints it and returns immediately.
    Checks for destructive patterns and prompts for confirmation if found.
    """
    if dry_run:
        console.print(Panel(command, title="[yellow][DRY RUN] Command to Execute[/yellow]", border_style="yellow"))
        return {"stdout": "", "stderr": "", "returncode": 0}
        
    safety = classify_command(command)
    if safety == "destructive":
        console.print(Panel(
            "[red]This command matches destructive patterns and could harm your system![/red]\n"
            f"Command: {command}",
            title="⚠️ [red]WARNING: DESTRUCTIVE COMMAND[/red]", 
            border_style="red"
        ))
        
        confirmation = console.input("[bold red]This command is destructive. Type YES to confirm:[/bold red] ")
        if confirmation != "YES":
            console.print("[yellow]Command execution aborted by user.[/yellow]")
            return {"stdout": "", "stderr": "Execution aborted by user.", "returncode": -1}
            
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "returncode": 1
        }
