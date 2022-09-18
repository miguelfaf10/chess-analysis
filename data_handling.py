from pathlib import Path
import logging

from datetime import datetime, timedelta

import pandas

from sqlalchemy import create_engine, select, Column, String, DateTime, Boolean, SmallInteger, ForeignKey
from sqlalchemy.sql import text 
from sqlalchemy.orm import declarative_base, declarative_mixin, relationship, Session
from sqlalchemy.exc import NoResultFound, MultipleResultsFound
from sqlalchemy_utils import ScalarListType

from data_structures import UserData, GameData
from chessportals_comm_back import LichessComm

# Create configure module   module_logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

Base = declarative_base()

dtypes = {'game_id': String,
          'user_id': String,
          'color': String,
          'opponent': String,
          'time_control': String,
          'datetime': DateTime,
          'opening': String,
          'result': String,
          'moves': ScalarListType(),
          'analysis': Boolean,
          'evals': ScalarListType(float),
          'mates': ScalarListType(float),
          'judgment': ScalarListType()
          }


class Users(Base):
    __tablename__ = 'users'

    user_id = Column(String, primary_key=True)
    creation_date = Column(DateTime)
    rating_classical = Column(SmallInteger)
    rating_rapid = Column(SmallInteger)
    rating_blitz = Column(SmallInteger)
    rating_bullet = Column(SmallInteger)
    games_classical = Column(SmallInteger)
    games_rapid = Column(SmallInteger)
    games_blitz = Column(SmallInteger)
    games_bullet = Column(SmallInteger)
    last_update = Column(DateTime)

    def __repr__(self):
        return f'<Users(user_id={self.user_id}, last_update={self.last_update}, classical={self.rating_classical}/{self.games_classical})>'


class Games(Base):
    __tablename__ = 'games'

    game_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.user_id'))
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
    children = relationship('Users')

    def __repr__(self):
        return f'<Game(id={self.game_id}, date={self.creation_date},color={self.color}, result={self.result}, opening={self.opening})>'

class GamesTemp(Base):
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

    engine = None
        
    def __init__(self) -> None:

        db_file = 'app.sqlite' 
        db_connect_str = 'sqlite:///' + db_file

        if Path(db_file).exists():
            logger.info(f'DB file {db_file} exists')
        else:
            logger.info('DB file app.db doesn\'t exist')

        self.engine = create_engine(db_connect_str, echo=False, future=True)
        Base.metadata.create_all(self.engine)


    def _update_user_data(self, user:Users):

        lichess_comm = LichessComm(user.user_id)
        user_data = lichess_comm.fetch_user_data()

        user.creation_date = user_data.createdAt
        user.rating_classical = user_data.perfs.classical.rating
        user.rating_rapid = user_data.perfs.rapid.rating
        user.rating_blitz = user_data.perfs.blitz.rating
        user.rating_bullet = user_data.perfs.bullet.rating
        user.games_classical = user_data.perfs.classical.games
        user.games_rapid = user_data.perfs.rapid.games
        user.games_blitz = user_data.perfs.blitz.games
        user.games_bullet = user_data.perfs.bullet.games
        user.last_update = datetime.now()


    def _migrate_user_data(self, lichess_id:str) -> None:

        # Retrieve user data from lichess
        lichess_comm = LichessComm(lichess_id)
        user_data = lichess_comm.fetch_user_data()

        if user_data is None:
            logger.info(f'User data for {lichess_id} not retrieved')
        else:
            logger.info(f'Created {user_data.id}')

            # Create DB model with Lichess info
            user = Users(user_id=user_data.id,
                        creation_date=user_data.createdAt,
                        rating_classical=user_data.perfs.classical.rating,
                        rating_rapid=user_data.perfs.rapid.rating,
                        rating_blitz=user_data.perfs.blitz.rating,
                        rating_bullet=user_data.perfs.bullet.rating,
                        games_classical=user_data.perfs.classical.games,
                        games_rapid=user_data.perfs.rapid.games,
                        games_blitz=user_data.perfs.blitz.games,
                        games_bullet=user_data.perfs.bullet.games,
                        last_update=datetime.now()
                        )

            # Save new user data entry into db         
            session = Session(self.engine)
            session.add(user)
            session.commit()
            session.close()


    def _migrate_user_games(self, lichess_id:str, since:datetime, until:datetime) -> None:

        # Retrieve user data from lichess
        lichess_comm = LichessComm(lichess_id)
        n_games = lichess_comm.fetch_user_games(since, until)

        # Retrieve user games from lichess for request period
        # and add it to temporary GamesTemp table in db
        # this is so to avoid erasing game in Games table, and
        # conflicts due to repeated game keys.
        lichess_comm.fill_df()
        lichess_comm.games_df.to_sql('games_temp', 
                                    con=self.engine, 
                                    if_exists='replace',
                                    dtype=dtypes,
                                    index=False)

        # Sequentially add games from GamesTemp table to main Games table in db
        # Before adding a game verify that it doesn't exists already by checking
        # the game_id.
        session = Session(self.engine)
        
        old_gameid_lst = [aux[0] for aux in session.execute(select(Games.game_id)).all()]
        new_game_lst = [aux[0] for aux in session.execute(select(GamesTemp)).all()]
        
        session = Session(self.engine)
        try:
            old_gameid_lst = [aux[0] for aux in session.execute(select(Games.game_id)).all()]
            new_game_lst = [aux[0] for aux in session.execute(select(GamesTemp)).all()]

            if len(new_game_lst)>0:
                for game in new_game_lst:
                    if game.game_id not in old_gameid_lst:
                        logger.debug(f'Adding game {game.game_id} to Games table in DB')
                        game = Games(
                                game_id = game.game_id,
                                user_id = game.user_id,
                                color = game.color,
                                opponent = game.opponent,
                                time_control = game.time_control,
                                creation_date = game.creation_date,
                                opening = game.opening,
                                result = game.result,
                                moves = game.moves,
                                analysis = game.analysis,
                                evals = game.evals,
                                mates = game.mates,
                                judgment = game.judgment
                        )
                        print(game)
                        session.add(game)
                    else:
                        logger.debug(f'Ignoring game "{game.game_id}" which exists already in Games table in DB')
            session.commit()
        except:
            logger.error(f'Failed to copy new games from temp to permanent db table')
            session.rollback()
        finally:
            session.close()
             

    def retrieve_user_games(self, lichess_id):

        # Check if user exists in db
        session = Session(self.engine)
        try:
            user = session.execute(select(Users).filter_by(user_id=lichess_id)).one()[0]
        except NoResultFound:
            logger.debug(f'Lichess user {lichess_id} not found in DB. No games can be retrieved')
            return None
        
        # Retrieve existing games from db
        game_lst = session.execute(select(Games).filter_by(user_id=lichess_id)).all()
        logger.info(f'User {lichess_id} has {len(game_lst)} games in DB')

        if len(game_lst) == 0: 
            since = datetime.now() - timedelta(days=10) #user.creation_date  # user.creation_date
            until = datetime.now()

            # Fetch all user games since user was created
            self._migrate_user_games(lichess_id, since, until)

            # Read again game list from db and return it
            game_lst = session.execute(select(Games).filter_by(user_id=lichess_id)).all()
            logger.info(f'User {lichess_id} has {len(game_lst)} games in DB, after fetching from lichess')

            if len(game_lst)>0:
                return game_lst[0]
            else:
                return None

        elif len(game_lst) > 0:
            time_since_update = datetime.now() - game_lst[0][0].creation_date
            
            # Fetch latest games into db if this hasn't been done in a while
            if time_since_update > timedelta(minutes=5):
                print(game_lst[0][0])
                since = game_lst[0][0].creation_date + timedelta(hours=1)
                until = datetime.now()
                self._migrate_user_games(lichess_id, since, until)

                # Read again game list from db and return it
                game_lst = session.execute(select(Games).filter_by(user_id=lichess_id)).all()
                logger.info(f'User {lichess_id} has {len(game_lst)} games in DB, after fetching from lichess')
                return game_lst[0]

            else:
                # Complete game list has already been read and can be returned as is
                return game_lst[0]

        session.close()


    def retrieve_user_data(self, lichess_id):

        session = Session(self.engine)
        try:
            user = session.execute(select(Users).filter_by(user_id=lichess_id)).one()[0]
            logger.info(f'Found user {user}')

            # Update user entry in db if this hasn't been done in a while
            time_since_update = datetime.now() - user.last_update

            if time_since_update > timedelta(days=10):
                logger.info(f'Update user {user}')
                user = self._update_user_data(user)

        except NoResultFound:
            logger.info(f'User {user} not found in database. Migrating from Lichess')
            user = self._migrate_user_data(lichess_id)

        except MultipleResultsFound:
            logger.error(f'Multiple {user} in database')

        finally:
            session.close()
            return user

# TODO : use dictionary to insert games in DB, instead of df ??
