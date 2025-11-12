import click
import asyncio
import httpx
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from typing import Optional
import json

console = Console()


@click.group()
def cli():
    pass


@cli.command()
@click.option('--plan-id', required=True, help='Plan ID')
def get_plan(plan_id: str):
    async def _get():
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:8080/planner/plans/{plan_id}")
            rprint(response.json())
    
    asyncio.run(_get())


@cli.command()
def health():
    """Check server health and authentication status"""
    async def _check():
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:8080/health")
                data = response.json()
                
                if data.get("services_initialized"):
                    rprint("[green]✅ Server is running and authenticated![/green]")
                else:
                    rprint("[yellow]⚠️ Server is running but not authenticated[/yellow]")
                    rprint("Check your Azure credentials in .env file")
                
                rprint(f"Status: {data}")
        except httpx.ConnectError:
            rprint("[red]❌ Cannot connect to server[/red]")
            rprint("Make sure the HTTP Test Server workflow is running")
        except Exception as e:
            rprint(f"[red]Error: {e}[/red]")
    
    asyncio.run(_check())


@cli.command()
@click.option('--plan-id', required=True, help='Plan ID')
def list_tasks(plan_id: str):
    async def _list():
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"http://localhost:8080/planner/plans/{plan_id}/tasks")
                
                if response.status_code == 404:
                    rprint(f"[red]Plan ID '{plan_id}' not found[/red]")
                    rprint("\n[yellow]Tip: Use a real Plan ID from your Microsoft Planner[/yellow]")
                    rprint("See docs/TESTING_GUIDE.md for how to find valid Plan IDs")
                    return
                
                if response.status_code == 503:
                    rprint("[red]Server not authenticated with Azure[/red]")
                    rprint("Check your .env file and Azure credentials")
                    return
                
                response.raise_for_status()
                tasks = response.json()
            
            table = Table(title=f"Tasks for Plan {plan_id}")
            table.add_column("ID", style="cyan")
            table.add_column("Title", style="green")
            table.add_column("Progress", style="yellow")
            table.add_column("Priority", style="magenta")
            
            for task in tasks:
                table.add_row(
                    task.get("id", ""),
                    task.get("title", ""),
                    f"{task.get('percentComplete', 0)}%",
                    str(task.get("priority", "N/A"))
                )
            
            console.print(table)
        except httpx.ConnectError:
            rprint("[red]❌ Cannot connect to server[/red]")
            rprint("Make sure the HTTP Test Server workflow is running")
        except httpx.ReadTimeout:
            rprint("[red]Request timed out[/red]")
            rprint(f"The server couldn't find plan '{plan_id}' after retrying")
            rprint("\n[yellow]Tip: Use a real Plan ID from your Microsoft Planner[/yellow]")
        except Exception as e:
            rprint(f"[red]Error: {e}[/red]")
    
    asyncio.run(_list())


@cli.command()
@click.option('--plan-id', required=True, help='Plan ID')
@click.option('--title', required=True, help='Task title')
@click.option('--bucket-id', help='Bucket ID')
@click.option('--priority', type=int, help='Priority (0-10)')
def create_task(plan_id: str, title: str, bucket_id: Optional[str], priority: Optional[int]):
    async def _create():
        data = {
            "plan_id": plan_id,
            "title": title
        }
        if bucket_id:
            data["bucket_id"] = bucket_id
        if priority is not None:
            data["priority"] = priority
        
        async with httpx.AsyncClient() as client:
            response = await client.post("http://localhost:8080/tools/create_task", json=data)
            rprint("[green]Task created successfully![/green]")
            rprint(response.json())
    
    asyncio.run(_create())


if __name__ == "__main__":
    cli()
