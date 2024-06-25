import os
from datetime import datetime

from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer

from core import settings


def detect_birds(
    audio_path: os.PathLike | str, latitude: float, longitude: float
) -> list[dict]:
    """
    Detect birds in an audio file.
    :param audio_path: Path to audio file.
    :param latitude: Latitude of the audio file.
    :param longitude: Longitude of the audio file.
    :return: List dictionaries containing detections.
    """
    analyzer = Analyzer()

    recording = Recording(
        analyzer,
        audio_path,
        lat=latitude,
        lon=longitude,
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
