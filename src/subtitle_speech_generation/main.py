import numpy as np
from config import Settings
from PIL import Image
from transformers import pipeline
from TTS.config import load_config
from TTS.utils.manage import ModelManager
from TTS.utils.synthesizer import Synthesizer

# Initialize caption model.
CAPTIONER = pipeline("image-to-text", model=Settings.CAPTION_MODEL)  # TODO: Add device.


def text_generation(frame: np.ndarray, stream_result: dict):
    """
    Generate text from a single frame using a captioning model.

    :param frame: frame to generate caption.
    :param stream_result: results from image detection on the specified frame.
    :return: generated caption.
    """

    # Reformat frame so the caption model can use it.
    image = Image.fromarray(frame)

    # Generate text from the image.
    result = CAPTIONER(image)
    generated_text = result[0]["generated_text"]

    # Check if any animals in the caption is repeated.
    words = generated_text.split()
    repeated_animal = next(
        (word for i, word in enumerate(words[:-1]) if word == words[i + 1]), None
    )

    # Set the caption to the generated text.
    caption = generated_text

    # If the caption consists of an error use handmade caption.
    if repeated_animal:
        matching_animals = [animal for animal in stream_result.keys()]
        caption = "The animals we can see here are: " + ", ".join(matching_animals)

    return caption


def speech_generation(text: str, save_path: str):
    """
    Generate text to speech for the given text.

    :param text: text to use for text to speech.
    :param save_path: path to save the generated text to.
    :return: generated text to speech wavs.
    """

    # Load text to speech model.
    synthesizer = Synthesizer(
        Settings.TTS_MODEL_PATH.absolute(), Settings.TTS_CONFIG_PATH.absolute()
    )

    # Create text to speech based on provided text.
    wavs = synthesizer.tts(text)

    # Save text to speech to provided save path.
    synthesizer.save_wav(wavs, save_path)

    return wavs
