import numpy as np
from PIL import Image
from transformers import pipeline

from core import settings

# Initialize caption model.
captioner = pipeline(
    "image-to-text", model=settings.CAPTION_MODEL, device=settings.DEVICE
)  # TODO: Add device.


def text_generation(frame: np.ndarray, stream_result: dict) -> str:
    """
    Generate text from a single frame using a captioning model.

    :param frame: frame to generate caption.
    :param stream_result: results from image detection on the specified frame.
    :return: generated caption.
    """

    # Reformat frame so the caption model can use it.
    image = Image.fromarray(frame)

    # Generate text from the image.
    result = captioner(image)
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
