import os
import pickle
import pathlib

import matplotlib

matplotlib.use("Agg")  # For macOS

import mlflow
import pandas as pd
from prefect import flow, task
from mlflow.entities import ViewType
from mlflow.tracking import MlflowClient
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestClassifier

import config

OPTUNA_EXPERIMENT_NAME = "random-forest-optuna"
EXPERIMENT_NAME = "random-forest-best-models"
RF_PARAMS = [
    "max_depth",
    "min_samples_leaf",
    "min_samples_split",
    "n_estimators",
    "n_jobs",
    "random_state",
]


mlflow.set_tracking_uri("http://127.0.0.1:5000")
mlflow.set_experiment(EXPERIMENT_NAME)
mlflow.sklearn.autolog(log_models=True)


def save_results(df, y_pred, output_file):
    df_result = pd.DataFrame()
    df_result = df.copy()
    df_result["game_prediction"] = y_pred

    df_result.to_parquet(output_file, engine="pyarrow", compression=None, index=False)


def get_paths(season: int):
    # input_file = os.path.join(config.OUTPUT_PATH, "test.parquet")
    pathlib.Path("data/output").mkdir(exist_ok=True)
    output_file = f"data/output/nba-{season}-season-predictions-reference.parquet"

    return output_file


@task(log_prints=True)
def train_and_log_model(data_path, params, predictors: list):
    train = pd.read_parquet(os.path.join(data_path, "train.parquet"))
    output_file = get_paths(season=2022)
    trn = train[train["season"] < "2022"]
    val = train[train["season"] == "2022"]

    with mlflow.start_run():
        converted_params = {key: int(value) for key, value in params.items()}
        mlflow.log_params(converted_params)

        rf = RandomForestClassifier(**converted_params)
        rf.fit(trn[predictors], trn["target"])
        # Evaluate model on the validation and test sets
        y_pred = rf.predict(val[predictors])
        val_accuracy = accuracy_score(val["target"], y_pred)
        save_results(val, y_pred, output_file)
        mlflow.log_metric("val_accuracy", val_accuracy)


@flow
def run_register_model(data_path: str, top_n: int):
    client = MlflowClient()

    # Retrieve the top_n model runs and log the models
    experiment = client.get_experiment_by_name(OPTUNA_EXPERIMENT_NAME)
    runs = client.search_runs(
        experiment_ids=experiment.experiment_id,
        run_view_type=ViewType.ACTIVE_ONLY,
        max_results=top_n,
        order_by=["metrics.val_accuracy DESC"],
    )
    for run in runs:
        train_and_log_model(
            data_path=data_path, params=run.data.params, predictors=config.BEST_COLUMNS
        )

    # Select the model with the best test Accuracy
    experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
    best_run = client.search_runs(
        experiment_ids=experiment.experiment_id,
        run_view_type=ViewType.ACTIVE_ONLY,
        order_by=["metrics.val_accuracy DESC"],
    )[0]

    # Register the best model
    run_id = best_run.info.run_id
    model_uri = f"runs:/{run_id}/model"
    mlflow.register_model(model_uri=model_uri, name="nba-game-prediction-best-model")

    model = mlflow.sklearn.load_model(model_uri)

    pathlib.Path("models").mkdir(exist_ok=True)
    with open("models/rf_nba.bin", "wb") as f_out:
        pickle.dump(model, f_out)


if __name__ == "__main__":
    run_register_model(data_path=config.OUTPUT_PATH, top_n=1)
