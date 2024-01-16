import torch


# Initialize model.
DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
MODEL = torch.hub.load("ultralytics/yolov5", "custom", "./model_weights.pt")
MODEL.to(DEVICE)


def image_detection(frames: list, confidence: float = 0.2):
    """

    :param confidence:
    :param frames:
    """
    # Save results of image detection.
    result = {}

    for frame in frames:
        # Get predictions from the specified model.
        output = MODEL(frame)

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

    # TODO: Save

    return result
