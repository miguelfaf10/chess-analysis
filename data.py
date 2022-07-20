from typing import Dict, KeysView, Optional, Union



class lichess_communication:
    
    lichess_id = None
    API_TOKEN = None
    client = None
    get_opening = True
    get_evals = True
    games_lst = None

    def __init__(self, user) -> None:
        
        # Initialize token
        with open('./token.txt') as f:
            self.API_TOKEN = f.readline()[:-1]
        
        # Initialize lichess client
        self.lichess_id = user
        session = berserk.TokenSession(self.API_TOKEN)
        self.client = berserk.Client(session=session)
    
    def get_games_by_dates(self, since, until)
    
        games_gen = client.games.export_by_player('miguel0f',
                                                    since=since,
                                                    until=until,
                                                    evals=self.get_evals,
                                                    opening=self.get_opening)


class Data:
    """Data Store Class"""

    products = {
        "milk": {"price": 1.50, "quantity": 10},
        "eggs": {"price": 0.20, "quantity": 100},
        "cheese": {"price": 2.00, "quantity": 10},
    }

    def __get__(self, obj, klas):

        print("(Fetching from Data Store)")
        return {"products": self.products}
