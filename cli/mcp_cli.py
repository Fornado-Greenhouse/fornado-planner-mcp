import click
import asyncio
import httpx
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from typing import Optional

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
@click.option('--plan-id', required=True, help='Plan ID')
def list_tasks(plan_id: str):
    async def _list():
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:8080/planner/plans/{plan_id}/tasks")
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
