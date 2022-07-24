# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dcc
from dash.dependencies import Input, Output

import plotly.express as px
import pandas as pd

from chessportals_communication import lichess_communication

logger = logging.getLogger(__name__)

app = Dash(__name__)

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
df = pd.DataFrame({
    "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
    "Amount": [4, 1, 2, 2, 4, 5],
    "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
})

fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")

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
    ]
)

@app.callback(
    Output("lichess-id-exists", "children"),
    Input("lichess_id", "value")
)
def validate_id(lichess_id):

    print(lichess_id)
    if lichess_id == None or lichess_id == '':
        return f'Classical rating : ____'
    else:
        
        
        return f'Classical rating : {user_data.perfs.classical.rating}'

if __name__ == '__main__':
    app.run_server(debug=True, port=8090)