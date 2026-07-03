import json
import requests
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from .config import load_config
from .customs import load_customs
from .context import get_shell_history, get_project_context, detect_os

console = Console()

SYSTEM_PROMPT_TEMPLATE = """You are Shellmate, an AI-powered terminal assistant.
You are helping the user: {name}

User Preferences:
- Preferred Shell: {preferred_shell}
- Editor: {editor}
- Default Git Branch: {default_branch}

Environment:
- OS: {os}
- Current Working Directory: {cwd}

{custom_commands_context}
{project_context}

Last 5 shell commands executed by the user:
{shell_history}

Always respond in pure JSON format (do not wrap in markdown like ```json).
Depending on the task, your JSON must match this structure:

For standard commands or error explanations:
{{
  "command": "the main suggested command",
  "explanation": "plain english explanation",
  "alternatives": ["alt command 1", "alt command 2"],
  "is_destructive": false
}}

For agent mode tasks:
{{
  "steps": [
    {{"command": "cmd1", "explanation": "why cmd1", "is_destructive": false}},
    {{"command": "cmd2", "explanation": "why cmd2", "is_destructive": false}}
  ]
}}
"""

def build_system_prompt() -> str:
    config = load_config()
    customs = load_customs()
    history = get_shell_history(5)
    project_ctx = get_project_context()
    
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
    
    return SYSTEM_PROMPT_TEMPLATE.format(
        name=config.get("name", "User"),
        preferred_shell=config.get("preferred_shell", "bash"),
        editor=config.get("editor", "nano"),
        default_branch=config.get("default_branch", "main"),
        os=detect_os(),
        cwd=str(Path.cwd()),
        custom_commands_context=customs_str,
        project_context=project_str,
        shell_history=history_str
    )

def query_ai(prompt: str, is_agent: bool = False, chat_history: list = None) -> dict:
    config = load_config()
    provider = config.get("provider", "openrouter").lower()
    api_key = config.get("api_key", "")
    
    if not api_key:
        console.print(Panel("[red]API key not set. Please run `shellmate setup` or `shellmate config set api_key <your_key>`.[/red]", title="Error"))
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
            "messages": messages,
            "response_format": {"type": "json_object"}
        }
    elif provider == "anthropic":
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        # Anthropic doesn't support system in messages array directly like this, but keeping it simple for the wrapper.
        # Actually, let's properly format Anthropic
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
        headers = {
            "Content-Type": "application/json"
        }
        # Simplify conversion for Gemini
        gemini_contents = []
        for msg in messages:
            role = "user" if msg["role"] in ["user", "system"] else "model"
            gemini_contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })
        payload = {
            "contents": gemini_contents,
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }
    else:
        console.print(Panel(f"[red]Unsupported provider: {provider}[/red]", title="Error"))
        return None

    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 429:
            console.print(Panel("[red]User limit reached (Rate limit or quota exceeded).[/red]", title="API Error", border_style="red"))
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
            
        # Try to parse the content as JSON
        # Sometimes models wrap in markdown despite instructions
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Fallback for plain text response
            console.print(Panel("[yellow]Failed to parse AI response as JSON. Showing raw text:[/yellow]\n" + content))
            return None
            
    except requests.exceptions.RequestException as e:
        console.print(Panel(f"[red]API Request failed:[/red]\n{str(e)}", title="API Error", border_style="red"))
        if hasattr(e.response, 'text'):
            console.print(f"Details: {e.response.text}")
        return None
