from litestar import Controller, get, post

from core.guards import authenticate
from db.redis_connection import RedisConnection
from models.word_cloud_model import AnimalVoteCount, UserVote, AnimalsCloud

r = RedisConnection().get_redis_client()


class WordCloudController(Controller):
    path = "/word-cloud"
    tags = ["word-cloud"]

    @get()
    async def list_found_animals(self) -> list[AnimalsCloud]:
        animals = []
        for key in r.scan_iter("animals:*"):
            dict_value = r.json().get(key)
            animals.append(AnimalsCloud(animal=dict_value["organism"]))

        return animals

    @get(path="/votes")
    async def list_animal_votes(self) -> list[AnimalVoteCount]:
        votes_dict = {}
        for key in r.scan_iter("votes:*"):
            dict_value = r.json().get(key)
            if dict_value["votedOrganism"] not in votes_dict:
                votes_dict[dict_value["votedOrganism"]] = 0
            votes_dict[dict_value["votedOrganism"]] += 1

        votes_return_list = []
        for key, value in votes_dict.items():
            votes_return_list.append(AnimalVoteCount(animal=key, votes=value))
        return votes_return_list

    @post(path="/votes", guards=[authenticate], security=[{"apiKey": []}])
    async def set_user_vote(self, data: UserVote) -> UserVote:
        return data
