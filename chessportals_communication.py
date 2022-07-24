from typing import List
from datetime import datetime
import pandas as pd
import berserk

from data_structures import GameData, UserData

class LichessComm:
    
    lichess_id = None
    API_TOKEN = None
    client = None
    
    user_data = None
    
    get_opening = True
    get_evals = True
    games_lst = []
    games_df = None
    
    def __init__(self, user) -> None:
        
        # Initialize token
        with open('conf/token.txt') as f:
            self.API_TOKEN = f.readline()[:-1]
        
        # Initialize lichess client
        self.lichess_id = user
        session = berserk.TokenSession(self.API_TOKEN)
        self.client = berserk.Client(session=session)
    
    def fetch_user_rating(self):
        
        player_rating = self.client.users.get_rating_history(self.lichess_id)

        return player_rating

    def fetch_user_data(self):
        
        user_data = self.client.users.get_public_data(self.lichess_id)

        self.user_data = UserData(**user_data)

        return self.user_data

    def fetch_user_games(self, since: datetime, until: datetime) -> List[GameData]:
    
        since_millis = int(berserk.utils.to_millis(since))
        until_millis = int(berserk.utils.to_millis(until))

        games_gen = self.client.games.export_by_player(self.lichess_id,
                                                       rated=True,
                                                       since=since_millis,
                                                       until=until_millis,
                                                       evals=self.get_evals,
                                                       opening=self.get_opening)

        self.games_lst = [GameData(**game) for game in games_gen] 

        return self.games_lst
    
        #for game in games_gen:
        #    try:
        #        self.games_lst.append(GameData(**game))
        #    except:
        #        print(game)
        
    def show_games_info(self) -> None:
        
        if self.games_lst == None:
            print('No games have been fetched')
            return False
        else:
            print(f'Fetched {len(self.games_lst)} games')
            print(f'Last game from  : {self.games_lst[0].createdAt}')
            print(f'First game from : {self.games_lst[-1].createdAt}')

    def show_user_info(self) -> None:
        
        if self.user_data == None:
            print('No user data has been fetched')
            return False
        else:
            print(f'User {self.user_data.id} created at {self.user_data.createdAt}')
            print(f'Rating Classical : {self.user_data.perfs.classical.rating:4} ({self.user_data.perfs.classical.games:4} games)')
            print(f'Rating Rapid     : {self.user_data.perfs.rapid.rating:4} ({self.user_data.perfs.rapid.games:4} games)')
            print(f'Rating Blitz     : {self.user_data.perfs.blitz.rating:4} ({self.user_data.perfs.blitz.games:4} games)')
            print(f'Rating Bullet    : {self.user_data.perfs.bullet.rating:4} ({self.user_data.perfs.bullet.games:4} games)')

    def fill_df(self) -> pd.DataFrame:

        games_dict = dict(game_id =[],
                          color = [],
                          opponent = [],
                          time_control = [],
                          creation_time = [],
                          opening = [],
                          result = [],
                          moves = [],
                          analysis = [],
                          evals = [],
                          mates = [],
                          judgment = [])

        for game in self.games_lst:

            games_dict['game_id'].append(game.id)

            games_dict['color'].append('white' if (game.players.white==self.lichess_id) else 'black')
            
            if game.players.white.user.id==self.lichess_id:
                games_dict['opponent'].append(game.players.black.user.id)
            else:
                games_dict['opponent'].append(game.players.white.user.id)
            
            games_dict['creation_time'].append(game.createdAt)
            
            games_dict['opening'].append(game.opening.name)
            
            if  game.winner=='draw':
                games_dict['result'].append('draw')
            elif game.winner=='white' and game.players.white.user.id==self.lichess_id:
                games_dict['result'].append('win')
            elif game.winner=='black' and game.players.black.user.id==self.lichess_id:
                games_dict['result'].append('win')
            else:
                games_dict['result'].append('loss')

            games_dict['time_control'].append(game.speed)

           
            games_dict['moves'].append(game.moves.split(' '))
            
            games_dict['analysis'].append(True if game.analysis!=None else False)
            
            games_dict['evals'].append([move_anal.eval for move_anal in game.analysis] 
                                       if game.analysis!=None else None)
            
            games_dict['mates'].append([move_anal.mate for move_anal in game.analysis] 
                                       if game.analysis!=None else None)
            
            games_dict['judgment'].append([move_anal.judgment.name if move_anal.judgment!='' else '' for move_anal in game.analysis] 
                                          if game.analysis!=None else None)

        self.games_df = pd.DataFrame.from_dict(games_dict, orient='columns')
        #self.games_df.set_index('id', inplace=True)
        
        return self.games_df