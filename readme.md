


Code Structure
--------------

visualization.py - Dash webapp
------------------------------
------------------------------
* Instantiates single DataLogic() object from module data_logic.py


data_logic.py - Interface functions for webapp
------------------------------------------------------------
------------------------------------------------------------
* Instantiates single Database() object from data_handling.py
* Declares:
* player_general_info() - Retrieve player info
* player_openings() - Retrieve player opening statistics


data_handling.py - Manages local database
------------------------------------------------------------
------------------------------------------------------------
* Declares SQLAlchemy dataclasses:

    **class Users(Base)**:
    - user_id
    - creation_date
    - rating_classical
    - rating_rapid
    - rating_blitz
    - rating_bullet
    - games_classical
    - games_rapid
    - games_blitz
    - games_bullet
    - last_update

    **class Games(Base)**:
    - game_id
    - user_id
    - color
    - opponent
    - time_control
    - creation_date
    - opening
    - result
    - moves
    - analysis
    - evals
    - mates
    - judgment
    - children

* Declares Database class
    - _update_user_data(user:Users) -> None
    - _migrate_user_data(lichess_id:str) -> None
    - retrieve_user_games(lichess_id:str) -> Games
    - retrieve_user_data(lichess_id:str) -> User


chessportals_comm.py - Handles communication with portals API's
------------------------------------------------------------
------------------------------------------------------------
* Declares LichessComm(lichess_id:str)
    - fetch_user_rating()
    - fetch_user_data()
    - fetch_user_games(since: datetime, until: datetime) -> List[GameData]
    - show_games_info() -> None
    - show_user_info() -> None
    - fill_df() -> pd.DataFrame


data_structures.py - Contains Pydantic dataclasses for API comm
------------------------------------------------------------
------------------------------------------------------------


Inspiration
-----------
    - https://natesolon.github.io/blog/tree