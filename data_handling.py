import logging

from datetime import datetime, timedelta

import pandas

from sqlalchemy import create_engine, select, MetaData, Table, Column, Integer, String, DateTime, Boolean, SmallInteger, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, Session
from sqlalchemy.exc import NoResultFound, MultipleResultsFound
from sqlalchemy_utils import ScalarListType

from data_structures import UserData, GameData
from chessportals_communication import LichessComm

# Create configure module   module_logger

logger = logging.getLogger(__name__)

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
        return f'<User(name={self.user_id}, last_update={self.last_update}, classical={self.rating_classical}/{self.games_classical})>'


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


class Database:

    engine = None

    def __init__(self) -> None:

        db_connect_str = 'sqlite:///:memory:'
        self.engine = create_engine(db_connect_str, echo=False, future=True)
        logger.info(f'Created \'{db_connect_str}\'')

        Base.metadata.create_all(self.engine)

    def process_user_data(self, lichess_id) -> UserData:

        session = Session(self.engine)

        try:
            user = session.execute(select(Users).filter_by(user_id=lichess_id)).one_or_none()
        except MultipleResultsFound:
            logger.error('Multiple {user} in database')

        if user != None:

            user = user[0]
            logger.info(f'Found {user}')

            # Update user entry in db if this hasn't been done in a while
            time_since_update = datetime.now() - user.last_update

            if time_since_update > timedelta(seconds=10):
                logger.info(f'Update {user}')
                lichess_comm = LichessComm(lichess_id)
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

                session.commit()

        else:

            logger.info(f'Not found {lichess_id}')

            lichess_comm = LichessComm(lichess_id)
            user_data = lichess_comm.fetch_user_data()

            logger.info(f'Created {user_data}')
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

            session.add(user)
            session.commit()

        session.close()

    def process_user_games(self, lichess_id):

        # First make sure user data is in DB
        self.process_user_data(lichess_id)

        session = Session(self.engine)
        user = session.execute(select(Users).filter_by(user_id=lichess_id)).one()[0]

        game_lst = session.execute(select(Games).filter_by(user_id=lichess_id)).all()
        logger.info(f'{len(game_lst)} games in DB')

        if len(game_lst) > 0:
            since = game_lst[0][0].creation_date
            until = datetime.now()
        else:
            since = datetime.now() - timedelta(days=10)  # user.creation_date
            until = datetime.now()

        lichess_comm = LichessComm(lichess_id)

        #since = datetime.now()-timedelta(days=100)
        lichess_comm.fetch_user_games(since, until)
        lichess_comm.fill_df()
        lichess_comm.games_df.to_sql('games',
                                     self.engine,
                                     if_exists='replace',
                                     dtype=dtypes,
                                     index=False,
                                     index_label='id')

        session.commit()
        session.close()


"""         if user != None:    
        #try:
        #    user = session.execute(select(Games).filter_by(user_id=lichess_id)).scalar_one()
        #    logger.info(f'Found \'{user}\'')

        #    last_update = datetime.now() - user.last_update

        lichess_comm = LichessComm(lichess_id)

        last_Xdays = datetime.now()-timedelta(days=20)
        since = last_Xdays
        until = datetime.now()

        lichess_comm.fetch_user_games(since,until)
        lichess_comm.fill_df()  
    
        lichess_comm.games_df.to_sql('games', 
                                    self.engine, 
                                    if_exists='append',
                                    dtype=dtypes,
                                    index=False,
                                    index_label='id')
 """
# TODO : use dictionary to insert games in DB, instead of df ??
