import sys
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from src.agent import AirlineAgent
from src.config import GEMINI_API_KEY, GEMINI_MODEL

console = Console()

def print_banner():
    banner = """
✈️  [bold cyan]SkyCare - Autonomous Airline Rebooking Agent[/bold cyan]  ✈️
Powered by [bold green]Google Gemini API[/bold green]
"""
    console.print(Panel(banner, border_style="cyan"))
    
    status_text = (
        f"[green]✓ Connected to Gemini Model:[/green] [bold]{GEMINI_MODEL}[/bold]"
        if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here"
        else "[yellow]⚠ Running in Demo / Mock Mode[/yellow] (Set [bold]GEMINI_API_KEY[/bold] in [bold].env[/bold] to use live LLM)"
    )
    console.print(Panel(status_text, border_style="yellow"))
    
    sample_info = """
[bold]Sample Test Scenarios (from data/sample_data.json):[/bold]
  • [bold]PNR: SKY101[/bold] | Passenger: [bold]John Doe[/bold] | Flight [bold]SK-402 (SFO -> JFK)[/bold] | [red]CANCELLED (Weather)[/red] | Tier: Platinum
  • [bold]PNR: SKY202[/bold] | Passenger: [bold]Sarah Connor[/bold] | Flight [bold]SK-510 (ORD -> LAX)[/bold] | [yellow]DELAYED (4 hours)[/yellow] | Tier: Silver
  • [bold]PNR: SKY303[/bold] | Passenger: [bold]David Smith[/bold] | Flight [bold]SK-800 (SEA -> MIA)[/bold] | [green]ON TIME[/green] | Tier: Regular
"""
    console.print(Panel(sample_info, title="Test Data Reference", border_style="blue"))

def main():
    print_banner()
    agent = AirlineAgent()
    
    console.print("\n[bold green]SkyCare Agent is ready.[/bold green] Type 'exit' or 'quit' to end session.\n")
    
    # Initial greeting from agent
    initial_greeting = agent.send_message("Greet the passenger politely and ask for their PNR and last name.")
    console.print(f"[bold cyan]SkyCare:[/bold cyan]")
    console.print(Markdown(initial_greeting))
    console.print()
    
    while True:
        try:
            user_input = console.input("[bold white]Passenger:[/bold white] ")
            if not user_input.strip():
                continue
            if user_input.strip().lower() in ["exit", "quit", "q"]:
                console.print("\n[bold cyan]SkyCare:[/bold cyan] Thank you for contacting SkyWay Airlines. Safe travels!\n")
                break
                
            response = agent.send_message(user_input)
            console.print(f"\n[bold cyan]SkyCare:[/bold cyan]")
            console.print(Markdown(response))
            console.print()
            
        except (KeyboardInterrupt, EOFError):
            console.print("\n\nSession terminated.")
            sys.exit(0)

if __name__ == "__main__":
    main()
