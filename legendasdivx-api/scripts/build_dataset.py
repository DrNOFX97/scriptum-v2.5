#!/usr/bin/env python3
"""Script para construir dataset de legendas"""

import httpx
import asyncio
import json
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
import csv

console = Console()
API_URL = "http://localhost:8000"

class DatasetBuilder:
    def __init__(self, output_dir: str = "./dataset"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.client = httpx.AsyncClient(timeout=60.0)
        
    async def search_movie(self, title: str, year: int = None):
        """Pesquisa filme em PT e EN"""
        results = {}
        
        for lang in ["pt-pt", "en"]:
            response = await self.client.get(
                f"{API_URL}/api/v1/search",
                params={
                    "query": title,
                    "language": lang,
                    "year": year,
                    "limit": 1
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["results"]:
                    results[lang] = data["results"][0]
        
        return results
    
    async def build_from_list(self, movies_file: str):
        """Constrói dataset a partir de lista de filmes"""
        
        # Ler lista de filmes
        with open(movies_file, 'r') as f:
            movies = json.load(f)
        
        dataset = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            
            task = progress.add_task(
                "[cyan]Construindo dataset...", 
                total=len(movies)
            )
            
            for movie in movies:
                title = movie.get("title")
                year = movie.get("year")
                
                progress.update(task, description=f"[cyan]Pesquisando: {title}")
                
                # Pesquisar legendas
                results = await self.search_movie(title, year)
                
                if "pt-pt" in results and "en" in results:
                    dataset.append({
                        "title": title,
                        "year": year,
                        "pt_id": results["pt-pt"]["id"],
                        "pt_release": results["pt-pt"]["release"],
                        "en_id": results["en"]["id"],
                        "en_release": results["en"]["release"],
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    console.print(f"[green]✓[/green] {title} - PT/EN pair encontrado")
                else:
                    console.print(f"[yellow]⚠[/yellow] {title} - Par incompleto")
                
                progress.update(task, advance=1)
                
                # Rate limiting
                await asyncio.sleep(5)
        
        # Guardar dataset
        output_file = self.output_dir / f"dataset_{datetime.now():%Y%m%d_%H%M%S}.json"
        with open(output_file, 'w') as f:
            json.dump(dataset, f, indent=2)
        
        console.print(f"\n[green]Dataset guardado:[/green] {output_file}")
        console.print(f"[green]Total de pares:[/green] {len(dataset)}")
        
        return dataset
    
    async def download_pairs(self, dataset_file: str):
        """Download de todos os pares do dataset"""
        
        with open(dataset_file, 'r') as f:
            dataset = json.load(f)
        
        downloads_dir = self.output_dir / "downloads"
        downloads_dir.mkdir(exist_ok=True)
        
        for item in dataset:
            title = item["title"]
            
            # Download PT
            pt_file = downloads_dir / f"{item['pt_id']}_pt.zip"
            if not pt_file.exists():
                console.print(f"Downloading PT: {title}")
                response = await self.client.get(
                    f"{API_URL}/api/v1/download/{item['pt_id']}"
                )
                if response.status_code == 200:
                    pt_file.write_bytes(response.content)
            
            # Download EN  
            en_file = downloads_dir / f"{item['en_id']}_en.zip"
            if not en_file.exists():
                console.print(f"Downloading EN: {title}")
                response = await self.client.get(
                    f"{API_URL}/api/v1/download/{item['en_id']}"
                )
                if response.status_code == 200:
                    en_file.write_bytes(response.content)
            
            await asyncio.sleep(10)  # Rate limiting conservador

async def main():
    """Exemplo de uso"""
    
    # Lista de filmes populares para teste
    test_movies = [
        {"title": "Oppenheimer", "year": 2023},
        {"title": "Barbie", "year": 2023},
        {"title": "The Matrix", "year": 1999},
        {"title": "Inception", "year": 2010},
        {"title": "Interstellar", "year": 2014},
    ]
    
    # Guardar lista de teste
    with open("movies_test.json", "w") as f:
        json.dump(test_movies, f)
    
    # Construir dataset
    builder = DatasetBuilder()
    dataset = await builder.build_from_list("movies_test.json")
    
    # Opcional: fazer download dos ficheiros
    # await builder.download_pairs("dataset/dataset_*.json")

if __name__ == "__main__":
    asyncio.run(main())
