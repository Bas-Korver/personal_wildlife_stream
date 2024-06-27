import numpy as np
from core import settings
from db import RedisConnection
from gensim.downloader import load
from gensim.models import KeyedVectors
from sklearn.metrics.pairwise import cosine_similarity

r = RedisConnection().get_redis_client()
model_path = '../GoogleNews-vectors-negative300.bin'
word2vec_model = KeyedVectors.load_word2vec_format(model_path, binary=True)
topic = np.zeros(word2vec_model.vector_size)
n_streams_topic = 5
topic_list = []

def stream_score(stream: str, image_detection: dict, audio_detection: dict) -> float:
    """
    Calculate the score of a stream.
    :param stream: YouTube ID of the stream.
    :param image_detection: dict of image detection results.
    :param audio_detection: dict of audio detection results.
    :return: score of the video file.
    """

    # Initialize stream score.
    score = 0

    # Decrease the score if it was often chosen recently.
    decrease_score = r.json().get("stream_information")[stream]
    decrease_score = max(
        [decrease_score, decrease_score - settings.PENALIZE_STREAM_AFTER_TURNS]
    )

    # Negate decrease score on calculated score.
    score -= settings.DECREASE_SCORE_WEIGHT * decrease_score

    # Go through audio detection results.
    for animal in audio_detection.keys():
        confidence = audio_detection[animal]["confidence"]

        score += settings.AUDIO_CONFIDENCE_WEIGHT * confidence

    votes_dict = {}
    total_votes = 0
    for key in r.scan_iter("votes:*"):
        data = r.json().get(key)
        for animal in data["voted_animals"]:
            if animal not in votes_dict:
                votes_dict[animal] = 0
            votes_dict[animal] += 1
            total_votes += 1

    # Go through image detection results.
    for animal in image_detection.keys():
        if animal in votes_dict:
            priority = votes_dict[animal] / total_votes
        else:
            priority = 0
        count = image_detection[animal]["count"]
        surface = image_detection[animal]["surface"]

        # Calculate stream score for this animal.
        score += (
            (settings.USER_VOTE_WEIGHT * priority)
            + (settings.ANIMAL_COUNT_WEIGHT * count)
            + (settings.ANIMAL_SURFACE_WEIGHT * surface)
        )

    # Add to score based on how well it fits the topic


    return score
