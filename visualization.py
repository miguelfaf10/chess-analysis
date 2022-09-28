from typing import Dict
import logging 

from dash import Dash, html, dcc
from dash.dependencies import Input, Output


import plotly.express as px
import pandas as pd

from data_logic import DataLogic

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)



data = DataLogic()
app = Dash(__name__)

app.layout = html.Div([
    html.H1('Chess Insight'),
    dcc.Input(id='lichess_id',
                type='text',
                placeholder='Lichess ID',
                debounce=True),
    html.Hr(),
    html.Div(id='rating-str'),
    dcc.Graph(id='rating-fig',
                config={'displayModeBar': False}),
    html.Hr(),
    dcc.Tabs(id='tabs-selection', value='tab-opening', children=[
        dcc.Tab(label='Rating', value='tab-rating'),
        dcc.Tab(label='Opening', value='tab-opening'),
        dcc.Tab(label='Analysis', value='tab-analysis'),
    ]),
    html.Div(id='tabs-content')
])

@app.callback(
    Output('rating-str', 'children'),
    Output('rating-fig', 'figure'),
    Input('lichess_id', 'value')
)
def validate_id(lichess_id):

    if lichess_id == None or lichess_id == '':
        rating_str = f''
        rating_fig = px.bar(x=['Classical','Rapid','Blitz','Bullet'],
                            y=[0,0,0,0],
                            labels={'x':'Time Control', 'y':'Rating'})
    else:
#        data.process_user(lichess_id)
        player_data = data.player_data_lichess(lichess_id)

        if player_data != None:
            rating_str = (f'On Lichess since {player_data.createdAt.strftime("%d/%m/%Y")}')
            rating_fig = px.bar(x=['Classical','Rapid','Blitz','Bullet'],
                                y=[player_data.perfs.classical.rating, 
                                    player_data.perfs.rapid.rating,
                                    player_data.perfs.blitz.rating,
                                    player_data.perfs.bullet.rating],
                                labels={'x':'Time Control', 'y':'Rating'})
        
        else:
            rating_str = f'User not found in Lichess'
            rating_fig = None

    return rating_str, rating_fig


@app.callback(
    Output('tabs-content', 'children'),
    Input('tabs-selection', 'value'),
    Input('lichess_id', 'value')
)
def render_content(tab, lichess_id):
    if tab == 'tab-opening':
        logger.info(f'Opening tab has been selected for user {lichess_id}.')
        opening_white_df = data.player_openings(lichess_id, 'white').tail(10)
        opening_black_df = data.player_openings(lichess_id, 'black').tail(10)
        return html.Div([
            html.H3('Opening'),
            dcc.Graph(
                figure=px.bar(opening_white_df,y='White',x=opening_white_df.columns[:-1]), # trick to include 'draw' column when avaible and remove 'total' col
                config={'displayModeBar': False}
            ),
            dcc.Graph(
                 figure=px.bar(opening_black_df,y='Black',x=opening_black_df.columns[:-1]),
                 config={'displayModeBar': False}
             )
 
        ])
    elif tab == 'tab-rating':
        logger.info(f'Rating tab has been selected for user {lichess_id}.')
        return html.Div([
            html.H3('Rating'),
            dcc.Graph(
                
            )
        ])
    elif tab == 'tab-analysis':
        logger.info(f'Analysis tab has been selected for user {lichess_id}.')
        return html.Div([
            html.H3('Analysis'),
            dcc.Graph(
                
            )
        ])


if __name__ == '__main__':

    logging.basicConfig(format='%(asctime)s [%(levelname)7s] %(name)30s <%(funcName)20s(),%(lineno)d> \n%(message)s',
                        level=logging.INFO)
    logger = logging.getLogger(__name__)

    app.run_server(debug=True, port=8090)