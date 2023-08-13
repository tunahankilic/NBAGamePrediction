import os
import pickle
import argparse

import pandas as pd
from prefect import flow, task

import config


@task(name="Target Creation")
def create_target(team: pd.DataFrame):
    team["target"] = team["won"].shift(-1)
    team["target"] = team["target"].map({True: 1, False: 0}).fillna(-1).astype(int)
    return team


def calculate_days_difference(team: pd.DataFrame):
    team["days_to_next_game"] = team["date"].diff().dt.days.shift(-1)
    return team


def rolling_averages(team: pd.DataFrame, window: int):
    rolling = team.rolling(window=window).mean()
    return rolling


def shift_col(team, col_name):
    next_col = team[col_name].shift(-1)
    return next_col


def add_col(df, col_name):
    df = df.copy()
    return df.groupby("team", group_keys=False).apply(lambda x: shift_col(x, col_name))


@task(retries=3, retry_delay_seconds=2, name="Read NBA Box Scores")
def read_dataframe(filename: str) -> pd.DataFrame:
    """Read data into DataFrame"""
    df = pd.read_parquet(os.path.join(config.INPUT_PATH, filename), engine="pyarrow")
    df = df.loc[df["season"] > "2018"].sort_values("date").reset_index(drop=True)
    del df["index_opp"]
    df = df.dropna(axis=1, how="all")
    return df


@flow
def run_data_prep(filename: str, season: int):
    df = read_dataframe(filename)

    df = df.groupby("team", group_keys=False).apply(create_target)
    df = df.groupby(["team", "season"], group_keys=False).apply(
        calculate_days_difference
    )
    removed_columns = ["season", "date", "won", "target", "team", "team_opp"]
    selected_columns = df.columns[~df.columns.isin(removed_columns)]
    df_rolling = df.groupby(["team", "season"], group_keys=False)[
        selected_columns
    ].apply(rolling_averages, window=10)
    rolling_cols = [f"{col}_10" for col in df_rolling.columns]
    df_rolling.columns = rolling_cols

    df = pd.concat([df, df_rolling], axis=1)
    df_filtered = (
        df.drop(df[df["target"] == -1].index)
        .reset_index(drop=True)
        .dropna()
        .reset_index(drop=True)
    )
    df_filtered["home_next"] = add_col(df_filtered, "home")
    df_filtered["team_opp_next"] = add_col(df_filtered, "team_opp")
    df_filtered["date_next"] = add_col(df_filtered, "date")

    df_full = df_filtered.merge(
        df_filtered[rolling_cols + ["team_opp_next", "date_next", "team"]],
        left_on=["team", "date_next"],
        right_on=["team_opp_next", "date_next"],
        suffixes=("", "_nopp"),
    )

    train = df_full.loc[df_full["season"] < str(season)]
    test = df_full.loc[df_full["season"] == str(season)]
    # Create dest_path folder unless it already exists
    os.makedirs(config.OUTPUT_PATH, exist_ok=True)
    train.to_parquet(
        os.path.join(config.OUTPUT_PATH, "train.parquet"), engine="pyarrow"
    )
    test.to_parquet(os.path.join(config.OUTPUT_PATH, "test.parquet"), engine="pyarrow")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--filename", type=str, default='nba_games.parquet')

    parser.add_argument("--season", type=int, default=2023)

    args = parser.parse_args()
    run_data_prep(filename=args.filename, season=args.season)
