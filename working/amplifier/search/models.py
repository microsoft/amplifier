"""Search result models"""

import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic import Field

sys.path.append(str(Path(__file__).parent.parent))


class SearchResult(BaseModel):
    """Memory search result with relevance score"""

    memory: Any = Field(..., description="The matched memory")  # Use Any to avoid validation issues
    score: float = Field(..., description="Relevance score (0-1)")
    match_type: str = Field(default="semantic", description="Type of match: semantic or keyword")
