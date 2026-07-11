import pyperclip
from pathlib import Path
from typing import Optional
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, Horizontal, Container
from textual.widgets import Header, Input, Button, Static, Label
from textual.binding import Binding
from textual._work_decorator import work
from shellmate.core.ai import query_ai
from shellmate.core.context import get_shell_history

# Absolute path so styles.css loads correctly from any working directory
_CSS_PATH = str(Path(__file__).parent / "styles.css")


class SuggestionCard(Container):
    """A focusable card widget showing a command suggestion."""

    def __init__(self, command: str, explanation: str, is_alternative: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.command = command
        self.explanation = explanation
        self.is_alternative = is_alternative
        self.can_focus = True

    def compose(self) -> ComposeResult:
        prefix = "Alternative: " if self.is_alternative else ""
        yield Label(f"{prefix}$ {self.command}", classes="card-command")
        yield Label(self.explanation, classes="card-explanation")
        yield Label("↵ Copy & Close   Ctrl+C Copy", classes="card-hint")


class ShellmateApp(App):
    CSS_PATH = _CSS_PATH
    BINDINGS = [
        Binding("escape", "quit", "Close"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chat_history_list = []
        # Reference to the current loading indicator so we can remove it
        self._loading_widget: Optional[Static] = None

    def compose(self) -> ComposeResult:
        # No built-in Header — we render our own bar with id="header"
        yield Label(" SHELLMATE                   Ctrl+\\ to toggle  |  Esc to close", id="header")

        with VerticalScroll(id="chat-history") as self.chat_area:
            pass

        with Horizontal(id="input-container"):
            yield Input(placeholder="Ask Shellmate anything…", id="query-input")
            yield Button("Ask ↵", variant="primary", id="ask-button")

        yield Label("↵ Copy & Close   Ctrl+C Copy only   Esc Close", id="footer")

    def on_mount(self) -> None:
        self.query_one("#query-input").focus()

        # Show recent shell history as welcome context
        history = get_shell_history(3)
        if history:
            welcome_text = " Recent commands:\n" + "\n".join(f"  $ {cmd}" for cmd in history)
            self.chat_area.mount(Static(welcome_text, classes="ai-message"))
        else:
            self.chat_area.mount(Static(" Hello! How can I help you in the terminal today?", classes="ai-message"))

    # ── Event handlers ──────────────────────────────────────────────────────────

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ask-button":
            await self.handle_query()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "query-input":
            await self.handle_query()

    def on_key(self, event) -> None:
        """Handle key presses on focused SuggestionCards."""
        if isinstance(self.focused, SuggestionCard):
            card = self.focused
            if event.key == "enter":
                # Copy command to clipboard and close the popup
                pyperclip.copy(card.command)
                self.exit()
            elif event.key == "ctrl+c":
                # Copy command without closing
                pyperclip.copy(card.command)

    # ── Query flow ──────────────────────────────────────────────────────────────

    async def handle_query(self) -> None:
        """Read the input, show user bubble, start a background worker for the AI call."""
        input_widget = self.query_one("#query-input")
        query = input_widget.value.strip()
        if not query:
            return

        input_widget.value = ""

        # Show the user's message in the chat
        self.chat_area.mount(Static(f"You: {query}", classes="user-message"))
        self.chat_history_list.append({"role": "user", "content": query})

        # Show a non-blocking loading indicator
        self._loading_widget = Static(" Thinking…", classes="ai-message")
        await self.chat_area.mount(self._loading_widget)
        self.chat_area.scroll_end(animate=False)

        # Fire the AI request in a background thread — does NOT block the TUI
        self.fetch_ai_response(query)

    @work(thread=True)
    def fetch_ai_response(self, query: str) -> None:
        """
        Worker that runs query_ai() in a background thread.
        Once complete, schedules handle_ai_response() back on the main thread.
        """
        response = query_ai(query, is_agent=False, chat_history=self.chat_history_list[:-1])
        # Post result back onto the Textual main thread safely
        self.call_from_thread(self.handle_ai_response, response)

    def handle_ai_response(self, response) -> None:
        """
        Called on the main thread after the worker finishes.
        Removes the loading indicator and mounts the response card(s).
        """
        # Remove the loading spinner
        if self._loading_widget is not None:
            self._loading_widget.remove()
            self._loading_widget = None

        if not response:
            self.chat_area.mount(Static(" Failed to get a response. Check your API key or connection.", classes="ai-message"))
            self.chat_area.scroll_end(animate=False)
            return

        self.chat_history_list.append({"role": "assistant", "content": str(response)})

        command = response.get("command", "")
        explanation = response.get("explanation", "")
        alternatives = response.get("alternatives", [])

        if command:
            # Primary suggestion card — auto-focus so user can hit Enter immediately
            card = SuggestionCard(command, explanation, is_alternative=False, classes="suggestion-card")
            self.chat_area.mount(card)
            card.focus()
        else:
            # Plain text explanation (no command returned)
            self.chat_area.mount(Static(f" {explanation}", classes="ai-message"))

        # Render each alternative as a smaller card
        for alt_cmd in alternatives:
            alt_card = SuggestionCard(alt_cmd, "Alternative suggestion", is_alternative=True, classes="suggestion-card alt-card")
            self.chat_area.mount(alt_card)

        self.chat_area.scroll_end(animate=False)


def run_popup():
    """Entry point called by the hotkey daemon and the hidden CLI command."""
    app = ShellmateApp()
    app.run()
