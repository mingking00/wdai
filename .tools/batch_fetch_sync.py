#!/usr/bin/env python3
"""
Batch GitHub File Fetcher - Synchronous version with ThreadPool
批量并行获取 GitHub 文件（同步版本）
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request
import urllib.error
import sys

def fetch_file(url: str, timeout: int = 30) -> dict:
    """Fetch a single file."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            content = resp.read().decode('utf-8')
            return {"url": url, "status": 200, "content": content, "error": None}
    except urllib.error.HTTPError as e:
        return {"url": url, "status": e.code, "content": None, "error": str(e)}
    except Exception as e:
        return {"url": url, "status": None, "content": None, "error": str(e)}

def batch_fetch(urls: list[str], max_workers: int = 5) -> list[dict]:
    """Fetch multiple files in parallel using threads."""
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(fetch_file, url): url for url in urls}
        for future in as_completed(future_to_url):
            results.append(future.result())
    return results

def github_raw_url(repo: str, branch: str, path: str) -> str:
    """Convert GitHub repo path to raw URL."""
    return f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"

def fetch_repo_files(repo: str, branch: str, paths: list[str]) -> dict[str, str]:
    """
    Batch fetch files from a GitHub repository.
    
    Returns:
        Dict mapping file paths to their contents
    """
    urls = [github_raw_url(repo, branch, p) for p in paths]
    results = batch_fetch(urls)
    
    output = {}
    for i, result in enumerate(results):
        path = paths[i]
        if result["content"]:
            output[path] = result["content"]
            print(f"✅ {path}", file=sys.stderr)
        else:
            print(f"⚠️  {path}: {result['error']}", file=sys.stderr)
    
    return output

if __name__ == "__main__":
    # Example usage
    FILES = [
        "app/Models/Word.php",
        "app/Models/Book.php",
        "resources/js/components/Reader.vue",
    ]
    
    print("Fetching...", file=sys.stderr)
    files = fetch_repo_files("simjanos-dev/LinguaCafe", "main", FILES)
    print(f"\nFetched {len(files)} files", file=sys.stderr)
