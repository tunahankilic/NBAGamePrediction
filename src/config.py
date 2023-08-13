import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# INPUT_FILE = "/Users/tunahankilic/Desktop/NBAGamePrediction/data/"\

INPUT_PATH = os.path.join(ROOT_DIR, "data")

# OUTPUT_FILE = "/Users/tunahankilic/Desktop/NBAGamePrediction/data/output"

OUTPUT_PATH = os.path.join(ROOT_DIR, "data", "output")

# MODEL_OUTPUT = "/Users/tunahankilic/Desktop/NBAGamePrediction/models/"

MODEL_OUTPUT = os.path.join(ROOT_DIR, "models")

SOURCE_PATH = os.path.join(ROOT_DIR, "src")

BEST_COLUMNS = [
    "drb",
    "pf",
    "usg%",
    "fg_opp",
    "3p_opp",
    "tov_opp",
    "usg%_opp",
    "days_to_next_game",
    "tov%_10",
    "usg%_10",
    "ortg_10",
    "drtg_10",
    "pace_10",
    "fg_opp_10",
    "3p%_opp_10",
    "ft%_opp_10",
    "pts_opp_10",
    "usg%_opp_10",
    "ortg_opp_10",
    "drtg_opp_10",
    "pace_opp_10",
    "total_opp_10",
    "home_next",
    "fg_10_nopp",
    "3p%_10_nopp",
    "trb_10_nopp",
    "usg%_10_nopp",
    "ortg_10_nopp",
    "usg%_opp_10_nopp",
    "drtg_opp_10_nopp",
]
