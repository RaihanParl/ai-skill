#!/usr/bin/env python3
from pathlib import Path
import runpy

repo_script = Path('/Users/mraihanparlaungan/ai-skill/hermes/scripts/sync_memory_to_ai_skill.py')
runpy.run_path(str(repo_script), run_name='__main__')
