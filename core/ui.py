import sys

try:
    from rich.console import Console
    console = Console()
except ImportError:
    class DummyConsole:
        def print(self, *args, **kwargs):
            if args:
                import re
                clean_text = re.sub(r'\[/?[a-zA-Z0-9_# -]+\]', '', str(args[0]))
                end = kwargs.get('end', '\n')
                print(clean_text, end=end)
    console = DummyConsole()

def styled_prompt(message: str = "", context: str = "~") -> str:
    """
    Renders T3RMUX terminal themed prompt:
    ┌─[FeaturesticLeaks@termux]-[context] (Optional Message)
    └─>>> 
    """
    has_leading_nl = message.startswith('\n') or message.startswith('\r\n')
    clean_msg = message.lstrip('\r\n').strip()
    if clean_msg.startswith("-> "):
        clean_msg = clean_msg[3:].strip()
        
    if has_leading_nl:
        console.print()

    # Header line
    header = (
        "[dim cyan]┌─[/dim cyan]"
        "[dim][[/dim]"
        "[bold bright_magenta]FeaturesticLeaks[/bold bright_magenta]"
        "[bold bright_cyan]@termux[/bold bright_cyan]"
        "[dim]][/dim]"
        "[dim cyan]─[/dim cyan]"
        "[dim][[/dim]"
        f"[bold yellow]{context}[/bold yellow]"
        "[dim]][/dim]"
    )
    
    if clean_msg:
        if clean_msg.lower().startswith("press enter"):
            header += f" [dim yellow]({clean_msg})[/dim yellow]"
        else:
            header += f" [dim]({clean_msg})[/dim]"

    console.print(header)

    # Prompt arrow line
    prompt_line = "[dim cyan]└─[/dim cyan][bold #FF6B6B]>>>[/bold #FF6B6B] "
    console.print(prompt_line, end="")

    try:
        return input()
    except (EOFError, RuntimeError):
        try:
            if sys.platform != 'win32':
                with open('/dev/tty', 'r') as tty:
                    return tty.readline().rstrip('\n')
            else:
                with open('CON', 'r') as con:
                    return con.readline().rstrip('\r\n')
        except Exception:
            return ""
    except Exception:
        return ""

def safe_input(prompt: str = '', context: str = '~') -> str:
    return styled_prompt(message=prompt, context=context)

def human_size(size: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f'{size:.2f} {unit}'
        size /= 1024.0
    return f'{size:.2f} PB'
