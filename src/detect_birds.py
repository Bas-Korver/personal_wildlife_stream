import os
import argparse
import json

from audio_extractor.main import extract_audio
from bird_detector.main import detect_birds

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="detect_birds")

    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-c", "--confidence", type=float, default=0.5)

    arguments = parser.parse_args()
    output_file = "audios/" + os.path.basename(arguments.input)
    extract_audio(arguments.input, output_file)

    detection = detect_birds(parser.parse_args())

    print(json.dumps(detection))
