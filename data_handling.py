from pathlib import Path
import logging

from datetime import datetime, timedelta

import pandas

from sqlalchemy import create_engine, select, Column, String, DateTime, Boolean, SmallInteger, ForeignKey
from sqlalchemy.sql import text 
from sqlalchemy.orm import declarative_base, declarative_mixin, relationship, Session
from sqlalchemy.exc import NoResultFound, MultipleResultsFound
from sqlalchemy_utils import ScalarListType

from data_structures import UserData, TimeControls, Performance, GameLichessData, GameData
from chessportals_comm import LichessComm

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

    @staticmethod
    def convert_userdata_type(user:Users) -> UserData:

        if user == None:
            return None
        else:
            user_data = UserData(
                id = user.user_id,
                createdAt = user.creation_date,
                perfs=TimeControls(
                    bullet=Performance(rating=user.rating_bullet,games=user.games_bullet),
                    blitz=Performance(rating=user.rating_blitz,games=user.games_blitz),
                    rapid=Performance(rating=user.rating_rapid,games=user.games_rapid),
                    classical=Performance(rating=user.rating_classical,games=user.games_classical),
                )
        )
        return user_data

    @staticmethod
    def convert_gamedata_type(game:Games) -> GameData:

        if game == None:
            return None
        else:
            game_data = GameData(
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
                evals = game.evals if game.evals!= None else [],
                mates = game.mates if game.mates!= None else [],
                judgment = game.judgment if game.judgment!= None else ''
        )
        return game_data

    def _migrate_user_data(self, lichess_id:str) -> Users:

        # Retrieve user data from lichess
        lichess_comm = LichessComm(lichess_id)
        user_data = lichess_comm.fetch_user_data()

        if user_data is None:
            logger.info(f'User {lichess_id} not found in Lichess')
            return None
        else:
            logger.info(f'Created {user_data.id} in DB')

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

            return user

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
                        session.add(game)
                    else:
                        logger.debug(f'Ignoring game "{game.game_id}" which exists already in Games table in DB')
            session.commit()
        except:
            logger.error(f'Failed to copy new games from temp to permanent db table')
            session.rollback()
        finally:
            session.close()


    def retrieve_user_data(self, lichess_id) -> Users:

        session = Session(self.engine)
        try:
            user = session.execute(select(Users).filter_by(user_id=lichess_id)).one()[0]
            logger.info(f'Found user {lichess_id} in DB')

             # Update user entry in db if this hasn't been done in a while
            time_since_update = datetime.now() - user.last_update

            if time_since_update > timedelta(days=10):
                logger.info(f'Update user {lichess_id}')
                self._migrate_user_data(lichess_id)
                user = session.execute(select(Users).filter_by(user_id=lichess_id)).one()[0]

        except NoResultFound:
            logger.info(f'User {lichess_id} not found in database. Migrating from Lichess')
            self._migrate_user_data(lichess_id)
            user = session.execute(select(Users).filter_by(user_id=lichess_id)).one()[0]
            if user != None:
                logger.info(f'Found user {lichess_id} in DB')
            else:
                return None

        except:
            logger.error(f'While retrieving user {lichess_id} from DB')
            user = None

        finally:
            user_data = self.convert_userdata_type(user)
            #session.close()
            return user_data  

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
            # Fetch all user games since user was created
            since = datetime.now() - timedelta(days=10) #user.creation_date  # user.creation_date
            until = datetime.now()

        elif len(game_lst) > 0:
            time_since_update = datetime.now() - game_lst[0][0].creation_date
            
            # Fetch latest games into db if this hasn't been done in a while
            if time_since_update > timedelta(minutes=5):
                since = game_lst[0][0].creation_date + timedelta(hours=1)
                until = datetime.now()
            
        # Actually migrate games from Lichess into DB
        self._migrate_user_games(lichess_id, since, until)

        # Read again game list from db and return it
        game_lst = session.execute(select(Games).filter_by(user_id=lichess_id)).all()
        
        logger.info(f'User {lichess_id} has {len(game_lst)} games in DB, after fetching from lichess')
        if len(game_lst) == 0: 
            session.close()
            return None
        else:
            print(game_lst)
            game_data_lst = [self.convert_gamedata_type(game[0]) for game in game_lst]
            session.close()        
            return game_data_lst
    
        


# TODO : use dictionary to insert games in DB, instead of df ??
