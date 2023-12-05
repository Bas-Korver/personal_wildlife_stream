from pydantic import BaseModel


class AnimalVoteCount(BaseModel):
    animal: str
    votes: int


class UserVote(BaseModel):
    user_id: str
    voted_animal: str


class AnimalsCloud(BaseModel):
    animal: str
