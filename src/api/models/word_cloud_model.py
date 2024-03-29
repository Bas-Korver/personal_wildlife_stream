from pydantic import BaseModel


class AnimalVoteCount(BaseModel):
    animal: str
    votes: int


class UserVote(BaseModel):
    user_id: str
    voted_animals: list


class AnimalsCloud(BaseModel):
    animal: str
