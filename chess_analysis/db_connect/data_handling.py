"""Implements application DB

This modules implements the application database and respective interface 
functions.
"""

from pathlib import Path
import logging
import yaml

from datetime import datetime, timedelta

import pandas

from sqlalchemy import create_engine, select, Column, String, DateTime, Boolean, Enum, Integer, SmallInteger, ForeignKey
from sqlalchemy.sql import text 
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, close_all_sessions
from sqlalchemy.exc import NoResultFound, MultipleResultsFound, IntegrityError
from sqlalchemy_utils import ScalarListType

from chess_analysis import CONFIG_FILE_PATH
from ..models.data_structures import User, UserLichess, Game
from ..api_clients.chessportals_comm import LichessComm


# Create configure module   module_logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


Base = declarative_base()

class UserORM(Base):
    """Declares SQLAlchemy table for players
    
    Each player is a user of the ChessScope app and can have accounts
    in different chess platforms (i.e. lichess, chess.com)
    """
    __tablename__ = 'users'

    user_id = Column(String, primary_key=True)
    email = Column(String)
    hashed_password = Column(String)
    lichess_id = Column(String)
    chesscom_id = Column(String)

    def __repr__(self):
         return f'<Player(user_id={self.user_id}, pass={self.hashed_password}, lichess_id={self.lichess_id})>'


class UserChesscomORM(Base):
    """Declares SQLAlchemy table for Chess.com users info
    """
  
    __tablename__ = 'users-chesscom'

    chesscom_id = Column(String, ForeignKey('users.chesscom_id'), primary_key=True)
    creation_date = Column(DateTime)
    classical_rating = Column(SmallInteger)
    classical_games = Column(SmallInteger)
    rapid_rating = Column(SmallInteger)
    rapid_games = Column(SmallInteger)
    blitz_rating = Column(SmallInteger)
    blitz_games = Column(SmallInteger)
    bullet_rating = Column(SmallInteger)
    bullet_games = Column(SmallInteger)
    
    last_update = Column(DateTime)

    def __repr__(self):
        return f'<Users(user_id={self.user_id}, last_update={self.last_update}, classical={self.rating_classical}/{self.games_classical})>'


class UserLichessORM(Base):
    """Declares SQLAlchemy table for **Lichess users info***
    """
  
    __tablename__ = 'users-lichess'

    lichess_id = Column(String, ForeignKey('users.lichess_id'), primary_key=True)
    creation_date = Column(DateTime)
    rating_classical = Column(SmallInteger)
    rating_rapid = Column(SmallInteger)
    rating_blitz = Column(SmallInteger)
    rating_bullet = Column(SmallInteger)
    games_classical = Column(SmallInteger)
    games_rapid = Column(SmallInteger)
    games_blitz = Column(SmallInteger)
    games_bullet = Column(SmallInteger)

    def __repr__(self):
        return f'<Users(user_id={self.lichess_id}, classical={self.rating_classical}/{self.games_classical})>'

class PlayerSide(Enum):
    white = 'white'
    black = 'black'

class GameResult(Enum):
    win = 'win'
    loss = 'loss'
    draw = 'draw'

class GamesORM(Base):
    """Declares SQLAlchemy table for ***players games***
    """

    __tablename__ = 'games'

    game_id = Column(String, primary_key=True)
    platform = Column(String(10))
    user_id = Column(String, ForeignKey('users.user_id'))
    user_side = Column(String)
    opponent_id = Column(String(50))
    time_control = Column(String)
    creation_date = Column(DateTime)
    opening = Column(String)
    result = Column(String)
    moves = Column(ScalarListType())
    analysis = Column(Boolean)
    evals = Column(ScalarListType(float))
    mates = Column(ScalarListType(float))
    judgment_name = Column(ScalarListType())
    judgment_comment = Column(ScalarListType())

    def __repr__(self):
        return f'<Game(id={self.game_id}, date={self.creation_date},side={self.user_side}, result={self.result}, opening={self.opening})>'


class Database:
    """Declares Database class
    
    This classes handles everything related to the application database.
    Provides interfaces for returning current information in the database. 
    Also implements methods for populating database with information from chess 
    platforms with communication functions implemented in module :py:mod:chessportals_comm
    """
    engine = None
    Session = None
        
    def __init__(self) -> None:
        """Constructor.
        
        Check if the database file exists. If not, create it.
        """
        with open(CONFIG_FILE_PATH) as f:
            config = yaml.safe_load(f) 
    
        db_url = config['database']['url']
        db_file = db_url.split('/')[-1] 
    
        if Path(db_file).exists():
            logger.info(f'DB file {db_file} exists')
        else:
            logger.info('DB file app.db doesn\'t exist')

        self.engine = create_engine(db_url, 
                                    echo=False, 
                                    future=True, 
                                    connect_args={"check_same_thread": False})
        
        self.Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        Base.metadata.create_all(self.engine)

    def close_conn(self):
        close_all_sessions()

    def get_session(self):
        """Return a session."""
        session = self.Session()
        try:
            yield session
        finally:
            session.close()

    def get_user(self, user_id: str):
        """Returns a user given the user_id"""
        session = self.Session()
        user = session.query(UserORM).filter(UserORM.user_id == user_id).first()
        
        if user and user.lichess_id:
            user_lichess = session.query(UserLichessORM).filter(UserLichessORM.lichess_id == user.lichess_id).first()
        else:
            user_lichess = None
        
        if user and user.chesscom_id:
            user_chesscom = session.query(UserChesscomORM).filter(UserChesscomORM.chesscom_id == user.lichess_id).first()
        else:
            user_chesscom = None
        
        return user, user_lichess, user_chesscom

    def get_user_by_email(self, email: str):
        session = self.Session()
        return session.query(UserORM).filter(UserORM.email == email).first()

    def get_users(self, skip: int = 0, limit: int = 100):
        session = self.Session()
        return session.query(UserORM).offset(skip).limit(limit).all()

    def create_user(self, user: User):
        session = self.Session()
        
        existing_user,_,_ = self.get_user(user.user_id)
        if not existing_user:
            # Create new user entry
            fake_hashed_password = user.password
            new_user = UserORM(user_id=user.user_id,
                                email=user.email,
                                lichess_id=user.lichess_id, 
                                chesscom_id=user.chesscom_id, 
                                hashed_password=fake_hashed_password)
            session = self.Session()
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            return new_user
        else:
            logger.info(f'Already existis in database user_id {existing_user.user_id}')
            return None
        
    def authenticate_user(self, username, password):
        session = self.Session()
        hashed_password = hash(password)

        user = session.query(User).filter_by(user_id=username).first()        
        
        return user and user.hashed_password == hashed_password

    def create_user_lichess(self, id: str, user_lichess: UserLichess) -> None:
        """Create a new UserLichessORM instance in the database
        """
        session = self.Session()
        # Find the UserORM instance that corresponds to the user_lichess.user_id
        user_orm, user_lichess_orm, user_chesscom_orm = self.get_user(id)
        if user_orm is None:
            logger.info(f"User with id '{id}' does not exist in the 'users' table.")
            return None
        elif user_lichess_orm:
            logger.info(f'User with email {user_orm.email} already registered lichess account {user_orm.lichess_id}')
            return None
        else:
            if not user_lichess_orm:
                # Create a new UserLichessORM instance
                user_orm.lichess_id = user_lichess.lichess_id
                # Add the UserLichessORM instance to the session
                session.add(UserLichessORM(**user_lichess.dict()))
                session.commit()
              
                return user_lichess
    
    def get_games(self, user_id: str):
        
        user_orm, user_lichess_orm, user_chesscom_orm = self.get_user(user_id)
    
        session = self.Session()
        if user_orm:
            query = session.query(GamesORM).filter(GamesORM.user_id == user_orm.user_id).all()
            return query
        else:
            return None
    
    def create_games(self, games: Game):

        session = self.Session()           
        # Add the UserLichessORM instance to the session
        k = 0
        for game in games:
            try:
                session.add(GamesORM(**game.dict()))
                session.flush()
                k += 1
            except IntegrityError:
                session.rollback()
                logger.debug(f'Not possible insert game with id: {game.game_id}')
        
        session.commit()
        logger.info(f'Number of games created in DB: {k}/{len(games)}')
