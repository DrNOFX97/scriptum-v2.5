#!/usr/bin/env python3
"""Script de teste da API"""

import httpx
import asyncio
from rich.console import Console
from rich.table import Table
from rich.progress import track
import json

console = Console()
API_URL = "http://localhost:8000"

async def test_health():
    """Testa endpoint de saúde"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{API_URL}/health")
        
        if response.status_code == 200:
            console.print("[green]✓[/green] Health check OK")
            console.print(response.json())
        else:
            console.print("[red]✗[/red] Health check falhou")

async def test_search(query: str = "Matrix"):
    """Testa pesquisa de legendas"""
    console.print(f"\n[yellow]Pesquisando:[/yellow] {query}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{API_URL}/api/v1/search",
            params={"query": query, "limit": 5}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Criar tabela com resultados
            table = Table(title=f"Resultados para '{query}'")
            table.add_column("ID", style="cyan")
            table.add_column("Título", style="magenta")
            table.add_column("Release", style="green")
            table.add_column("Idioma", style="yellow")
            table.add_column("Downloads", style="blue")
            
            for result in data["results"]:
                table.add_row(
                    result["id"],
                    result["title"][:40],
                    result["release"][:30],
                    result["language"],
                    str(result["downloads"])
                )
            
            console.print(table)
            console.print(f"\n[green]Total:[/green] {data['total']} resultados")
            console.print(f"[green]Cache:[/green] {'Sim' if data['cached'] else 'Não'}")
            console.print(f"[green]Tempo:[/green] {data['search_time']:.2f}s")
            
            return data["results"]
        else:
            console.print(f"[red]Erro:[/red] {response.status_code}")
            console.print(response.text)
            return []

async def test_download(subtitle_id: str):
    """Testa download de legenda"""
    console.print(f"\n[yellow]Downloading:[/yellow] {subtitle_id}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{API_URL}/api/v1/download/{subtitle_id}",
            follow_redirects=True
        )
        
        if response.status_code == 200:
            # Guardar ficheiro
            filename = f"test_subtitle_{subtitle_id}.zip"
            with open(filename, "wb") as f:
                f.write(response.content)
            
            console.print(f"[green]✓[/green] Download concluído: {filename}")
            console.print(f"[green]Tamanho:[/green] {len(response.content)} bytes")
        else:
            console.print(f"[red]Erro no download:[/red] {response.status_code}")

async def main():
    """Executa testes"""
    console.print("[bold blue]🧪 Testando Subtitle API[/bold blue]\n")
    
    # 1. Health check
    await test_health()
    
    # 2. Pesquisar
    results = await test_search("Oppenheimer")
    
    # 3. Download (se houver resultados)
    if results:
        first_id = results[0]["id"]
        await test_download(first_id)
    
    # 4. Testar cache (mesma pesquisa)
    console.print("\n[yellow]Testando cache (segunda pesquisa):[/yellow]")
    await test_search("Oppenheimer")
    
    # 5. Stats
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{API_URL}/api/v1/search/stats")
        console.print("\n[cyan]Rate Limiter Stats:[/cyan]")
        console.print(response.json())

if __name__ == "__main__":
    asyncio.run(main())
