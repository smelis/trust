from pydantic import BaseModel
from typing import List, Optional


class TrustIndicator(BaseModel):
    category: str
    towards: str
    why: str
    relation: Optional[str] = None


class CommentAnalysis(BaseModel):
    comment_text: str
    fullname: str
    trust_indicators: List[TrustIndicator]
    date_time: str
    author: str
    author_karma: int
    author_flair: Optional[str]
    # forward declaration of by name reference to the model as an escape from recursion
    comments: List["CommentAnalysis"]
    url: str


class PostAnalysis(BaseModel):
    post_title: str
    post_text: str
    fullname: str
    trust_indicators: List[TrustIndicator]
    date_time: str
    author: str
    author_karma: int
    author_flair: Optional[str]
    comments: List[CommentAnalysis]
    url: str
