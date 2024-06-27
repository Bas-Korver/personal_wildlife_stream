import os
from pathlib import Path

from TTS.utils.synthesizer import Synthesizer

from core import settings


def speech_generation(video_path: os.PathLike | str, text: str) -> None:
    """
    Generate text to speech for the given text.

    :param video_path: path to save the generated text to.
    :param text: text to use for text to speech.
    """

    video_path = Path(video_path)
    directory = video_path.parents[0]
    video_name = video_path.stem

    # Generate subtitle file.
    audio_path = directory / f"{video_name}.wav"

    # Load text to speech model.
    synthesizer = Synthesizer(settings.TTS_MODEL_PATH, settings.TTS_CONFIG_PATH)

    # Create text to speech based on provided text.
    wave_narration = synthesizer.tts(text)

    # Save text to speech to provided save path.
    synthesizer.save_wav(wave_narration, audio_path)
