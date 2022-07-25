from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

"""Pydantic Data Class to hold game data 
"""


class User(BaseModel):
    name: str
    id: str


class GlobalAnalysis(BaseModel):
    inaccuracy: int
    mistake: int
    blunder: int
    acpl: int


class Player(BaseModel):
    user: User
    rating: int
    ratingDiff: Optional[int] = 0
    analysis: Optional[GlobalAnalysis] = None


class Players(BaseModel):
    white: Player
    black: Player


class Opening(BaseModel):
    eco: str
    name: str
    ply: int


class Judgment(BaseModel):
    name: str
    comment: str


class MoveAnalysis(BaseModel):
    mate: Optional[int] = 'nan'
    eval: Optional[int] = 'nan'
    best: Optional[str]
    variation: Optional[str]
    judgment: Optional[Judgment] = ''


class Clock(BaseModel):
    initial: int
    increment: int
    totalTime: int


class GameData(BaseModel):
    id: str
    rated: bool
    variant: str
    speed: str
    createdAt: datetime
    lastMoveAt: datetime
    status: str
    players: Players
    winner: Optional[str] = 'draw'
    opening: Optional[Opening] = None
    moves: str
    analysis: Optional[List[MoveAnalysis]] = None
    clock: Clock


"""Pydantic Data Class to hold user data
"""


class Performance(BaseModel):
    games: int
    rating: int


class TimeControls(BaseModel):
    bullet: Performance
    blitz: Performance
    rapid: Performance
    classical: Performance


class UserData(BaseModel):
    id: str
    createdAt: datetime
    perfs: TimeControls
