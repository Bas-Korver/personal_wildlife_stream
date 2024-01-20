import asyncio
import time

import cv2
import numpy as np
from vidgear.gears import WriteGear

YOUTUBE_STREAM_KEY = "fz7r-tbdx-swd0-m1vk-44j5"  # Make configurable.

STREAM_PARAMS = {
    "-input_framerate": 30,
}


def start_livestream():
    # Create a stream.
    streamer = WriteGear(
        output="output.mp4",
        logging=True,
        **STREAM_PARAMS,
    )

    end_timestamp = time.time() + 10
    i = 0

    # Create livestream.
    while time.time() <= end_timestamp:
        i += 1
        print("[!]", i)

        # Check if next set of videos are processed.
        if False is True:  # TODO: Change if statement.
            # Get frames from the highest ranking stream and stream them.
            video_frames = []  # TODO: Get frames

            # Set this set of videos as the current set of videos.
            # TODO

            # Set that this video has been streamed.
            # TODO

            # Delete previous set of videos.

            for frame in video_frames:
                # streamer.write(frame)
                # asyncio.sleep(1 / STREAM_PARAMS["-input_framerate"]) # TODO: Possibly add small delay if it does not space out the frames properly.
                pass

            # Sleep for X seconds based on the amount of frames added.
            asyncio.sleep(
                max((0, (len(video_frames) / STREAM_PARAMS["-input_framerate"]) - 1))
            )  # TODO: If earlier delay used, remove this one.

            # Go to next iteration.
            continue

        # If the next set of videos are not processed yet check the current set of videos that are processed
        # and get a lower ranking stream not shown yet.
        if False is True:  # TODO: Change if statement.
            # Get frames from the highest ranking stream that has not been shown yet.
            video_frames = []  # TODO: Get frames

            # Set that this video has been streamed.
            # TODO

            for frame in video_frames:
                # streamer.write(frame)
                # asyncio.sleep(1 / STREAM_PARAMS["-input_framerate"]) # TODO: Possibly add small delay if it does not space out the frames properly.
                pass

            # Sleep for X seconds based on the amount of frames added.
            asyncio.sleep(
                max((0, (len(video_frames) / STREAM_PARAMS["-input_framerate"]) - 1))
            )  # TODO: If earlier delay used, remove this one.

            # Go to next iteration.
            continue

        # If there are no processed videos display a placeholder frame saying the stream will return shortly.
        frame = np.zeros((1080, 1920, 3))
        text = "Returning shortly"
        font_scale = 2
        cv2.putText(
            frame,
            text,
            (
                (
                    frame.shape[1]
                    - cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)[0][
                        0
                    ]
                )
                // 2,
                (
                    frame.shape[0]
                    + cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)[0][
                        1
                    ]
                )
                // 2,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        # Stream the placeholder frame.
        streamer.write(frame, rgb_mode=True)
        time.sleep(1 / STREAM_PARAMS["-input_framerate"])

        # TODO: Remove debug
        cv2.imshow("Output Frame", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    # If the stream is over terminate the stream.
    streamer.close()

    cv2.destroyAllWindows()


if __name__ == "__main__":
    start_livestream()
