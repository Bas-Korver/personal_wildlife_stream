import pandas as pd
from models.country import Country
from sqlalchemy import Table
from sqlalchemy.event import listens_for


@listens_for(Country.__table__, "after_create")
def insert_rows(target: Table, connection, **kw):
    # Load countries.csv file, and preprocess it for database.
    df = pd.read_csv("./countries.csv")
    df = df[["alpha-3", "name"]]
    df = df.rename(columns={"alpha-3": "iso"})

    # Insert the rows into the database.
    connection.execute(
        target.insert(),
        df.to_dict(orient="records"),
    )
