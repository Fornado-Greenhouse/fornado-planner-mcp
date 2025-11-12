"""
MCP CLI - Command-line interface for testing Microsoft Planner MCP Server
"""

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
    """Microsoft Planner MCP CLI"""
    pass


@cli.command()
@click.option('--plan-id', required=True, help='Plan ID')
def get_plan(plan_id: str):
    async def _get():
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:8080/planner/plans/{plan_id}")
            plan = response.json()
            
            rprint(f"[cyan]Plan: {plan.get('title', 'Untitled')}[/cyan]")
            rprint(f"ID: {plan.get('id')}")
            rprint(f"Owner: {plan.get('owner')}")
            if plan.get('created_date_time'):
                rprint(f"Created: {plan.get('created_date_time')}")
    
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
def list_groups():
    """List all Microsoft 365 Groups (Teams) accessible by the app"""
    async def _list():
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get("http://localhost:8080/planner/groups")
                
                if response.status_code == 503:
                    rprint("[red]Server not authenticated with Azure[/red]")
                    return
                
                response.raise_for_status()
                data = response.json()
                
                rprint(f"[green]Found {data['count']} Microsoft 365 Groups[/green]")
                
                if data['groups']:
                    table = Table(title="Microsoft 365 Groups")
                    table.add_column("Group ID", style="cyan")
                    table.add_column("Display Name", style="green")
                    table.add_column("Description", style="yellow")
                    
                    for group in data['groups']:
                        table.add_row(
                            group.get("id", ""),
                            group.get("displayName", ""),
                            group.get("description", "")[:50] if group.get("description") else ""
                        )
                    
                    console.print(table)
                    rprint("\n[yellow]Use a Group ID to list its plans:[/yellow]")
                    rprint("python cli/mcp_cli.py list-group-plans --group-id <GROUP_ID>")
                else:
                    rprint("[yellow]No groups found. Make sure your Azure app has Group.Read.All permission[/yellow]")
        except httpx.ConnectError:
            rprint("[red]❌ Cannot connect to server[/red]")
            rprint("Make sure the HTTP Test Server workflow is running")
        except Exception as e:
            rprint(f"[red]Error: {e}[/red]")
    
    asyncio.run(_list())


@cli.command()
@click.option('--group-id', required=True, help='Microsoft 365 Group ID')
def list_group_plans(group_id: str):
    """List all Planner plans for a specific group"""
    async def _list():
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"http://localhost:8080/planner/groups/{group_id}/plans")
                
                if response.status_code == 404:
                    rprint(f"[red]Group ID '{group_id}' not found[/red]")
                    return
                
                if response.status_code == 503:
                    rprint("[red]Server not authenticated with Azure[/red]")
                    return
                
                response.raise_for_status()
                data = response.json()
                
                rprint(f"[green]Found {data['count']} plans in this group[/green]")
                
                if data['plans']:
                    table = Table(title=f"Plans for Group {group_id}")
                    table.add_column("Plan ID", style="cyan")
                    table.add_column("Title", style="green")
                    table.add_column("Owner", style="yellow")
                    
                    for plan in data['plans']:
                        table.add_row(
                            plan.get("id", ""),
                            plan.get("title", "Untitled"),
                            plan.get("owner", "")[:30] if plan.get("owner") else ""
                        )
                    
                    console.print(table)
                    
                    if data['plans']:
                        first_plan_id = data['plans'][0].get('id')
                        rprint(f"\n[yellow]Example: List tasks for the first plan:[/yellow]")
                        rprint(f"python cli/mcp_cli.py list-tasks --plan-id {first_plan_id}")
                else:
                    rprint("[yellow]No plans found in this group[/yellow]")
        except httpx.ConnectError:
            rprint("[red]❌ Cannot connect to server[/red]")
            rprint("Make sure the HTTP Test Server workflow is running")
        except Exception as e:
            rprint(f"[red]Error: {e}[/red]")
    
    asyncio.run(_list())


@cli.command()
@click.option('--plan-id', required=True, help='Plan ID')
def list_tasks(plan_id: str):
    async def _list():
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"http://localhost:8080/planner/plans/{plan_id}/tasks")
                
                if response.status_code == 404:
                    rprint(f"[red]Plan ID '{plan_id}' not found[/red]")
                    rprint("\n[yellow]Tip: Use 'list-groups' command to discover your Plan IDs[/yellow]")
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
            table.add_column("Status", style="yellow")
            table.add_column("Priority")
            
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
            rprint("\n[yellow]Tip: Use 'list-groups' command to discover valid Plan IDs[/yellow]")
        except Exception as e:
            rprint(f"[red]Error: {e}[/red]")
    
    asyncio.run(_list())


@cli.command()
@click.option('--plan-id', required=True, help='Plan ID')
@click.option('--title', required=True, help='Task title')
@click.option('--bucket-id', help='Bucket ID (optional)')
def create_task(plan_id: str, title: str, bucket_id: Optional[str]):
    async def _create():
        async with httpx.AsyncClient() as client:
            params = {
                "plan_id": plan_id,
                "title": title
            }
            if bucket_id:
                params["bucket_id"] = bucket_id
            
            response = await client.post(
                "http://localhost:8080/tools/create_task",
                params=params
            )
            response.raise_for_status()
            result = response.json()
            
            rprint(f"[green]Task created successfully![/green]")
            rprint(f"Task ID: {result.get('task_id')}")
            rprint(f"Title: {result.get('title')}")
    
    asyncio.run(_create())


if __name__ == "__main__":
    cli()