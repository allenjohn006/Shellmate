import json
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from .ai import query_ai
from .executor import classify_command, run_command
from .config import load_config

console = Console()

def run_agent(goal: str):
    console.print(Panel(f"Agent Goal: {goal}", title="[bold blue]Shellmate Agent Mode[/bold blue]", border_style="blue"))
    
    chat_history = []
    config = load_config()
    dry_run = config.get("dry_run", False)
    
    # Step 1: Initial Planning
    console.print("[cyan]Thinking... Planning steps...[/cyan]")
    prompt = f"Goal: {goal}\nPlan the steps required to achieve this goal."
    
    while True:
        response_data = query_ai(prompt, is_agent=True, chat_history=chat_history)
        if not response_data:
            console.print("[red]Agent execution halted due to API error.[/red]")
            break
            
        chat_history.append({"role": "user", "content": prompt})
        chat_history.append({"role": "assistant", "content": json.dumps(response_data)})
        
        steps = response_data.get("steps", [])
        if not steps:
            console.print("[green]Goal completed or no further steps needed.[/green]")
            break
            
        # Execute steps
        all_completed = True
        for i, step in enumerate(steps, 1):
            command = step.get("command")
            explanation = step.get("explanation")
            
            console.print(f"\n[bold magenta]Step {i}:[/bold magenta] {explanation}")
            console.print(Panel(command, border_style="green"))
            
            if dry_run:
                run_command(command, dry_run=True)
                continue
                
            safety = classify_command(command)
            if safety == "destructive":
                console.print("[red]⚠️  This command is flagged as DESTRUCTIVE.[/red]")
                
            # Prompt user
            choice = Prompt.ask(
                "[bold cyan]Action[/bold cyan]", 
                choices=["y", "n", "s", "a"], 
                default="y",
                show_choices=False,
                show_default=False
            )
            # Make a custom prompt for choices:
            console.print("[dim](y)es, (n)o, (s)kip, (a)bort[/dim]")
            
            choice = Prompt.ask("Choose", choices=["y", "n", "s", "a"], default="y")
            
            if choice == "a":
                console.print("[yellow]Agent aborted by user.[/yellow]")
                return
            elif choice == "s":
                console.print("[yellow]Skipping step.[/yellow]")
                prompt = f"User skipped the previous step. Continue with next steps to achieve the goal: {goal}"
                all_completed = False
                break
            elif choice == "n":
                console.print("[yellow]Step rejected.[/yellow]")
                feedback = Prompt.ask("Why? (This feedback will be sent to the AI)")
                prompt = f"User rejected the step '{command}'. Reason: {feedback}. Please adjust the plan."
                all_completed = False
                break
            elif choice == "y":
                # Execute
                console.print("[dim]Executing...[/dim]")
                result = run_command(command, dry_run=False)
                
                if result["returncode"] != 0:
                    console.print(Panel(result["stderr"], title="[red]Error Output[/red]", border_style="red"))
                    prompt = f"Command '{command}' failed with exit code {result['returncode']}.\nError: {result['stderr']}\nPlease adjust the plan to fix this."
                    all_completed = False
                    break
                else:
                    if result["stdout"]:
                        console.print(Panel(result["stdout"][:500] + ("..." if len(result["stdout"]) > 500 else ""), title="[green]Output[/green]", border_style="green"))
                    prompt = f"Command '{command}' succeeded.\nOutput: {result['stdout'][:500]}\nPlan the next steps if the goal is not yet fully achieved, or return an empty steps array."
                    # Continue to next step in the loop if we want, or we can feed back immediately.
                    # Given the prompt instructs step 7 & 8: "feed output back to AI as context, AI decides next step"
                    # We should break and let the AI re-plan based on output.
                    all_completed = False
                    break
                    
        if all_completed and dry_run:
            break
