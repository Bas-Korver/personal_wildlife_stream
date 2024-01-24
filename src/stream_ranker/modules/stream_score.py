from core.config import settings
from db.redis_connection import RedisConnection

r = RedisConnection().get_redis_client()


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

    # Go through image detection results.
    for animal in image_detection.keys():
        priority = 1  # TODO: Add priority based on user votes, percentage of votes.
        count = image_detection[animal]["count"]
        surface = image_detection[animal]["surface"]

        # Calculate stream score for this animal.
        score += (
            (settings.USER_VOTE_WEIGHT * priority)
            + (settings.ANIMAL_COUNT_WEIGHT * count)
            + (settings.ANIMAL_SURFACE_WEIGHT * surface)
        )

    return score
