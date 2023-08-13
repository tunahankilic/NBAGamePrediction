setup:
	pipenv install
	pipenv install --dev
	pre-commit install
	pre-commit autoupdate


quality_checks:
	isort .
	black .
	pylint --rcfile=pyproject.toml --recursive=y .


integration_test: quality_checks
	bash tests/run_cloud.sh


prefect_server:
	prefect server start


mlflow_server:
	mlflow server


preprocess_data:
	pipenv run python src/preprocess_data.py $(filename) $(season)
# DEFAULT
#	- filename: data/nba_games.parquet
#	- season = 2023 (will be test data)


tune_hyperparams:
	pipenv run python src/rf_optuna.py $(num_trials)
# Default num_trials=20


train:
	pipenv run python src/train.py


predict:
	pipenv run python src/predict.py 2023


build:
	docker build -t nbagameprediction:v1 --platform=linux/arm64 .


deploy: build
	docker run -it -v ./output/:/app/output/ nbagameprediction:v1 2023


# DOCKER COMPOSE SHOULD BE UP AND RUNNING: docker-compose -f monitoring/docker-compose.yaml up
# Prefect must be up and running
monitor:
	pipenv run python monitoring/evidently_monitoring.py

# DOCKER COMPOSE SHOULD BE DOWN AFTER MONITORING: docker-compose -f monitoring/docker-compose.yaml down




# TO RUN:

# make setup
