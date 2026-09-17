#!/usr/bin/env python3
"""
Root CLI dispatcher for AlertMe.
Delegates to src.cli.main().
"""
import sys
from pathlib import Path

# Ensure workspace root is in sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.cli import main

if __name__ == "__main__":
    main()
