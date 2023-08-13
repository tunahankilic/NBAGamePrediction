import os
import ast
import argparse

import numpy as np
import mlflow
import optuna
import pandas as pd
from optuna.samplers import TPESampler
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import TimeSeriesSplit

import config

mlflow.set_tracking_uri("http://127.0.0.1:5000")
mlflow.set_experiment("random-forest-optuna")


def run_optimization(data: pd.DataFrame, columns: list, num_trials: int):
    def objective(trial):
        scores = []

        X = data[columns]
        y = data["target"]
        # Define hyperparameter search space
        params = {
            "n_estimators": 500,
            "max_depth": trial.suggest_int("max_depth", 3, 15, 1),
            "min_samples_split": trial.suggest_int("min_samples_split", 2, 10, 1),
            "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 5, 1),
            "random_state": 2023,
            "n_jobs": -1,
        }

        with mlflow.start_run():
            mlflow.log_params(params)
            # Create the model with suggested hyperparameters
            model = RandomForestClassifier(**params)

            # Define TimeSeriesSplit cross-validation
            tscv = TimeSeriesSplit(n_splits=5)

            # Calculate the performance metric using cross_val_score and TimeSeriesSplit
            for fold, (train_index, test_index) in enumerate(tscv.split(X)):
                X_train, X_test = X.iloc[train_index], X.iloc[test_index]
                y_train, y_test = y.iloc[train_index], y.iloc[test_index]

                model.fit(X_train, y_train)
                preds = model.predict(X_test)
                acc_score = accuracy_score(y_test, preds)
                scores.append(acc_score)

            mlflow.log_metric("val_accuracy", np.mean(scores))
        # Return the average accuracy (Optuna maximizes the objective)
        return np.mean(scores)

    study = optuna.create_study(
        direction="maximize"
    )  # We want to maximize the accuracy
    study.optimize(
        objective, n_trials=num_trials
    )  # You can increase the number of trials for a more thorough search
    print("Number of finished trials: ", len(study.trials))
    print("Best trial:")
    trial = study.best_trial
    print("  Value: ", trial.value)
    print("  Params: ")
    for key, value in trial.params.items():
        print("    {}: {}".format(key, value))
    return trial


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--num_trials", type=int, default=20)
    args = parser.parse_args()

    df = pd.read_parquet(os.path.join(config.OUTPUT_PATH, "train.parquet"))
    run_optimization(data=df, columns=config.BEST_COLUMNS, num_trials=args.num_trials)
