FROM python:3.11-slim

RUN pip3 install --upgrade pip
RUN pip3 install requests
RUN pip3 install pipenv --force-reinstall

WORKDIR /app

VOLUME /app/output

COPY ["Pipfile", "Pipfile.lock", "./"]

RUN pipenv install --system --deploy

COPY ["models/rf_nba.bin", "./models/rf_nba.bin"]
COPY ["models/", "./models"]
COPY ["src/",  "./src"]
COPY ["data/output", "./data/output"]
COPY ["data/nba_games.parquet", "./data/nba_games.parquet"]

ENV PYTHONPATH=${PYTHONPATH}:${PWD}

ENTRYPOINT [ "python", "src/predict.py"]

# docker build -t nbagameprediction:v1 --platform=linux/arm64 .
# docker run -it -v ./output/:/app/output/ nbagameprediction:v1 2023
