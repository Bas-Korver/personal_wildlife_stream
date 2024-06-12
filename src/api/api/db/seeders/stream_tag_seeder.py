import pandas as pd
from models.stream import StreamTag
from sqlalchemy import Table
from sqlalchemy.event import listens_for


@listens_for(StreamTag.__table__, "after_create")
def insert_rows(target: Table, connection, **kw):
    # Load streams.csv file, and preprocess it for database.
    df = pd.read_csv("./data/streams.csv")
    tags = [{"name": tag, "model": None} for tag in df["tag"].unique()]

    # Insert the rows into the database.
    connection.execute(
        target.insert(),
        tags,
    ) 
