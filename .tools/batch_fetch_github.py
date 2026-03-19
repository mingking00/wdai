#!/usr/bin/env python3
"""
Batch Parallel GitHub File Fetcher
批量并行获取 GitHub 文件
"""

import asyncio
import aiohttp
import sys
from urllib.parse import urlparse

async def fetch_file(session: aiohttp.ClientSession, url: str, timeout: int = 30) -> dict:
    """Fetch a single file."""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
            if resp.status == 200:
                content = await resp.text()
                return {"url": url, "status": 200, "content": content, "error": None}
            else:
                return {"url": url, "status": resp.status, "content": None, 
                        "error": f"HTTP {resp.status}"}
    except Exception as e:
        return {"url": url, "status": None, "content": None, "error": str(e)}

async def batch_fetch(urls: list[str], max_concurrent: int = 10) -> list[dict]:
    """Fetch multiple files in parallel."""
    connector = aiohttp.TCPConnector(limit=max_concurrent, limit_per_host=5)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_file(session, url) for url in urls]
        return await asyncio.gather(*tasks)

def github_raw_url(repo: str, branch: str, path: str) -> str:
    """Convert GitHub repo path to raw URL."""
    # repo format: owner/repo
    return f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"

async def fetch_repo_files(repo: str, branch: str, paths: list[str]) -> dict[str, str]:
    """
    Batch fetch files from a GitHub repository.
    
    Args:
        repo: Repository in format "owner/repo"
        branch: Branch name (e.g., "main", "master")
        paths: List of file paths in the repo
    
    Returns:
        Dict mapping file paths to their contents
    """
    urls = [github_raw_url(repo, branch, p) for p in paths]
    results = await batch_fetch(urls)
    
    output = {}
    for i, result in enumerate(results):
        path = paths[i]
        if result["content"]:
            output[path] = result["content"]
        else:
            print(f"⚠️  Failed to fetch {path}: {result['error']}", file=sys.stderr)
    
    return output

# Example usage for LinguaCafe
LINGUACAFE_FILES = [
    "app/Models/Word.php",
    "app/Models/Book.php",
    "app/Models/Chapter.php",
    "app/Models/Vocabulary.php",
    "app/Http/Controllers/BookController.php",
    "resources/js/components/Reader.vue",
    "resources/js/components/VocabularyHighlighter.vue",
    "database/migrations/2023_01_01_create_words_table.php",
]

if __name__ == "__main__":
    # Example: Fetch LinguaCafe core files
    print("🚀 Batch fetching LinguaCafe files...")
    files = asyncio.run(fetch_repo_files(
        repo="simjanos-dev/LinguaCafe",
        branch="main",
        paths=LINGUACAFE_FILES
    ))
    
    for path, content in files.items():
        print(f"\n{'='*60}")
        print(f"📄 {path} ({len(content)} chars)")
        print('='*60)
        print(content[:500] + "..." if len(content) > 500 else content)
