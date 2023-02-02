from typing import KeysView
import logging
from datetime import datetime, timedelta

import pandas as pd

from data_structures import TimeControls, UserLichessData
from data_handling import Database

# Create configure module   module_logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class DataLogic:
    """Business logic holding data store instances"""

    db = None
    
    def __init__(self):
        self.db = Database()

    def player_data_lichess(self, player_id) -> UserLichessData:
        user_data = self.db.retrieve_user_data(player_id)
        return user_data

    def player_openings(self, player_id, side):

        user_games = self.db.retrieve_user_games(player_id)
        logger.info(f'Player_openings analysis received {len(user_games)} games')
        openings_dict = {
            'opening': [],
            'color': [],
            'result': [],
            'date': [],
            'time': [] 
            }
        for game in user_games:
            openings_dict['opening'].append(game.opening)
            openings_dict['color'].append(game.color)
            openings_dict['result'].append(game.result)
            openings_dict['date'].append(game.creation_date)
            openings_dict['time'].append(game.time_control)

        openings_df = pd.DataFrame.from_dict(openings_dict)
        openings_df = openings_df[openings_df['color']==side]
        stats_df = openings_df.groupby(['opening', 'result']).size().unstack(fill_value=0)
        stats_df['total'] = openings_df['opening'].value_counts()
        stats_df.sort_values('total',ascending=True, inplace=True)
        stats_df.reset_index(inplace=True)

        return stats_df
