from typing import KeysView
import logging
from datetime import datetime, timedelta

import pandas

from data_structures import TimeControls
from data_handling import Database, Users, Games

# Create configure module   module_logger
logger = logging.getLogger(__name__)

class DataLogic:
    """Business logic holding data store instances"""

    db = None
    
    def __init__(self):
        self.db = Database()

    def player_general_info(self, player_id) -> Users:
        info = self.db.retrieve_user_data(player_id)
        return info

    def player_openings(self, player_id):
        self.db.retrieve_user_data(player_id)
        self.db.retrieve_user_games(player_id)
        return {}
