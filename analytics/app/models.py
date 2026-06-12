from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AnalyzeRequest(BaseModel):
    unique_id: str
    audio_path: Optional[str] = None


class AnalyzeTextRequest(BaseModel):
    unique_id: str
    transcript: str
    language: Optional[str] = None


class CallAnalysis(BaseModel):
    category: str
    sentiment: str
    model_mentioned: Optional[str] = None
    resolved: bool
    summary: str
    confidence: float = 1.0


class CallRecord(BaseModel):
    id: int
    unique_id: str
    caller_number: str
    call_date: datetime
    language: Optional[str]
    duration: int
    transcript: Optional[str]
    ai_category: Optional[str]
    ai_sentiment: Optional[str]
    ai_model_mentioned: Optional[str]
    ai_resolved: Optional[bool]
    ai_summary: Optional[str]
    ai_analyzed_at: Optional[datetime]


class DailyReport(BaseModel):
    date: str
    total_calls: int
    analyzed_calls: int
    categories: dict
    sentiments: dict
    top_language: str
    avg_duration_seconds: float
    narrative: str


class WeeklyReport(BaseModel):
    week_start: str
    week_end: str
    total_calls: int
    analyzed_calls: int
    categories: dict
    sentiments: dict
    daily_trend: list
    narrative: str


class StatsResponse(BaseModel):
    total_calls: int
    analyzed_calls: int
    pending_calls: int
    categories: dict
    sentiments: dict
    languages: dict
    avg_duration_seconds: float
    last_7_days_trend: list
