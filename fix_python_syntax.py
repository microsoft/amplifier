#!/usr/bin/env python3
"""Fix Python 3.10+ syntax to be compatible with Python 3.9"""

import re
from pathlib import Path

def fix_file(file_path):
    """Fix Python 3.10+ syntax in a file."""
    with open(file_path, 'r') as f:
        content = f.read()

    original = content

    # Add imports if needed
    if 'list[' in content or 'tuple[' in content or 'dict[' in content:
        if 'from typing import' in content:
            # Add to existing import
            if 'List' not in content:
                content = re.sub(r'from typing import (.+)',
                                lambda m: f"from typing import {m.group(1)}, List, Dict, Tuple, Optional",
                                content, count=1)
        else:
            # Add new import
            content = "from typing import List, Dict, Tuple, Optional\n" + content

    # Fix type hints
    content = re.sub(r'\blist\[', 'List[', content)
    content = re.sub(r'\bdict\[', 'Dict[', content)
    content = re.sub(r'\btuple\[', 'Tuple[', content)
    content = re.sub(r'(\w+)\s*\|\s*None', r'Optional[\1]', content)

    if content != original:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Fixed: {file_path}")
        return True
    return False

# Fix all Python files in discovery_processor
discovery_dir = Path('/Users/alexlopez/Sites/OCTO/amplified-design/amplifier/ai_working/discovery_processor')
fixed_count = 0

for py_file in discovery_dir.rglob('*.py'):
    if fix_file(py_file):
        fixed_count += 1

print(f"Fixed {fixed_count} files")