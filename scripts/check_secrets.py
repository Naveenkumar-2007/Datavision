#!/usr/bin/env python3
"""
Security Check: Scan repository for hardcoded secrets

This script scans the codebase for potential hardcoded API keys,
passwords, and other secrets. Run this before committing code.

Usage:
    python scripts/check_secrets.py
    
Exit Codes:
    0 - No secrets found
    1 - Potential secrets detected
"""

import os
import re
import sys
from pathlib import Path

# Patterns that might indicate hardcoded secrets
SECRET_PATTERNS = [
    # API Keys
    (r'api_key\s*=\s*["\'][A-Za-z0-9_-]{20,}["\']', "Hardcoded API key"),
    (r'apikey\s*=\s*["\'][A-Za-z0-9_-]{20,}["\']', "Hardcoded API key"),
    (r'AIza[A-Za-z0-9_-]{35}', "Google API key"),
    (r'sk-[A-Za-z0-9]{48}', "OpenAI API key"),
    (r'gsk_[A-Za-z0-9]{52}', "Groq API key"),
    
    # Passwords
    (r'password\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded password"),
    (r'passwd\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded password"),
    
    # Tokens
    (r'token\s*=\s*["\'][A-Za-z0-9_-]{20,}["\']', "Hardcoded token"),
    (r'bearer\s+[A-Za-z0-9_-]{20,}', "Bearer token"),
    
    # AWS
    (r'AKIA[A-Z0-9]{16}', "AWS Access Key ID"),
    (r'aws_secret_access_key\s*=\s*["\'][^"\']+["\']', "AWS Secret Key"),
    
    # Database
    (r'mongodb\+srv://[^:]+:[^@]+@', "MongoDB connection string with credentials"),
    (r'postgres://[^:]+:[^@]+@', "PostgreSQL connection string with credentials"),
]

# Files/directories to skip
SKIP_PATTERNS = [
    '.git',
    'node_modules',
    '__pycache__',
    '.venv',
    'venv',
    '.env',
    '.env.local',
    'package-lock.json',
    'uv.lock',
    '.env.example',  # This file contains placeholders, not real secrets
]

# File extensions to check
CHECK_EXTENSIONS = ['.py', '.js', '.ts', '.tsx', '.jsx', '.json', '.yaml', '.yml', '.toml', '.md']


def should_skip(path: Path) -> bool:
    """Check if path should be skipped"""
    for pattern in SKIP_PATTERNS:
        if pattern in str(path):
            return True
    return False


def check_file(filepath: Path) -> list:
    """Check a single file for secrets"""
    findings = []
    
    try:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern, description in SECRET_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    # Skip if line contains environment variable reference
                    if 'os.environ' in line or 'os.getenv' in line or 'process.env' in line:
                        continue
                    # Skip if it's a placeholder/example
                    if 'your_' in line.lower() or '_here' in line.lower() or 'example' in line.lower():
                        continue
                    # Skip if it's in a comment explaining format
                    if line.strip().startswith('#') and any(x in line.lower() for x in ['format', 'example', 'like']):
                        continue
                        
                    findings.append({
                        'file': str(filepath),
                        'line': line_num,
                        'type': description,
                        'content': line.strip()[:100]  # First 100 chars
                    })
    except Exception as e:
        print(f"Warning: Could not read {filepath}: {e}")
    
    return findings


def main():
    """Main function"""
    print("🔍 Scanning repository for hardcoded secrets...")
    print()
    
    # Get repository root
    repo_root = Path(__file__).parent.parent
    
    all_findings = []
    files_scanned = 0
    
    for ext in CHECK_EXTENSIONS:
        for filepath in repo_root.rglob(f'*{ext}'):
            if should_skip(filepath):
                continue
            
            files_scanned += 1
            findings = check_file(filepath)
            all_findings.extend(findings)
    
    print(f"📁 Scanned {files_scanned} files")
    print()
    
    if all_findings:
        print(f"⚠️  Found {len(all_findings)} potential secret(s):")
        print()
        
        for finding in all_findings:
            print(f"  📄 {finding['file']}:{finding['line']}")
            print(f"     Type: {finding['type']}")
            print(f"     Content: {finding['content']}")
            print()
        
        print("❌ SECURITY CHECK FAILED")
        print()
        print("Please:")
        print("1. Remove hardcoded secrets from the files above")
        print("2. Use environment variables instead (os.environ['KEY'])")
        print("3. Add secrets to .env file (which is gitignored)")
        print("4. Run this script again to verify")
        
        return 1
    else:
        print("✅ No hardcoded secrets found!")
        print()
        print("Remember to:")
        print("- Never commit .env files")
        print("- Always use environment variables for secrets")
        print("- Add this check to your CI pipeline")
        
        return 0


if __name__ == "__main__":
    sys.exit(main())
