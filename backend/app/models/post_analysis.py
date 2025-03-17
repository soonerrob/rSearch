"""Post analysis model."""

import json
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlmodel import Field, Relationship, SQLModel


class PostAnalysis(SQLModel, table=True):
    """Post analysis model."""
    
    __tablename__ = "postanalysis"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: int = Field(sa_column=Column(Integer, ForeignKey("redditpost.id", ondelete="CASCADE")))
    matching_themes: str = Field(sa_column=Column(String, nullable=False, server_default=''))
    theme_scores: str = Field(sa_column=Column(String, nullable=False, server_default='{}'))
    keywords: str = Field(sa_column=Column(String, nullable=False, server_default=''))
    analyzed_at: datetime = Field(sa_column=Column(DateTime, nullable=False))
    
    # New array/jsonb columns
    matching_themes_array: Optional[List[str]] = Field(sa_column=Column(ARRAY(String), nullable=True))
    keywords_array: Optional[List[str]] = Field(sa_column=Column(ARRAY(String), nullable=True))
    theme_scores_jsonb: Optional[dict] = Field(sa_column=Column(JSONB, nullable=True))
    
    def get_matching_themes(self) -> List[str]:
        """Get matching themes in array format."""
        if self.matching_themes_array:
            return self.matching_themes_array
        if self.matching_themes:
            return [theme.strip() for theme in self.matching_themes.split(',') if theme.strip()]
        return []
    
    def get_keywords(self) -> List[str]:
        """Get keywords in array format."""
        if self.keywords_array:
            return self.keywords_array
        if self.keywords:
            return [kw.strip() for kw in self.keywords.split(',') if kw.strip()]
        return []
    
    def get_theme_scores(self) -> dict:
        """Get theme scores in dict format."""
        if self.theme_scores_jsonb:
            return self.theme_scores_jsonb
        if self.theme_scores:
            try:
                return json.loads(self.theme_scores)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}
    
    def to_dict(self) -> Dict:
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'post_id': self.post_id,
            'matching_themes': self.get_matching_themes(),
            'keywords': self.get_keywords(),
            'theme_scores': self.get_theme_scores(),
            'analyzed_at': self.analyzed_at
        }

    def set_matching_themes(self, themes: List[str]) -> None:
        """Set matching themes in both string and array format."""
        self.matching_themes = ','.join(themes) if themes else ''
        self.matching_themes_array = themes

    def set_keywords(self, keywords: List[str]) -> None:
        """Set keywords in both string and array format."""
        self.keywords = ','.join(keywords) if keywords else ''
        self.keywords_array = keywords

    def set_theme_scores(self, scores: Dict) -> None:
        """Set theme scores in both string and JSONB format."""
        self.theme_scores = json.dumps(scores) if scores else '{}'
        self.theme_scores_jsonb = scores 