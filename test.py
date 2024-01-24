import pathlib
import time
import subprocess

video_file = "C:/Users/Bas_K/source/repos/personal_wildlife_stream/src/streams/DsNtwGJXTTs/20240123_102224.mp4"  # Absolute file name!
output_file = None

print(f"ffmpeg -f concat -safe 0 -i {video_file} -c copy -f mpegts output.ts")

# Very true
while True:
    intermediate_file_path = f"intermediate_{time.strftime('%Y%m%d_%H%M%S')}.ts"

    if output_file is None:
        # Create new output file with this intermediate file.
        output_file = "output.ts"
        # subprocess.run(f"ffmpeg -i {video_file} -c copy {output_file}")
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                video_file,
                "-c",
                "copy",
                output_file,
            ]
        )

        print("Created new output file.")
    else:
        # Create intermediate files.
        # Extension file.
        subprocess.run(
            [
                "ffmpeg",
                "-i",
                video_file,
                "-c",
                "copy",
                intermediate_file_path,
            ]
        )

        # Original stream.
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                output_file,
                "-c",
                "copy",
                "intermediate_stream.ts",
            ]
        )

        print("Created intermediate file.")

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                f"concat:{intermediate_file_path}|intermediate_stream.ts",
                "-c",
                "copy",
                f"{output_file}",
            ]
        )
        print("Concatenated output file.")

        print("Remove intermediate file.")
        pathlib.Path(intermediate_file_path).unlink()

    print("Sleep 10s")

    time.sleep(1)

#
