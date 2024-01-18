from config import settings


def rank_stream(stream_result):
    # Initialize stream score.
    stream_score = 0

    # Decrease the score if it was often chosen recently.
    decrease_score = 0  # TODO: Decrease score if chosen often save in Redis.
    decrease_score = max(
        [decrease_score, decrease_score - settings.PENALIZE_STREAM_AFTER_TURNS]
    )  # TODO: Only penalize streams after being chosen a specified amount of times.

    # Go through results to calculate score.
    for animal in stream_result.keys():
        priority = 1  # TODO: Add priority based on user votes, percentage of votes.
        count = stream_result[animal]["count"]
        surface = stream_result[animal]["surface"]

        # Calculate stream score for this animal.
        stream_score += (
            (settings.USER_VOTE_WEIGHT * priority)
            + (settings.ANIMAL_COUNT_WEIGHT * count)
            + (settings.ANIMAL_SURFACE_WEIGHT * surface)
        )  # TODO: maybe device a better scoring heuristic.

    # Negate decrease score on calculated score.
    stream_score -= settings.DECREASE_SCORE_WEIGHT * decrease_score

    # TODO: Save

    return stream_score
