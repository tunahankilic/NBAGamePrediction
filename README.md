# NBA Game Predictor


## Description

This is a project to predict the results of upcoming NBA games. The data of the project starts from 2018-2019 season up to and including 2022-2023 season and it was gathered from [Basketball-Reference](https://www.basketball-reference.com/). Basic and advanced stats provided in the box scores of the games are the key points to execute successful predictions. The NBA Game Predictor uses data from 2016 to 2022 in order to predict the game results of 2022-2023 season. Since moving averages were input as feature to the model, the model starts its predictions after the 10th game.

To give an idea of the data used, the schedule and results page for the 22-23 season and box score tables for the first game of the season can be found in the links below.

[2022-23 NBA Schedule and Results](https://www.basketball-reference.com/leagues/NBA_2023_games.html)

[Philadelphia 76ers at Boston Celtics Box Score, October 18, 2022](https://www.basketball-reference.com/boxscores/202210180BOS.html)


## Table of Contents

- [Installation](#installation)
- [Usage](#usage)

## Installation

To clone the project to your local and to change the working directory to the project path:

```bash
git clone https://github.com/tunahankilic/NBAGamePrediction
cd NBAGamePrediction
```

Once the cloning is done, run the following command to setup the project environment:

```bash
make setup
pipenv shell
```

## Usage

Before get in to train the prediction model, ``Prefect`` server and ``MLflow`` must be up and running to ensure orchestration and tracking of the process. In order to run both, the following commands should be executed in separate terminals for each. Before that, the virtual environment must be enabled in each terminal.

#### Start Prefect Server

```bash
make prefect_server
```

#### Start MLflow Server
```bash
make mlflow_server
```

### Model Train

To train the result prediction model, simply run the following make command. This will, first perform the hyperparameter tuning of our model by using ``Optuna`` (a hyperparameter optimization framework), log each trial to ``MLflow`` with corresponding hyperparameters, the the hyperparameter tuning is finished, it automatically starts model training. Once the model training is done, the best model is saved in ``models/`` path and is registered to ``MLflow`` for prediction purposes.

```bash
make train
```

### Model Test

To evaluate the model's performance on the unseen data, simply run the following command to execute prediction.

```bash
make predict
```

### Model Deployment

To deploy the result predictor model in ``Docker``, run the following command. It will first build the Docker image from a Dockerfile and then it starts a new container from a specified image.

```bash
make deploy
```

### Model Monitoring

``Evidently`` is used to evaluate, test and monitor the model. It is an open-source tool that fulfills the whole aforementioned processes. ``Prefect`` must be up and running for monitoring process as well. Monitoring will start simply by running the following command.

```bash
make monitor
```

To monitor and evaluate the model, ``PostgreSQL`` is used to store evaluation metrics of Evidently and ``Adminer`` is used to provide database management process. To visualize every metric that was calculated, ``Grafana``, the open source analytics & monitoring solution, is used. There is a previously created dashboard for calculated metrics and it is customizable by changing the metrics in ``monitoring/evidently_monitoring.py``

Adminer can be accessible at:
```
localhost:8080
```
Grafana can be accessible at:
```
localhost:3000
```

Once the monitoring done, the monitoring service must be stopped by running following command:

```bash
docker-compose -f monitoring/docker-compose.yaml down
```

### Integration Tests

``Localstack`` is used to run AWS S3 cloud storage on your local machine without connecting to a remote cloud provider. As a part of integration test, ``src/predict_cloud.py`` is running and save the results as a parquet file to a specified path in AWS S3. There are couple of tests that are carried out. To run integration tests, simply run the following command:

```bash
make integration_test
```
