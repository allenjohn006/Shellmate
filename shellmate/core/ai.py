import json
import re
import requests
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from .config import load_config
from .customs import load_customs
from .context import get_shell_history, get_project_context, detect_os

console = Console()

def build_system_prompt() -> str:
    config = load_config()
    customs = load_customs()
    history = get_shell_history(5)
    project_ctx = get_project_context()

    name = config.get("name", "User")
    preferred_shell = config.get("preferred_shell", "bash")
    editor = config.get("editor", "nano")
    default_branch = config.get("default_branch", "main")
    os_name = detect_os()
    cwd = str(Path.cwd())

    customs_str = "Custom Commands Available:\n"
    if customs:
        for c in customs:
            customs_str += f"- {c.get('name')}: {c.get('description')} (Command: {c.get('command')})\n"
    else:
        customs_str += "None\n"

    project_str = "Current Project Context:\n"
    if project_ctx:
        project_str += json.dumps(project_ctx, indent=2) + "\n"
    else:
        project_str += "None\n"

    history_str = "\n".join(history) if history else "None"

    # Using f-string avoids .format() conflicts with JSON curly braces in the template
    return f"""You are Shellmate, an AI-powered terminal assistant.
You are helping the user: {name}

User Preferences:
- Preferred Shell: {preferred_shell}
- Editor: {editor}
- Default Git Branch: {default_branch}

Environment:
- OS: {os_name}
- Current Working Directory: {cwd}

{customs_str}
{project_str}

Last 5 shell commands executed by the user:
{history_str}

CRITICAL: Always respond in pure, valid JSON only. No markdown. No extra text. No duplicate keys.

For standard commands or error explanations, respond with exactly this structure:
{{"command": "the main suggested command", "explanation": "plain english explanation", "alternatives": ["alt command 1", "alt command 2"], "is_destructive": false}}

For agent mode tasks, respond with exactly this structure:
{{"steps": [{{"command": "cmd1", "explanation": "why", "is_destructive": false}}, {{"command": "cmd2", "explanation": "why", "is_destructive": false}}]}}
"""

def extract_json(content: str) -> dict | None:
    """Robustly extract JSON from model response even if malformed."""
    content = content.strip()

    # Strip markdown fences
    content = re.sub(r"^```json\s*", "", content)
    content = re.sub(r"^```\s*", "", content)
    content = re.sub(r"\s*```$", "", content)
    content = content.strip()

    # Try direct parse first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Try to extract first valid JSON object using regex
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Try to fix duplicate keys by taking the last occurrence
    # This handles the {}{}{}{ garbage the model sometimes returns
    clean = re.sub(r'\}\s*\{[^{}]*\}\s*(?=\})', '', content)
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass

    for closing in [']}', ']}]}', '}', '}}']:
        try:
             return json.loads(content + closing)
        except json.JSONDecodeError:
             continue

    return None

def query_ai(prompt: str, is_agent: bool = False, chat_history: list = None) -> dict:
    config = load_config()
    provider = config.get("provider", "openrouter").lower()
    api_key = config.get("api_key", "")

    if not api_key:
        console.print(Panel(
            "[red]API key not set. Run `shellmate config set api_key <your_key>`.[/red]",
            title="Error"
        ))
        return None

    model = config.get("agent_model") if is_agent else config.get("quick_model")
    system_prompt = build_system_prompt()

    messages = [{"role": "system", "content": system_prompt}]
    if chat_history:
        messages.extend(chat_history)
    messages.append({"role": "user", "content": prompt})

    headers = {}
    url = ""
    payload = {}

    if provider == "openrouter":
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages
            # Removed response_format json_object — not all free models support it
            # and it causes the duplicate key garbage we saw
        }

    elif provider == "anthropic":
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        system_content = messages[0]["content"]
        user_messages = messages[1:]
        payload = {
            "model": model,
            "system": system_content,
            "messages": user_messages,
            "max_tokens": 4096
        }

    elif provider == "openai":
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "response_format": {"type": "json_object"}
        }

    elif provider == "gemini":
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        gemini_contents = []
        for msg in messages:
            role = "user" if msg["role"] in ["user", "system"] else "model"
            gemini_contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })
        payload = {
            "contents": gemini_contents,
            "generationConfig": {"responseMimeType": "application/json"}
        }

    else:
        console.print(Panel(f"[red]Unsupported provider: {provider}[/red]", title="Error"))
        return None

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.status_code == 429:
            console.print(Panel(
                "[red]Rate limit hit. Try again in a moment or switch model with `sm model set`.[/red]",
                title="Rate Limited", border_style="red"
            ))
            return None

        response.raise_for_status()
        data = response.json()

        content = ""
        if provider in ["openrouter", "openai"]:
            content = data["choices"][0]["message"]["content"]
        elif provider == "anthropic":
            content = data["content"][0]["text"]
        elif provider == "gemini":
            content = data["candidates"][0]["content"]["parts"][0]["text"]

        result = extract_json(content)

        if result is None:
            console.print(Panel(
                f"[yellow]Could not parse response. Raw output:[/yellow]\n{content[:500]}",
                title="Parse Warning"
            ))

        return result

    except requests.exceptions.Timeout:
        console.print(Panel("[red]Request timed out. The model may be slow — try again.[/red]", title="Timeout", border_style="red"))
        return None
    except requests.exceptions.RequestException as e:
        console.print(Panel(f"[red]API Request failed:[/red]\n{str(e)}", title="API Error", border_style="red"))
        if hasattr(e, 'response') and e.response is not None:
            console.print(f"Details: {e.response.text}")
        return None