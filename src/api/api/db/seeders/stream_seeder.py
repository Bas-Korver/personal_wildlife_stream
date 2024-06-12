import pandas as pd
from models.country import Country
from models.stream import Stream, StreamTag
from sqlalchemy import Table, select
from sqlalchemy.event import listens_for


@listens_for(Stream.__table__, "after_create")
def insert_rows(target: Table, connection, **kw):
    # Load stored countries and tags.
    countries = connection.execute(select[Country.iso, Country.name])
    tags = connection.execute(select[StreamTag.id, StreamTag.name])

    # Create conversions function to convert name to associated id.
    country2id = {country["name"].lower(): country["iso"] for country in countries}
    tag2id = {tag["name"].lower(): tag["id"] for tag in tags}

    # Load streams.csv file, and preprocess it for database.
    df = pd.read_csv("./data/streams.csv")
    df["tag"] = df["tag"].apply(lambda row: tag2id[row.lower()])
    df["country"] = df["country"].apply(lambda row: country2id[row.lower()])

    df = df.rename(columns={"tag": "tag_id", "country": "country_id"})

    # Insert the rows into the database.
    connection.execute(
        target.insert(),
        df.to_dict(orient="records"),
    )
