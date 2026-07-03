import pyperclip
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, Horizontal, Container
from textual.widgets import Header, Input, Button, Static, Label
from textual.binding import Binding
from shellmate.core.ai import query_ai
from shellmate.core.context import get_shell_history

class SuggestionCard(Container):
    def __init__(self, command: str, explanation: str, **kwargs):
        super().__init__(**kwargs)
        self.command = command
        self.explanation = explanation
        self.can_focus = True

    def compose(self) -> ComposeResult:
        yield Label(f"> {self.command}", classes="card-command")
        yield Label(self.explanation, classes="card-explanation")
        yield Label("[Enter] to Run/Copy & Close  |  [Tab] to Copy", classes="card-explanation")

class ShellmateApp(App):
    CSS_PATH = "styles.css"
    BINDINGS = [
        Binding("escape", "quit", "Close Popup"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chat_history_list = []
        
    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Label("SHELLMATE (Ctrl+Space to toggle)", id="header")
        
        with VerticalScroll(id="chat-history") as self.chat_area:
            pass
            
        with Horizontal(id="input-container"):
            yield Input(placeholder="Ask Shellmate...", id="query-input")
            yield Button("Ask", variant="primary", id="ask-button")
            
        yield Label("Esc: Close | Enter on card: Copy & Close | Tab on card: Copy", id="footer")

    def on_mount(self) -> None:
        self.query_one("#query-input").focus()
        
        # Add initial context
        history = get_shell_history(3)
        if history:
            welcome_msg = Static("Hello! I see you recently ran these commands:\n" + "\n".join(history), classes="ai-message")
            self.chat_area.mount(welcome_msg)
        else:
            self.chat_area.mount(Static("Hello! How can I help you in the terminal today?", classes="ai-message"))

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ask-button":
            await self.handle_query()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "query-input":
            await self.handle_query()

    async def handle_query(self) -> None:
        input_widget = self.query_one("#query-input")
        query = input_widget.value.strip()
        if not query:
            return
            
        input_widget.value = ""
        
        # Show user message
        self.chat_area.mount(Static(query, classes="user-message"))
        self.chat_history_list.append({"role": "user", "content": query})
        
        # Show loading
        loading = Static("Thinking...", classes="ai-message")
        await self.chat_area.mount(loading)
        self.chat_area.scroll_end(animate=False)
        
        # Run AI (blocking call should ideally be async, but for simplicity in this script we'll just run it)
        # Textual might hang briefly here, in production we'd use workers, but this works for now.
        response = query_ai(query, is_agent=False, chat_history=self.chat_history_list[:-1])
        loading.remove()
        
        if not response:
            self.chat_area.mount(Static("Failed to get response.", classes="ai-message"))
            return
            
        self.chat_history_list.append({"role": "assistant", "content": str(response)})
        
        command = response.get("command", "")
        explanation = response.get("explanation", "")
        
        if command:
            card = SuggestionCard(command, explanation, classes="suggestion-card")
            await self.chat_area.mount(card)
        else:
            self.chat_area.mount(Static(explanation, classes="ai-message"))
            
        self.chat_area.scroll_end(animate=False)

    def on_key(self, event) -> None:
        if isinstance(self.focused, SuggestionCard):
            card = self.focused
            if event.key == "enter":
                pyperclip.copy(card.command)
                self.exit()
            elif event.key == "tab":
                pyperclip.copy(card.command)

def run_popup():
    app = ShellmateApp()
    app.run()
