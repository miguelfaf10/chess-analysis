import pickle, json

from distutils.debug import DEBUG
from typing import List

import logging
from pprint import pprint

from datetime import datetime
import pandas as pd
import berserk
from berserk.exceptions import ApiError 

from data_structures import Game, UserLichess

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
        games (List[Game]): List of game information for the user.
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

    def fetch_user_data(self, save_reply=False, use_saved_reply=False):
        """Fetch and store public data of a lichess user.
        This function uses the Lichess API to retrieve public data of the lichess user, specified by the lichess_id attribute of the class instance. The data is stored in the user_data attribute of the class instance as an instance of the UserLichessData class.
        
        Returns: None
        
        Raises: Exception: If there's an error in fetching the user data from the Lichess API. The error message is logged with logger.error.
        """
        # Try to retrieve public data of the user with id self.lichess_id
        try:
            
            if use_saved_reply:
                with open('user_data.pickle','rb') as fp:                
                    user_data = pickle.load(fp)                
            else:
                # Get public data of the user with id self.lichess_id from the client object
                user_data = self.client.users.get_public_data(self.lichess_id)
                
            if save_reply:
                with open('user_data.pickle','wb') as fp:
                    pickle.dump(user_data, fp)
            
            # If logger's effective level is set to logging.DEBUG
            if logging.DEBUG == logger.getEffectiveLevel():
                # Dump the received data to a JSON file in the "logs" directory with the name lichessAPI_user_{self.lichess_id}.json
                with open(f'logs/lichessAPI_user_{self.lichess_id}.json', 'w') as fp:
                    json.dump(user_data , fp, default=str, indent=4)

            # Store relevant data from the user_data in an instance of the UserLichessData class
            self.user_data = UserLichess(
                                lichess_id = user_data['id'],
                                creation_date = user_data['createdAt'],
                                games_bullet = user_data['perfs']['bullet']['games'],
                                rating_bullet = user_data['perfs']['bullet']['rating'],
                                games_blitz = user_data['perfs']['blitz']['games'],
                                rating_blitz = user_data['perfs']['blitz']['rating'],
                                games_rapid = user_data['perfs']['rapid']['games'],
                                rating_rapid = user_data['perfs']['rapid']['rating'],
                                games_classical = user_data['perfs']['classical']['games'],
                                rating_classical = user_data['perfs']['classical']['rating']
            )
        # If an ApiError occurs, log the error and return None  
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
            print(f'User {self.user_data.lichess_id} created on {self.user_data.creation_date}')
            print(f'Rating Classical : {self.user_data.rating_classical:4} ({self.user_data.games_classical:4} games)')
            print(f'Rating Rapid     : {self.user_data.rating_rapid:4} ({self.user_data.games_rapid:4} games)')
            print(f'Rating Blitz     : {self.user_data.rating_blitz:4} ({self.user_data.games_blitz:4} games)')
            print(f'Rating Bullet    : {self.user_data.rating_bullet:4} ({self.user_data.games_bullet:4} games)')


    def fetch_user_games(self, since: datetime, until: datetime, save_reply=False, use_saved_reply=False) -> int:
        """This function retrieves the games played by the user between the specified date range from the Lichess API. The date range is specified using since and until arguments of datetime type. The function returns the number of games retrieved as an int, or None if an exception occurs.
        The function converts the datetime arguments since and until to milliseconds using the berserk.utils.to_millis function. It then uses the self.client.games.export_by_player method to retrieve the games and stores them as Game objects in the self.games list.
        For each game, the function extracts relevant information such as the players' IDs, winner, moves, evaluations, mates, and judgment information. These values are used to create a Game object and append it to the self.games list.
        The function logs the number of games retrieved using the logger.info method. In case of an exception, the error message is logged using the logger.error method.
        """
        # Convert 'since' and 'until' from datetime objects to milliseconds
        since_millis = int(berserk.utils.to_millis(since))
        until_millis = int(berserk.utils.to_millis(until))

        try:
            # Log information about retrieving games from Lichess
            logger.info(f'Retrieving games from lichess for user "{self.lichess_id}"')
            logger.info(f'Between {since} and {until}')
            
            if use_saved_reply:
                with open('game_data.pickle','rb') as fp:                
                    games = pickle.load(fp)                
            else:
                # Get a generator of games from Lichess API using the export_by_player method
                games = self.client.games.export_by_player(self.lichess_id,
                                                                rated=True,
                                                                since=since_millis,
                                                                until=until_millis,
                                                                evals=self.get_evals,
                                                                opening=self.get_opening)
                games = list(games)
                logger.debug(f'Number of games exported from Lichess using berserk module: {len(games)}')
                
            if save_reply:
                
                with open('game_data.pickle','wb') as fp:
                    pickle.dump([game for game in games], fp)
                        
            # Iterate through the generator of games
            for i,game_data in enumerate(games):
                # If logger is in debug mode, write each game data to a separate file
                if logging.DEBUG == logger.getEffectiveLevel():
                    id = game_data['id']
                    logger.debug(f'Retrieving game {i} with ID: {id}')
                
                    with open(f'logs/lichessAPI_game_{self.lichess_id}_{id}.json', 'w') as fp:
                        json.dump(game_data , fp, default=str, indent=4)
                
                # Get the id of black and white players in the game
                black_id = game_data['players']['black']['user']['id']
                white_id = game_data['players']['white']['user']['id']
                
                # Determine the side of the user and the opponent in the game
                if self.lichess_id == black_id:
                    user_side = 'black'
                    opponent_side = 'white'
                    opponent_id = white_id
                elif self.lichess_id == white_id:
                    user_side = 'white'
                    opponent_side = 'black'
                    opponent_id = black_id
                    
                # Determine the result of the game 
                if 'winner' in game_data.keys(): 
                    if game_data['winner'] == user_side:
                        result = 'win'
                    elif game_data['winner'] == opponent_side:
                        result = 'loss'
                    else:
                        result = 'draw'
                else:
                    result = ''
                    
                if 'opening' in game_data.keys():
                    opening = game_data['opening']['name']
                    
                # Extract relevant information from the game analysis
                if 'analysis' in game_data.keys():
                    analysis = True
                    evals = [move.get('eval', float('nan')) for move in game_data['analysis']]
                    mates = [move.get('mate', float('nan')) for move in game_data['analysis']]
                    judgment = [move.get('judgment', None) for move in game_data['analysis']]
                    judgment_name = [judge.get('name', '') for judge in judgment if judge!=None]
                    judgment_comment = [judge.get('comment', '') for judge in judgment if judge!=None]
                else:
                    analysis = False
                    evals = [float('nan')]
                    mates = [float('nan')]
                    judgment_name = ['']
                    judgment_comment = ['']
                                
                # Create pydantic data structure object and fill it with retrieved information
                game = Game(
                                user_id = self.lichess_id,
                                game_id = game_data['id'],
                                user_side = user_side,
                                opponent_id = opponent_id,
                                time_control = game_data['perf'],
                                creation_date =  game_data['createdAt'],
                                opening = opening,
                                result = result,
                                moves = game_data['moves'].split(),
                                analysis = analysis,
                                evals = evals,
                                mates = mates,
                                judgment_name = judgment_name,
                                judgment_comment = judgment_comment
                )
                # Append game object into list of games
                self.games.append(game)
                
            # Create dataframe with info about all retrieved games
            self.games_df = pd.DataFrame([game.dict() for game in self.games])
                                
            logger.info(f'{len(self.games)} games retrieved')
            return len(self.games)

        except Exception as e:
            logger.error(f'Exception "{e}" while fetching games from Lichess API')
            return None


    def show_games_info(self) -> None:
        """Prints information about the fetched games.
        If no games have been fetched yet, prints a message indicating that.
        If no games have been found for the specified time period, prints a message indicating that.
        If games have been fetched, prints the number of games fetched and the creation date of the
        first (most recent) and last (oldest) game.
        """
        # If self.games is None
        if self.games is None:
            # Print a message indicating that no games have been fetched yet
            print('No games have been fetched yet')
            # Return immediately
            return
        # If self.games is an empty list
        elif self.games == []:
            # Print a message indicating that no games have been found for this time period
            print('No games have been found for this time period')
            return
        # If self.games is a non-empty list
        else:
            # Print the number of games that have been fetched, as well as the most recent and the oldest game
            print(f'Fetched {len(self.games)} games')
            print(f'Last game from  : {self.games[0].creation_date}')
            print(f'First game from : {self.games[-1].creation_date}')