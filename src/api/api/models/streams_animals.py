from db.postgres import Base
from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.types import Integer

Table(
    "streams_animals",
    Base.metadata,
    Column("stream_id", ForeignKey("streams.id"), primary_key=True),
    Column("animal_id", ForeignKey("animals.id"), primary_key=True),
    Column("count", Integer, default=0),
)
