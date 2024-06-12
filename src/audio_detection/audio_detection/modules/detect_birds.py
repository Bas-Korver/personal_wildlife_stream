import os
from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer
from datetime import datetime

from core.config import settings


def detect_birds(audio_path: str | os.PathLike) -> list[dict]:
    """
    Detect birds in an audio file.
    :param audio_path: Path to audio file.
    :return: List dictionaries containing detections.
    """
    analyzer = Analyzer()

    # TODO: longitude and latitude to birdnetlib.Recording for a more accurate result.
    recording = Recording(
        analyzer,
        audio_path,
        date=datetime.today(),
        min_conf=settings.MODEL_CONFIDENCE,
    )

    recording.analyze()

    return list(
        map(
            lambda detection: {
                **detection,
                "label": "bird",
                "label_specific": detection["label"],
            },
            recording.detections,
        )
    )
