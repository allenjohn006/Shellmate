import json
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from .ai import query_ai
from .executor import classify_command, run_command
from .config import load_config

console = Console()

def run_agent(goal: str):
    console.print(Panel(
        f"[bold]Goal:[/bold] {goal}",
        title="[bold blue]Shellmate Agent Mode[/bold blue]",
        border_style="blue"
    ))

    config = load_config()
    dry_run = config.get("dry_run", False)

    if dry_run:
        console.print("[yellow]DRY RUN mode — commands will be shown but not executed.[/yellow]\n")

    # Full conversation history fed back to AI each round
    chat_history = []
    # The first prompt asks AI to plan steps for the goal
    prompt = (
        f"Goal: {goal}\n"
        f"Plan the steps required to achieve this goal. "
        f"Return a JSON object with a 'steps' array. "
        f"If the goal is already complete, return an empty steps array."
    )

    max_rounds = 10  # safety cap to avoid infinite loops
    round_num = 0

    while round_num < max_rounds:
        round_num += 1
        console.print(f"\n[cyan]Planning... (round {round_num})[/cyan]")

        response_data = query_ai(prompt, is_agent=True, chat_history=chat_history)

        if not response_data:
            console.print("[red]Agent halted — API error or could not parse response.[/red]")
            break

        # Record this exchange in history
        chat_history.append({"role": "user", "content": prompt})
        chat_history.append({"role": "assistant", "content": json.dumps(response_data)})

        steps = response_data.get("steps", [])

        if not steps:
            console.print(Panel(
                "[green]✅ Goal completed! No further steps needed.[/green]",
                border_style="green"
            ))
            break

        console.print(f"[dim]AI planned {len(steps)} step(s) for this round.[/dim]")

        # Execute each step one by one
        step_index = 0
        while step_index < len(steps):
            step = steps[step_index]
            command = step.get("command", "").strip()
            explanation = step.get("explanation", "")
            is_destructive = step.get("is_destructive", False)

            if not command:
                step_index += 1
                continue

            # Show the step
            console.print(f"\n[bold magenta]Step {step_index + 1} of {len(steps)}:[/bold magenta] {explanation}")

            # Classify safety even if not flagged by AI
            safety = classify_command(command)
            if safety == "destructive" or is_destructive:
                console.print(Panel(
                    f"[red]⚠️  DESTRUCTIVE COMMAND DETECTED[/red]\n{command}",
                    border_style="red"
                ))
            else:
                console.print(Panel(f"[bold green]{command}[/bold green]", border_style="green"))

            if dry_run:
                console.print(f"[yellow][DRY RUN] Would execute: {command}[/yellow]")
                step_index += 1
                continue

            # Single clean prompt for user choice
            console.print("[dim]  (y) run  (n) reject  (s) skip  (a) abort[/dim]")
            choice = Prompt.ask("  Action", choices=["y", "n", "s", "a"], default="y")

            if choice == "a":
                console.print("[yellow]Agent aborted by user.[/yellow]")
                return

            elif choice == "s":
                console.print("[yellow]⏭  Step skipped.[/yellow]")
                step_index += 1
                continue

            elif choice == "n":
                feedback = Prompt.ask("  Why? (feedback sent to AI)")
                prompt = (
                    f"User rejected the command '{command}'. Reason: {feedback}. "
                    f"Please revise the plan and continue working toward the original goal: {goal}"
                )
                break  # re-plan with feedback

            elif choice == "y":
                console.print("[dim]  Executing...[/dim]")
                result = run_command(command, dry_run=False)

                if result["returncode"] != 0:
                    # Command failed — show error and ask AI to fix
                    error_output = result["stderr"] or result["stdout"] or "Unknown error"
                    console.print(Panel(
                        error_output[:600],
                        title="[red]Command Failed[/red]",
                        border_style="red"
                    ))
                    prompt = (
                        f"The command '{command}' failed with exit code {result['returncode']}.\n"
                        f"Error output:\n{error_output[:600]}\n"
                        f"Please revise the plan to fix this and continue toward the goal: {goal}"
                    )
                    break  # re-plan with error context

                else:
                    # Command succeeded — show output and move to next step
                    stdout = result["stdout"].strip()
                    if stdout:
                        console.print(Panel(
                            stdout[:500] + ("..." if len(stdout) > 500 else ""),
                            title="[green]Output[/green]",
                            border_style="green"
                        ))
                    console.print("[green]✅ Step completed.[/green]")
                    step_index += 1

                    # If this was the last step, ask AI if goal is done
                    if step_index >= len(steps):
                        prompt = (
                            f"All planned steps completed successfully.\n"
                            f"Last command output: {stdout[:300]}\n"
                            f"Is the original goal fully achieved: '{goal}'? "
                            f"If yes, return empty steps array. "
                            f"If more steps are needed, return them."
                        )
                        break  # go back to AI for next round check
        else:
            # All steps in this round executed without breaking
            # Ask AI if there's anything left to do
            prompt = (
                f"All planned steps for this round completed successfully. "
                f"Is the original goal fully achieved: '{goal}'? "
                f"If yes, return empty steps array. If more steps are needed, return them."
            )

    else:
        console.print(f"[yellow]Agent reached maximum rounds ({max_rounds}). Stopping.[/yellow]")