import torch
import torch.nn as nn
from core.config import settings


def image_detection(model: nn.Module, frames: list, confidence: float = 0.7) -> dict:
    """
    Detects animals in a list of frames.
    :param model: Model to use for detection.
    :param frames: List of frames to detect animals in.
    :param confidence: Confidence threshold for detection.
    :return: Dictionary containing the number of detections for each animal.
    """

    # Save results of image detection.
    result = {}

    for frame in frames:
        # Get predictions from the specified model.
        output = model(frame)

        # Filter predictions based on confidence.
        findings = output.pandas().xyxy[0]
        findings = findings[findings["confidence"] >= confidence]

        for i in range(len(findings)):
            # Get detected animal's name and normalized surface size.
            animal_name = findings["name"][i]
            animal_surface = (
                (findings["xmax"][i] - findings["xmin"][i])
                * (findings["ymax"][i] - findings["ymin"][i])
                / (frame.shape[0] * frame.shape[1])
            )

            # If animal not seen yet, add it to results.
            if animal_name not in result:
                result[animal_name] = {
                    "count": 0,
                    "surface": 0,
                }

            # Update results.
            result[animal_name]["count"] += 1
            result[animal_name]["surface"] += animal_surface

    # Average out detections over frames.
    for animal in result.keys():
        result[animal]["count"] /= len(frames)  # TODO: Possibly round down/up.
        result[animal]["surface"] /= len(frames)

    return result


if __name__ == "__main__":
    print("This is a module, not a script.")
