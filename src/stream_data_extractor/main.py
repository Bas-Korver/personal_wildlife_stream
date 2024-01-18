import subprocess
import argparse


def extract_audio(input_file, output_file):
    subprocess.run(
        ["ffmpeg", "-i", input_file, "-q:a", "0", "-map", "a", output_file],
        check=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="audio_extractor")

    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output", required=True)

    arguments = parser.parse_args()

    extract_audio(arguments.input, arguments.output)
