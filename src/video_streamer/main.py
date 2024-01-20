from vidgear.gears import WriteGear, CamGear
import time
import cv2

# YouTube Stream Key and URL (Replace with your actual Stream Key)
stream_key = "fz7r-tbdx-swd0-m1vk-44j5"
VIDEO_SOURCE = "C:/Users/Bas_K/source/repos/personal_wildlife_stream/src/streams/yPSYdCWRWFA/20240119_154914.mp4"
output_params = {
    "-input_framerate": 30,
    "-output_dimensions": (1920, 1080),
    "-disable_force_termination": True,
}

# Configure WriteGear (use FFmpeg parameters for streaming)
writer = WriteGear(
    output="output.mp4",
    logging=True,
    **output_params,
)

i = 0
streaming = True
# loop over
while streaming:
    # Get current time to see duration each iteration.
    duration = time.time()

    # Load chosen video.
    stream = CamGear(source=VIDEO_SOURCE, logging=True).start()

    # Stream chosen video.
    while True:
        # Read frames from stream.
        frame = stream.read()

        # Check if a frame is available, otherwise video is over and break from this loop.
        if frame is None:
            break

        # Write frame to the stream.
        writer.write(frame)

        # Show output frames of the stream.
        cv2.imshow("Stream output", frame)

        # Check for 'q' key if pressed then stop the stream.
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            streaming = False
            break

        time.sleep(1 / 30)

    # Safely close video stream
    stream.stop()

    print(time.time() - duration)
    print(i)
    i += 1
    if i >= 10:
        break

cv2.destroyAllWindows()

# safely close writer
writer.close()
