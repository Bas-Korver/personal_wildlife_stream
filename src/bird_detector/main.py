import argparse

from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer


def detect_birds(arguments):
    analyzer = Analyzer()

    recording = Recording(
        analyzer,
        arguments.input,
        min_conf=arguments.confidence,
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="birds_detector")

    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-c", "--confidence", type=float, default=0.5)

    detect_birds(parser.parse_args())
