from typing import KeysView
import logging
from datetime import datetime, timedelta

import pandas

from data_structures import TimeControls, UserData
from data_handling import Database

# Create configure module   module_logger
logger = logging.getLogger(__name__)

class DataLogic:
    """Business logic holding data store instances"""

    db = None
    
    def __init__(self):
        self.db = Database()

    def player_data_lichess(self, player_id) -> UserData:
        user_data = self.db.retrieve_user_data(player_id)
        return user_data

    def player_openings(self, player_id):
        self.db.retrieve_user_data(player_id)
        self.db.retrieve_user_games(player_id)
        return {}
