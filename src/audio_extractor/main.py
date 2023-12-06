import subprocess
import argparse


def extract_audio(arguments):
    subprocess.run(
        ["ffmpeg", "-i", arguments.input, "-q:a", "0", "-map", "a", arguments.output],
        check=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="audio_extractor")

    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output", required=True)

    extract_audio(parser.parse_args())
