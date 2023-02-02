"""Pydantic datastructures

This modules defines the datastructures used to interface with chessportals
APIs, as well as structures used internally by the application

GameData
|-- game_id: str
|-- user_id: str
|-- user_side: str
|-- opponent_id: str
|-- time_control: str
|-- creation_date: datetime
|-- opening: str
|-- result: str
|-- moves: List[str]
|-- analysis: bool
|-- evals: List[float]
|-- mates: List[float]
|-- judgment: str

UserLichessData
|-- id: str
|-- createdAt: datetime
|-- bullet_games: int
|-- bullet_rating: int
|-- blitz_games: int
|-- blitz_rating: int
|-- rapid_games: int
|-- rapid_rating: int
|-- classical_games: int
|-- classical_rating: int

"""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class GameData(BaseModel):
    """Pydantic class representing data for a single game on Lichess.

    Attributes:
        game_id (str): Unique identifier of the game.
        user_id (str): Unique identifier of the user.
        user_side (str): Side the user played as ("white" or "black").
        opponent_id (str): Unique identifier of the opponent.
        time_control (str): Time control of the game as ("bullet", "blitz", "rapid", "classical").
        creation_date (datetime): The date and time the game was created.
        opening (str): The opening played in the game.
        result (str): Result of the game ("win", "loss", "draw").
        moves (List[str]): List of moves in the game, represented as strings in the format "e2".
        evals (List[float]): List of evaluation scores for each move, represented as floats (nan when not available).
        mates (List[float]): List of mate in #moves, represented as floats (nan when not available).
        judgment_name (List[str]): List of judgments for some moves, represented as strings ("blunder", "mistake", ..., or "" when not available).
        judgment_comment (List[str]): List of comments for some moves, represented as strings (e.g. "Lost forced checkmate sequence. Bxh6" or "" when not available).
    """
    game_id: str
    user_id: str
    user_side: str
    opponent_id: str
    time_control: str
    creation_date: datetime
    opening: str
    result: str
    moves: List[str]
    evals: List[float]
    mates: List[float]
    judgment_name: List[str]
    judgment_comment: List[str]

class UserLichessData(BaseModel):
    """Pydantic class representing user data on Lichess.

    Attributes:
        id (str): Unique identifier of the user.
        creation_date (datetime): The date and time the user account was created.
        bullet_games (int): Number of bullet games played by the user.
        bullet_rating (int): The user's bullet rating.
        blitz_games (int): Number of blitz games played by the user.
        blitz_rating (int): The user's blitz rating.
        rapid_games (int): Number of rapid games played by the user.
        rapid_rating (int): The user's rapid rating.
        classical_games (int): Number of classical games played by the user.
        classical_rating (int): The user's classical rating.
    """
    id: str
    creation_date: datetime
    bullet_games: int
    bullet_rating: int
    blitz_games: int
    blitz_rating: int
    rapid_games: int
    rapid_rating: int
    classical_games: int
    classical_rating: int
