import os
import sys
import time
import random
import logging
import datetime

import joblib
import pandas as pd
import psycopg

sys.path.insert(0, os.path.abspath("."))
from prefect import flow, task
from evidently import ColumnMapping
from evidently.report import Report
from evidently.metrics import (
    ColumnDriftMetric,
    DatasetDriftMetric,
    ColumnSummaryMetric,
    DatasetMissingValuesMetric,
)

from src import config

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s"
)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


SEND_TIMEOUT = 10
rand = random.Random()

create_table_statement = """
drop table if exists nba_predictions;
create table nba_predictions(
    timestamp timestamp,
	num_drifted_columns integer,
    share_missing_values float,
    fg_opp_10_summary float,
    fg_nopp_10_summary float,
    fg_opp_10_col_drift float,
    fg_nopp_10_col_drift float
)
"""


with open('models/rf_nba.bin', 'rb') as f_in:
    model = joblib.load(f_in)


reference_data = pd.read_parquet(
    os.path.join(config.OUTPUT_PATH, "nba-2022-season-predictions-reference.parquet")
)
raw_data = pd.read_parquet(os.path.join(config.OUTPUT_PATH, "test.parquet"))

unique_dates = raw_data['date'].unique()
raw_data = raw_data[raw_data['date'].isin(unique_dates[:30])].copy()


begin = raw_data['date'].min()  # date of the first game of the corresponding season

num_features = config.BEST_COLUMNS

column_mapping = ColumnMapping(
    numerical_features=num_features, target=None, prediction='game_prediction'
)

report = Report(
    metrics=[
        DatasetDriftMetric(),
        DatasetMissingValuesMetric(),
        ColumnSummaryMetric(column_name="fg_opp_10"),
        ColumnSummaryMetric(column_name="fg_10_nopp"),
        ColumnDriftMetric(column_name="fg_opp_10", stattest="wasserstein"),
        ColumnDriftMetric(column_name="fg_10_nopp", stattest="wasserstein"),
    ]
)


@task
def prep_db():
    with psycopg.connect(
        "host=localhost port=5432 user=postgres password=example", autocommit=True
    ) as conn:
        res = conn.execute("SELECT 1 FROM pg_database WHERE datname='test'")
        if len(res.fetchall()) == 0:
            conn.execute("create database test;")
        with psycopg.connect(
            "host=localhost port=5432 dbname=test user=postgres password=example"
        ) as conn:
            conn.execute(create_table_statement)


@task(retries=2, retry_delay_seconds=5, name='calculate metrics')
def calculate_metrics_postgresql(curr, i):
    target_date = begin + datetime.timedelta(i)
    current_data = raw_data[
        (raw_data['date'] >= target_date)
        & (raw_data['date'] < (target_date + datetime.timedelta(1)))
    ]
    current_data['game_prediction'] = model.predict(current_data[num_features])
    report.run(
        reference_data=reference_data,
        current_data=current_data,
        column_mapping=column_mapping,
    )
    result = report.as_dict()

    num_drifted_columns = result['metrics'][0]['result']['number_of_drifted_columns']
    share_missing_values = result['metrics'][1]['result']['current'][
        'share_of_missing_values'
    ]
    fg_opp_10_summary = result['metrics'][2]['result']['current_characteristics']['p50']
    fg_nopp_10_summary = result['metrics'][3]['result']['current_characteristics'][
        'p50'
    ]
    fg_opp_10_col_drift = result['metrics'][4]['result']['drift_score']
    fg_nopp_10_col_drift = result['metrics'][5]['result']['drift_score']

    curr.execute(
        "insert into nba_predictions(timestamp, num_drifted_columns, share_missing_values, fg_opp_10_summary, fg_nopp_10_summary, fg_opp_10_col_drift, fg_nopp_10_col_drift) values (%s, %s, %s, %s, %s, %s, %s)",
        (
            begin + datetime.timedelta(i),
            num_drifted_columns,
            share_missing_values,
            fg_opp_10_summary,
            fg_nopp_10_summary,
            fg_opp_10_col_drift,
            fg_nopp_10_col_drift,
        ),
    )


@flow
def batch_monitoring_backfill():
    prep_db()
    last_send = datetime.datetime.now() - datetime.timedelta(seconds=10)
    with psycopg.connect(
        "host=localhost port=5432 dbname=test user=postgres password=example",
        autocommit=True,
    ) as conn:
        for i in range(0, 30):
            target_date = begin + datetime.timedelta(i)
            if target_date in raw_data['date'].values:
                with conn.cursor() as curr:
                    calculate_metrics_postgresql(curr, i)
            else:
                continue

            new_send = datetime.datetime.now()
            seconds_elapsed = (new_send - last_send).total_seconds()
            if seconds_elapsed < SEND_TIMEOUT:
                time.sleep(SEND_TIMEOUT - seconds_elapsed)
            while last_send < new_send:
                last_send = last_send + datetime.timedelta(seconds=10)
            logging.info("data sent")


if __name__ == '__main__':
    batch_monitoring_backfill()
