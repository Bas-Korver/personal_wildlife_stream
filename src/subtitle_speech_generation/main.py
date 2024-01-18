from TTS.config import load_config
from TTS.utils.manage import ModelManager
from TTS.utils.synthesizer import Synthesizer
from transformers import pipeline
from PIL import Image


def text_generation(animals_detected, frame):
    # Initialize the image captioning pipeline
    captioner = pipeline("image-to-text", model="Salesforce/blip-image-captioning-base")

    # change frame to format that can be processed by captioner
    image = Image.fromarray(frame)
    #generate text from image
    result_list = captioner(image)
    generated_text = result_list[0]['generated_text']
    # Check if any word in the caption is repeated side by side
    words = generated_text.split()
    repeated_animal = next((word for i, word in enumerate(words[:-1]) if word == words[i + 1]), None)

    # if captioner made an error, use handmade text, otherwise use generated text
    if repeated_animal:
        matching_animals = [animal for animal in animals_detected]
        text = "The animals we can see here are: " + ', '.join(matching_animals)
    else:
        text = generated_text

    return text

def speech_generation(text):
    config = "./config.json"
    model = "./david.pth"

    model_path = model  # Absolute path to the model checkpoint.pth
    config_path = config  # Absolute path to the model config.json

    synthesizer = Synthesizer(
        model_path, config_path
    )
    wavs = synthesizer.tts(text)
    synthesizer.save_wav(wavs, './speech.mp3')