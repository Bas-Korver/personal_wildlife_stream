from pathlib import Path

import pandas as pd
from sqlalchemy import Table, select
from sqlalchemy.event import listens_for

from models.country import Country
from models.stream import Stream, StreamTag


@listens_for(Stream.__table__, "after_create")
def insert_rows(target: Table, connection, **kw) -> None:
    # Load stored countries and tags.
    countries = connection.execute(select(Country.id, Country.name)).fetchall()
    tags = connection.execute(select(StreamTag.id, StreamTag.name)).fetchall()

    # Create conversions function to convert name to associated id.
    country2id = {country[1].lower(): country[0] for country in countries}
    tag2id = {tag[1].lower(): tag[0] for tag in tags}

    # Load streams.csv file, and preprocess it for database.
    df = pd.read_csv(str(Path(__file__).resolve().parent / "../data/streams.csv"))
    df["tag"] = df["tag"].apply(lambda row: tag2id[row.lower()])
    df["country"] = df["country"].apply(lambda row: country2id[row.lower()])

    df = df.rename(columns={"tag": "tag_id", "country": "country_id"})

    # Insert the rows into the database.
    connection.execute(
        target.insert(),
        df.to_dict(orient="records"),
    )
