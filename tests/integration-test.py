import os
import sys
import subprocess
from datetime import datetime

import boto3
import pandas as pd

S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "http://localhost:4566")
INPUT_FILE_PATTERN = os.getenv("INPUT_FILE_PATTERN", None)
OUTPUT_FILE_PATTERN = os.getenv("OUTPUT_FILE_PATTERN", None)
BUCKET_NAME = os.getenv("BUCKET_NAME", "nba-predictions")


def read_dataframe(df) -> pd.DataFrame:
    """Read data into DataFrame"""
    df = df.loc[df["season"] > "2018"].sort_values("date").reset_index(drop=True)
    del df["index_opp"]
    df = df.dropna(axis=1, how="all")
    return df


def are_dates_sorted(dates_list):
    # Convert the list of strings to a list of datetime objects
    dates = [datetime.strptime(date_str, "%Y-%m-%d") for date_str in dates_list]
    # Check if the list is sorted in ascending order
    return all(dates[i] <= dates[i + 1] for i in range(len(dates) - 1))


def test_read_data():
    data = [
        (4, "2022-01-01", "2022", "MIA", "SAS"),
        (1, "2018-01-01", "2018", "CHI", "WAS"),
        (2, "2019-01-01", "2019", "PHI", "DAL"),
        (1, "2020-01-01", "2020", "BOS", "LAL"),
        (3, "2023-01-01", "2023", "HOU", "CLE"),
        (3, "2021-01-01", "2021", "ATL", "MIN"),
    ]

    columns = ["index_opp", "date", "season", "team", "team_opp"]
    df = pd.DataFrame(data, columns=columns)
    df = read_dataframe(df)

    # print(df.date.to_list())

    assert list(df["season"].unique()) == ["2019", "2020", "2021", "2022", "2023"]
    assert "index_opp" not in df.columns
    assert are_dates_sorted(df.date.to_list())


def test_save_data(year: int):
    subprocess.run(["python src/predict_cloud.py %s" % (year)], shell=True)

    s3 = boto3.client("s3", endpoint_url=S3_ENDPOINT_URL)
    response = s3.list_objects_v2(Bucket=BUCKET_NAME)
    objects = response.get("Contents", [])

    assert objects and all(
        obj["Size"] > 0 for obj in objects
    ), "Bucket is empty or contains objects with zero size"


if __name__ == "__main__":
    year = sys.argv[1]
    test_read_data()
    test_save_data(year=int(year))
