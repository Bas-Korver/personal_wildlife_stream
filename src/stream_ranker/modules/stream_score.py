from core.config import settings


def stream_score(image_detection, audio_detection):
    # Initialize stream score.
    score = 0

    # Decrease the score if it was often chosen recently.
    decrease_score = 0  # TODO: Decrease score if chosen often save in Redis.
    decrease_score = max(
        [decrease_score, decrease_score - settings.PENALIZE_STREAM_AFTER_TURNS]
    )  # TODO: Only penalize streams after being chosen a specified amount of times.

    # Negate decrease score on calculated score.
    score -= settings.DECREASE_SCORE_WEIGHT * decrease_score

    # Go through audio detection results.
    # TODO: Audio detection ranking.

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
        )  # TODO: maybe device a better scoring heuristic.

    return score
