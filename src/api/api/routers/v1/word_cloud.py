from litestar import Controller, get, post
from litestar.datastructures import State
from redis.commands.json.path import Path

from core.guards import authenticate
from models.word_cloud_model import AnimalVoteCount, UserVote, AnimalsCloud


class WordCloudController(Controller):
    path = "/word-cloud"
    tags = ["word-cloud"]

    @get()
    async def list_found_animals(self, state: State) -> list[AnimalsCloud]:
        added_animals = []
        animals = []
        current_batch = state.r.lrange("stream_order", 0, -1)

        for video_key in current_batch:
            data = state.r.json().get(video_key)

            for animal in data["image_detection"]:
                if animal not in added_animals:
                    added_animals.append(animal)
                    animals.append(AnimalsCloud(animal=animal))

            for animal in data["audio_detection"]:
                if animal not in added_animals:
                    added_animals.append(animal)
                    animals.append(AnimalsCloud(animal=animal))

        return animals

    @get(path="/votes")
    async def list_animal_votes(self, state: State) -> list[AnimalVoteCount]:
        votes_dict = {}
        for key in state.r.scan_iter("votes:*"):
            data = state.r.json().get(key)
            for animal in data["voted_animals"]:
                if animal not in votes_dict:
                    votes_dict[animal] = 0
                votes_dict[animal] += 1

        votes_return_list = []
        for key, value in votes_dict.items():
            votes_return_list.append(AnimalVoteCount(animal=key, votes=value))
        return votes_return_list

    @post(path="/votes", guards=[authenticate], security=[{"apiKey": []}])
    async def set_user_vote(self, state: State, data: UserVote) -> UserVote:
        # HACK: For now send random user ID to API
        state.r.json().set(
            f"votes:{data.user_id}",
            Path.root_path(),
            {
                "voted_animals": data.voted_animals,
            },
        )
        state.r.expire(
            f"votes:{data.user_id}",
            1800,
        )
        return data
