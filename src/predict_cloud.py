import os
import sys
import pickle
import pathlib

# from prefect import task, flow, get_run_logger
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score

import config

FILEPATH = Path(__file__).parent.resolve()
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "http://localhost:4566")


with open("models/rf_nba.bin", "rb") as f_in:
    model = pickle.load(f_in)


def save_results(df, y_pred, output_pattern):
    if S3_ENDPOINT_URL:
        options = {"client_kwargs": {"endpoint_url": S3_ENDPOINT_URL}}
        df_result = pd.DataFrame()
        df_result = df.copy()
        df_result["game_prediction"] = y_pred

        df_result.to_parquet(
            output_pattern,
            engine="pyarrow",
            compression=None,
            index=False,
            storage_options=options,
        )


def get_paths(season: int):
    input_file = os.path.join(config.OUTPUT_PATH, "test.parquet")
    output_file = os.getenv(
        "OUTPUT_FILE_PATTERN",
        "s3://nba-predictions/out/nba-{season:04d}-season-predictions.parquet",
    )

    return input_file, output_file.format(season=season)


def apply_model(input_file, output_file, columns, season):
    df = pd.read_parquet(input_file)
    y_pred = model.predict(df[columns])
    print(
        f'Prediction Accuracy for Season {season}: {accuracy_score(df["target"], y_pred):.2f}'
    )
    save_results(df, y_pred, output_file)

    return output_file


def game_result_prediction(season: int):
    input_file, output_file = get_paths(season)

    apply_model(
        input_file=input_file,
        output_file=output_file,
        columns=config.BEST_COLUMNS,
        season=season,
    )


def run():
    season = int(sys.argv[1])  # 2023
    game_result_prediction(season)


if __name__ == "__main__":
    run()
