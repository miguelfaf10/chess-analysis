"""Implements application DB

This modules implements the application database and respective interface 
functions.
"""

from pathlib import Path
import logging

from datetime import datetime, timedelta

import pandas

from sqlalchemy import create_engine, select, Column, String, DateTime, Boolean, Enum, Integer, SmallInteger, ForeignKey
from sqlalchemy.sql import text 
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.exc import NoResultFound, MultipleResultsFound
from sqlalchemy_utils import ScalarListType

from src.data_structures import User, UserLichess, Game
from src.chessportals_comm import LichessComm

# Create configure module   module_logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


SQLALCHEMY_DATABASE_URL = 'sqlite:///app.sqlite' 
Base = declarative_base()



class UserORM(Base):
    """Declares SQLAlchemy table for players
    
    Each player is a user of the ChessScope app and can have accounts
    in different chess platforms (i.e. lichess, chess.com)
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String)
    hashed_password = Column(String)
    lichess_id = Column(String)
    chesscom_id = Column(String)

    def __repr__(self):
         return f'<Player(user_id={self.id}, lichess_id={self.lichess_id})>'


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
    user_id = Column(String, ForeignKey('users.id'))
    user_side = Column(PlayerSide)
    opponent_id = Column(String(50))
    time_control = Column(String)
    creation_date = Column(DateTime)
    opening = Column(String)
    result = Column(GameResult)
    moves = Column(ScalarListType())
    analysis = Column(Boolean)
    evals = Column(ScalarListType(float))
    mates = Column(ScalarListType(float))
    judgment_name = Column(ScalarListType())
    judgment_comment = Column(ScalarListType())

    def __repr__(self):
        return f'<Game(id={self.game_id}, date={self.creation_date},side={self.user_side}, result={self.result}, opening={self.opening})>'

class GamesTemp(Base):   
    """Declares SQLAlchemy table for temporary players games
    
    This DB table is used temporarily when fetching games from external platforms 
    """
    __tablename__ = 'games_temp'

    game_id = Column(String, primary_key=True)
    user_id = Column(String)
    color = Column(String)
    opponent = Column(String)
    time_control = Column(String)
    creation_date = Column(DateTime)
    opening = Column(String)
    result = Column(String)
    moves = Column(ScalarListType())
    analysis = Column(Boolean)
    evals = Column(ScalarListType(float))
    mates = Column(ScalarListType(float))
    judgment = Column(String)

# class GamesTemp(Base):
#     __tablename__ = 'games_temp'

#     game_id = Column(String, primary_key=True)

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

        db_file = SQLALCHEMY_DATABASE_URL.split('/')[-1] 
    
        if Path(db_file).exists():
            logger.info(f'DB file {db_file} exists')
        else:
            logger.info('DB file app.db doesn\'t exist')

        self.engine = create_engine(SQLALCHEMY_DATABASE_URL, 
                                    echo=False, 
                                    future=True, 
                                    connect_args={"check_same_thread": False})
        
        self.Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        Base.metadata.create_all(self.engine)

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
        user = session.query(UserORM).filter(UserORM.id == user_id).first()
        
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
        
        existing_user = self.get_user_by_email(user.email)
        if not existing_user:
            # Create new user entry
            fake_hashed_password = user.password + "notreallyhashed"
            new_user = UserORM(email=user.email,
                            lichess_id=user.lichess_id, 
                            chesscom_id=user.chesscom_id, 
                            hashed_password=fake_hashed_password)
            session = self.Session()
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            return new_user
        else:
            logger.info(f'User with same email already exists: {existing_user.email}')
            return None

    def create_user_lichess(self, id: str, user_lichess: UserLichess) -> None:
        """Create a new UserLichessORM instance in the database
        """
        session = self.Session()
        # Find the UserORM instance that corresponds to the user_lichess.user_id
        user_orm, user_lichess_orm, user_chesscom_orm = self.get_user(id)
        print(user_orm, user_lichess_orm, user_chesscom_orm)
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
        query = session.query(GamesORM).filter(GamesORM.user_id == user_orm.id).all()
        
        return query
    
    def create_games(self, games: Game):

        session = self.Session()           
        # Add the UserLichessORM instance to the session
        for game in games:
            session.add(GamesORM(**game.dict()))
        session.commit()
 
    
    # @staticmethod
    # def convert_userdata(user:UserLichess) -> UserLichess:

    #     if user == None:
    #         return None
    #     else:
    #         user_data = UserLichess(
    #             id = user.user_id,
    #             createdAt = user.creation_date,
    #             perfs=TimeControls(
    #                 bullet=Performance(rating=user.rating_bullet,games=user.games_bullet),
    #                 blitz=Performance(rating=user.rating_blitz,games=user.games_blitz),
    #                 rapid=Performance(rating=user.rating_rapid,games=user.games_rapid),
    #                 classical=Performance(rating=user.rating_classical,games=user.games_classical),
    #             )
    #     )
    #     return user_data

    # @staticmethod
    # def convert_gamedata(game:Game) -> GameData:

    #     if game == None:
    #         return None
    #     else:
    #         game_data = GameData(
    #             game_id = game.game_id,
    #             user_id = game.user_id,
    #             color = game.color,
    #             opponent = game.opponent,
    #             time_control = game.time_control,
    #             creation_date = game.creation_date,
    #             opening = game.opening,
    #             result = game.result,
    #             moves = game.moves,
    #             analysis = game.analysis,
    #             evals = game.evals if game.evals!= None else [],
    #             mates = game.mates if game.mates!= None else [],
    #             judgment = game.judgment if game.judgment!= None else ''
    #     )
    #     return game_data

    # def migrate_user_data(self, lichess_id:str) -> UserLichess:

    #     # Retrieve user data from lichess
    #     lichess_comm = LichessComm(lichess_id)
    #     user_data = lichess_comm.fetch_user_data()

    #     if user_data is None:
    #         logger.info(f'User {lichess_id} not found in Lichess')
    #         return None
    #     else:
    #         logger.info(f'Created {user_data.id} in DB')

    #         # Create DB model with Lichess info
    #         user = UserLichess(user_id=user_data.id,
    #                     creation_date=user_data.createdAt,
    #                     rating_classical=user_data.perfs.classical.rating,
    #                     rating_rapid=user_data.perfs.rapid.rating,
    #                     rating_blitz=user_data.perfs.blitz.rating,
    #                     rating_bullet=user_data.perfs.bullet.rating,
    #                     games_classical=user_data.perfs.classical.games,
    #                     games_rapid=user_data.perfs.rapid.games,
    #                     games_blitz=user_data.perfs.blitz.games,
    #                     games_bullet=user_data.perfs.bullet.games,
    #                     last_update=datetime.now()
    #                     )

    #         # Save new user data entry into db         
    #         session = Session(self.engine)
    #         session.add(user)
    #         session.commit()
    #         session.close()

    #         return user

    # def migrate_user_games(self, lichess_id:str, since:datetime, until:datetime) -> None:

    #     # Retrieve user data from lichess
    #     lichess_comm = LichessComm(lichess_id)
    #     n_games = lichess_comm.fetch_user_games(since, until)

    #     # Retrieve user games from lichess for request period
    #     # and add it to temporary GamesTemp table in db
    #     # this is so to avoid erasing game in Games table, and
    #     # conflicts due to repeated game keys.
    #     lichess_comm.fill_df()
    #     lichess_comm.games_df.to_sql('games_temp', 
    #                                 con=self.engine, 
    #                                 if_exists='replace',
    #                                 dtype=dtypes,
    #                                 index=False)

    #     # Sequentially add games from GamesTemp table to main Games table in db
    #     # Before adding a game verify that it doesn't exists already by checking
    #     # the game_id.
    #     session = self.Session(self.engine)
    #     try:
    #         old_gameid_lst = [aux[0] for aux in session.execute(select(Games.game_id)).all()]
    #         new_game_lst = [aux[0] for aux in session.execute(select(GamesTemp)).all()]

    #         if len(new_game_lst)>0:
 
    #             for game_temp in new_game_lst:
    #                 if game_temp.game_id not in old_gameid_lst:
    #                     logger.debug(f'Adding game {game_temp.game_id} to Games table in DB')
    #                     game = Games(
    #                             game_id = game_temp.game_id,
    #                             user_id = game_temp.user_id,
    #                             color = game_temp.color,
    #                             opponent = game_temp.opponent,
    #                             time_control = game_temp.time_control,
    #                             creation_date = game_temp.creation_date,
    #                             opening = game_temp.opening,
    #                             result = game_temp.result,
    #                             moves = game_temp.moves,
    #                             analysis = game_temp.analysis,
    #                             evals = game_temp.evals,
    #                             mates = game_temp.mates,
    #                             judgment = game_temp.judgment
    #                     )
    #                     session.add(game)
    #                 else:
    #                     logger.debug(f'Ignoring game "{game_temp.game_id}" which exists already in Games table in DB')
    #         session.commit()
    #     except:
    #         logger.error(f'Failed to copy new games from temp to permanent db table')
    #         session.rollback()
    #     finally:
    #         session.close()


    # def retrieve_player_data(self, player_id) -> UserLichess:

    #     session = Session(self.engine)
    #     try:
    #         player = session.execute(select(Player).filter_by(player_id=player_id)).one()[0]
    #         logger.info(f'Found in DB: {player}')

    #     except NoResultFound:
    #         logger.info(f'Player {player_id} not found in DB.')
    #         return None

    #     finally:
    #         user_data = self.convert_userdata(player)
    #         #session.close()
    #         return user_data  


    # def retrieve_user_games(self, lichess_id):

    #     # Check if user exists in db
    #     session = self.Session(self.engine)
    #     try:
    #         user = session.execute(select(Users).filter_by(user_id=lichess_id)).one()[0]
    #     except NoResultFound:
    #         logger.debug(f'Lichess user {lichess_id} not found in DB. No games can be retrieved')
    #         return None
        
    #     # Retrieve existing games from db
    #     game_lst = session.execute(select(Games).filter_by(user_id=lichess_id)).all()
    #     logger.info(f'User {lichess_id} has {len(game_lst)} games in DB')

    #     if len(game_lst) == 0: 
    #         session.close()
    #         return None
    #     else:
    #         game_data_lst = [self.convert_gamedata(game[0]) for game in game_lst]
    #         session.close()        
    #         return game_data_lst
    
    