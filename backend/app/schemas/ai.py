"""Schemas for AI-related functionality."""

from typing import List, Optional

from pydantic import BaseModel


class Source(BaseModel):
    """A source used in an AI response."""
    title: str
    score: int
    url: Optional[str] = None
    relevance: Optional[float] = None


class AIResponse(BaseModel):
    """Response from AI analysis."""
    answer: str
    sources: List[Source]
    confidence: Optional[float] = None
    metadata: Optional[dict] = None 