from distutils.debug import DEBUG
from typing import List

import logging
from pprint import pprint

from datetime import datetime
import pandas as pd
import berserk
from berserk.exceptions import ApiError 

from src.data_structures import GameData, UserLichessData

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class LichessComm:
    """Class that wraps around the Lichess API provided by berserk to retrieve information.

    Attributes:
        lichess_id (str): The ID of the lichess user.
        API_TOKEN (str): The token to access the Lichess API.
        client (berserk.Client): The client used to connect to the Lichess API.
        user_data (UserLichessData): The data structure that stores the information of the lichess user.
        get_opening (bool): If true, include opening information for games.
        get_evals (bool): If true, include evaluation information for games.
        games (List[GameData]): List of game information for the user.
        games_df (pd.DataFrame): DataFrame of game information for the user.

    """
    
    lichess_id = None
    API_TOKEN = None
    client = None

    user_data = None

    get_opening = True
    get_evals = True
    games = []
    games_df = None

    def __init__(self, lichess_id) -> None:
        """Initialize the LichessComm object.

        Args:
            lichess_id (str): The ID of the lichess user.
        
        """
        # Initialize token
        with open('conf/token.txt') as f:
            self.API_TOKEN = f.readline()[:-1]

        # Initialize lichess client
        self.lichess_id = lichess_id
        session_lichess = berserk.TokenSession(self.API_TOKEN)
        self.client = berserk.Client(session=session_lichess)
        logger.debug('Created client session to Lichess API')

    def fetch_user_rating(self):
        """Fetch the rating history of the lichess user.

        Returns:
            dict: The rating history of the lichess user, or None if there is an error.
        
        """
        try:
            player_rating = self.client.users.get_rating_history(self.lichess_id)
            return player_rating
            
        except ApiError:
            logger.error('While get_rating_history from Lichess API')
            return None

    def fetch_user_data(self):
        """Fetch and store public data of a lichess user.
        This function uses the Lichess API to retrieve public data of the lichess user, specified by the lichess_id attribute of the class instance. The data is stored in the user_data attribute of the class instance as an instance of the UserLichessData class.
        
        Returns: None
        
        Raises: Exception: If there's an error in fetching the user data from the Lichess API. The error message is logged with logger.error.
        """

        try:
            user_data = self.client.users.get_public_data(self.lichess_id)
            
            self.user_data = UserLichessData(
                                id = user_data['id'],
                                creation_date = user_data['createdAt'],
                                bullet_games = user_data['perfs']['bullet']['games'],
                                bullet_rating = user_data['perfs']['bullet']['rating'],
                                blitz_games = user_data['perfs']['blitz']['games'],
                                blitz_rating = user_data['perfs']['blitz']['rating'],
                                rapid_games = user_data['perfs']['rapid']['games'],
                                rapid_rating = user_data['perfs']['rapid']['rating'],
                                classical_games = user_data['perfs']['classical']['games'],
                                classical_rating = user_data['perfs']['classical']['rating']
            )
            
        except ApiError:
            logger.error('While get_public_data from Lichess API')
            return None

    def show_user_info(self) -> None:
        """This function displays the user information if it has been fetched, otherwise it prints "No user data has been fetched".

        Returns: None
        """

        if self.user_data is None:
            print('No user data has been fetched')
            return False
        else:
            print(f'User {self.user_data.id} created on {self.user_data.creation_date}')
            print(f'Rating Classical : {self.user_data.classical_rating:4} ({self.user_data.classical_games:4} games)')
            print(f'Rating Rapid     : {self.user_data.rapid_rating:4} ({self.user_data.rapid_games:4} games)')
            print(f'Rating Blitz     : {self.user_data.blitz_rating:4} ({self.user_data.blitz_games:4} games)')
            print(f'Rating Bullet    : {self.user_data.bullet_rating:4} ({self.user_data.bullet_games:4} games)')


    def fetch_user_games(self, since: datetime, until: datetime) -> int:
        """This function retrieves the games played by the user between the specified date range from the Lichess API. The date range is specified using since and until arguments of datetime type. The function returns the number of games retrieved as an int, or None if an exception occurs.
        The function converts the datetime arguments since and until to milliseconds using the berserk.utils.to_millis function. It then uses the self.client.games.export_by_player method to retrieve the games and stores them as GameData objects in the self.games list.
        For each game, the function extracts relevant information such as the players' IDs, winner, moves, evaluations, mates, and judgment information. These values are used to create a GameData object and append it to the self.games list.
        The function logs the number of games retrieved using the logger.info method. In case of an exception, the error message is logged using the logger.error method.
        """

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
            
            for game_data in games_gen:
                
                black_id = game_data['players']['black']['user']['id']
                white_id = game_data['players']['white']['user']['id']
                
                if self.lichess_id == black_id:
                    user_side = 'black'
                    opponent_side = 'white'
                    opponent_id = white_id
                elif self.lichess_id == white_id:
                    user_side = 'white'
                    opponent_side = 'black'
                    opponent_id = black_id
                    
                if game_data['winner'] == user_side:
                    result = 'win'
                elif game_data['winner'] == opponent_side:
                    result = 'loss'
                else:
                    result = 'draw'
                    
                evals = [move.get('eval', float('nan')) for move in game_data['analysis']]
                mates = [move.get('mate', float('nan')) for move in game_data['analysis']]
                judgment = [move.get('judgment', None) for move in game_data['analysis']]
                judgment_name = [judge.get('name', '') for judge in judgment if judge!=None]
                judgment_comment = [judge.get('comment', '') for judge in judgment if judge!=None]
             
                game = GameData(
                                user_id = self.lichess_id,
                                game_id = game_data['id'],
                                user_side = user_side,
                                opponent_id = opponent_id,
                                time_control = game_data['perf'],
                                creation_date =  game_data['createdAt'],
                                opening = game_data['opening']['name'],
                                result = result,
                                moves = game_data['moves'].split(),
                                evals = evals,
                                mates = mates,
                                judgment_name = judgment_name,
                                judgment_comment = judgment_comment
                )
                
                self.games.append(game)
                
            self.games_df = pd.DataFrame([game.dict() for game in self.games])
                                
            logger.info(f'{len(self.games)} games retrieved')
            return len(self.games)

        except Exception as e:
            logger.error(f'Exception "{e}" while fetching games from Lichess API')
            return None


    def show_games_info(self) -> None:

        if self.games is None:
            print('No games have been fetched yet')
            return
        elif self.games == []:
            print('No games have been found for this time period')
            return
        else:
            print(f'Fetched {len(self.games)} games')
            print(f'Last game from  : {self.games[0].creation_date}')
            print(f'First game from : {self.games[-1].creation_date}')
