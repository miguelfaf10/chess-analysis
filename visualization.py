from typing import Dict
import logging 

from dash import Dash, html, dcc
from dash.dependencies import Input, Output


import plotly.express as px
import pandas as pd

from data_logic import DataLogic

logger = logging.getLogger(__name__)



data = DataLogic()
app = Dash(__name__)

app.layout = html.Div(
    [
        html.H1('Chess Insight'),
        dcc.Input(id='lichess_id',
                  type='text',
                  placeholder='Lichess ID',
                  debounce=True),
        html.Hr(),
        html.Div(id='lichess-id-exists'),
        html.Hr(),
        dcc.Tabs(id="tabs-example-graph", value='tab-1-example-graph', children=[
            dcc.Tab(label='Rating', value='tab-rating'),
            dcc.Tab(label='Opening', value='tab-opening'),
            dcc.Tab(label='Analysis', value='tab-analysis'),
        ])
    ]
)

@app.callback(
    Output("lichess-id-exists", "children"),
    Input("lichess_id", "value")
)
def validate_id(lichess_id):

    if lichess_id == None or lichess_id == '':
        return f'Classical rating : ____'
    else:
#        data.process_user(lichess_id)
        info = data.player_general_info(lichess_id)
        return f'Classical rating : {info.rating_classical}'

@app.callback(Output('tabs-content-example-graph', 'children'),
              Input('tabs-example-graph', 'value'))
def render_content(tab):
    if tab == 'tab-':
        return html.Div([
            html.H3('Tab content 1'),
            dcc.Graph(
                figure={
                    'data': [{
                        'x': [1, 2, 3],
                        'y': [3, 1, 2],
                        'type': 'bar'
                    }]
                }
            )
        ])
    elif tab == 'tab-2-example-graph':
        return html.Div([
            html.H3('Tab content 2'),
            dcc.Graph(
                id='graph-2-tabs-dcc',
                figure={
                    'data': [{
                        'x': [1, 2, 3],
                        'y': [5, 10, 6],
                        'type': 'bar'
                    }]
                }
            )
        ])


if __name__ == '__main__':

    logging.basicConfig(format='%(asctime)s [%(levelname)7s] %(name)30s <%(funcName)20s(),%(lineno)d> \t%(message)s',
                        level=logging.INFO)
    logger = logging.getLogger(__name__)

    app.run_server(debug=True, port=8090)