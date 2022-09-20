from distutils.debug import DEBUG
from typing import List

import logging

from datetime import datetime
import pandas as pd
import berserk
from berserk.exceptions import ApiError 

from data_structures import GameLichessData, UserData

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class LichessComm:

    lichess_id = None
    API_TOKEN = None
    client = None

    user_data = None

    get_opening = True
    get_evals = True
    games_lst = []
    games_df = None

    def __init__(self, lichess_id) -> None:

        # Initialize token
        with open('conf/token.txt') as f:
            self.API_TOKEN = f.readline()[:-1]

        # Initialize lichess client
        self.lichess_id = lichess_id
        session_lichess = berserk.TokenSession(self.API_TOKEN)
        self.client = berserk.Client(session=session_lichess)
        logger.debug('Created client session to Lichess API')

    def fetch_user_rating(self):

        try:
            player_rating = self.client.users.get_rating_history(self.lichess_id)
            return player_rating
            
        except ApiError:
            logger.error('While get_rating_history from Lichess API')
            return None

    def fetch_user_data(self):
    
        try:
            user_data = self.client.users.get_public_data(self.lichess_id)
            self.user_data = UserData(**user_data)
            return self.user_data

        except ApiError:
            logger.error('While get_public_data from Lichess API')
            return None


    def fetch_user_games(self, since: datetime, until: datetime) -> int:
    

        since_millis = int(berserk.utils.to_millis(since))
        until_millis = int(berserk.utils.to_millis(until))

        try:
            logger.info(f'Retrieving games from lichess for user "{self.lichess_id}"')
            logger.info(f'Between {since} and {until}')
            
            games_gen = self.client.games.export_by_player(self.lichess_id,
                                                        rated=True,
                                                        since=since_millis,
                                                        until=until_millis,
                                                        evals=self.get_evals,
                                                        opening=self.get_opening)
            self.games_lst = [GameLichessData(**game) for game in games_gen]
            
            logger.info(f'{len(self.games_lst)} games retrieved')
            return len(self.games_lst)

        except Exception as e:
            logger.error(f'Exception "{e}" while fetching games from Lichess API')
            return None


    def show_games_info(self) -> None:

        if self.games_lst is None:
            print('No games have been fetched')
            return False
        else:
            print(f'Fetched {len(self.games_lst)} games')
            print(f'Last game from  : {self.games_lst[0].createdAt}')
            print(f'First game from : {self.games_lst[-1].createdAt}')

    def show_user_info(self) -> None:

        if self.user_data is None:
            print('No user data has been fetched')
            return False
        else:
            print(f'User {self.user_data.id} created at {self.user_data.createdAt}')
            print(f'Rating Classical : {self.user_data.perfs.classical.rating:4} ({self.user_data.perfs.classical.games:4} games)')
            print(f'Rating Rapid     : {self.user_data.perfs.rapid.rating:4} ({self.user_data.perfs.rapid.games:4} games)')
            print(f'Rating Blitz     : {self.user_data.perfs.blitz.rating:4} ({self.user_data.perfs.blitz.games:4} games)')
            print(f'Rating Bullet    : {self.user_data.perfs.bullet.rating:4} ({self.user_data.perfs.bullet.games:4} games)')

    def fill_df(self) -> pd.DataFrame:

        games_dict = dict(game_id=[],
                          user_id=[],
                          color=[],
                          opponent=[],
                          time_control=[],
                          creation_date=[],
                          opening=[],
                          result=[],
                          moves=[],
                          analysis=[],
                          evals=[],
                          mates=[],
                          judgment=[])

        for game in self.games_lst:

            games_dict['game_id'].append(game.id)

            games_dict['color'].append('white' if (game.players.white == self.lichess_id) else 'black')

            if game.players.white.user.id == self.lichess_id:
                games_dict['user_id'].append(game.players.white.user.id)
                games_dict['opponent'].append(game.players.black.user.id)
            else:
                games_dict['user_id'].append(game.players.black.user.id)
                games_dict['opponent'].append(game.players.white.user.id)

            games_dict['creation_date'].append(game.createdAt)

            if game.opening is not None:
                games_dict['opening'].append(game.opening.name)
            else:
                games_dict['opening'].append(None)

            if game.winner == 'draw':
                games_dict['result'].append('draw')
            elif game.winner == 'white' and game.players.white.user.id == self.lichess_id:
                games_dict['result'].append('win')
            elif game.winner == 'black' and game.players.black.user.id == self.lichess_id:
                games_dict['result'].append('win')
            else:
                games_dict['result'].append('loss')

            games_dict['time_control'].append(game.speed)

            games_dict['moves'].append(game.moves.split(' '))

            games_dict['analysis'].append(True if game.analysis != None else False)

            games_dict['evals'].append([move_anal.eval for move_anal in game.analysis]
                                       if game.analysis != None else None)

            games_dict['mates'].append([move_anal.mate for move_anal in game.analysis]
                                       if game.analysis != None else None)

            games_dict['judgment'].append([move_anal.judgment.name if move_anal.judgment != '' else '' for move_anal in game.analysis]
                                          if game.analysis != None else None)

        self.games_df = pd.DataFrame.from_dict(games_dict, orient='columns')
        #self.games_df.set_index('id', inplace=True)

        return self.games_df
