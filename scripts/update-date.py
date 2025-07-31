#!/usr/bin/env python3
import re
import sys
from datetime import datetime, timedelta
import requests
from pathlib import Path

def get_last_repo_update(repo):
    """Fetch last update date from GitHub API"""
    url = f"https://api.github.com/repos/{repo}"
    response = requests.get(
        url,
        headers={"Accept": "application/vnd.github.v3+json"}
    )
    response.raise_for_status()
    return response.json()["pushed_at"]

def should_update(current_date, frequency):
    """Determine if update should occur based on frequency"""
    last_update = datetime.strptime(current_date, "%Y-%m-%d")
    return (datetime.now() - last_update).days >= frequency

def update_file_dates(file_path):
    """Update date in specified markdown file if needed"""
    content = Path(file_path).read_text()
    
    # Check if auto-update is enabled
    if not re.search(r'auto_update_date:\s*true', content, re.IGNORECASE):
        return False
    
    # Extract front matter parameters
    repo = re.search(r'repo:\s*"(.*?)"', content).group(1)
    frequency = int(re.search(r'update_frequency:\s*(\d+)', content).group(1))
    date_match = re.search(r'date:\s*(\d{4}-\d{2}-\d{2})', content)
    
    if not date_match:
        print(f"No date found in {file_path}")
        return False
    
    current_date = date_match.group(1)
    
    # Check update frequency
    if not should_update(current_date, frequency):
        return False
    
    # Get new date from GitHub
    new_date = get_last_repo_update(repo).split("T")[0]
    
    # Update the file
    updated_content = re.sub(
        r'(date:\s*)\d{4}-\d{2}-\d{2}',
        fr'\g<1>{new_date}',
        content
    )
    
    Path(file_path).write_text(updated_content)
    print(f"Updated {file_path} to date {new_date}")
    return True

def main():
    changed_files = []
    
    # Find all markdown files in content directory
    for md_file in Path("content").rglob("*.md"):
        try:
            if update_file_dates(md_file):
                changed_files.append(str(md_file))
        except Exception as e:
            print(f"Error processing {md_file}: {e}")
    
    # Exit code indicates if changes were made
    sys.exit(1 if changed_files else 0)

if __name__ == "__main__":
    main()