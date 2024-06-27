import subprocess
import time


file = "C:/Users/Bas_K/source/repos/9d306401-30c8-48aa-9fb3-8723265c43fc/20240627_220405.mp4"
audio_path = "C:/Users/Bas_K/source/repos/9d306401-30c8-48aa-9fb3-8723265c43fc/test.wav"
sub = "C:/Users/Bas_K/source/repos/9d306401-30c8-48aa-9fb3-8723265c43fc/sub.srt"
escaped_path = sub.replace("\\", "/").replace(":", "\\:")

subprocess.run(
    [
        "ffmpeg",
        "-i",
        str(file),
        "-i",
        audio_path,
        "-filter_complex",
        # "[0:a][1:a]amerge=inputs=2[a]",
        "[0:a]apad[aud1];[1:a]apad[aud2];[aud1][aud2]amerge=inputs=2[a]",
        "-map",
        "0:v",
        "-map",
        "[a]",
        "-c:v",
        "libx264",
        "-ac",
        "2",
        "-t",
        "10",
        "-vf",
        f"subtitles='{escaped_path}'",
        "C:/Users/Bas_K/source/repos/9d306401-30c8-48aa-9fb3-8723265c43fc/out.mp4",
    ]
)
# while True:
#     start_time = time.time()
#     subprocess.run(
#         [
#             "ffmpeg",
#             "-re",
#             "-i",
#             file,
#             "-vf",
#             f"subtitles='{escaped_path}'",
#             "-r",
#             "30",
#             "-g",
#             "120",
#             "-c:v",
#             "libx264",
#             "-preset",
#             "superfast",
#             "-b:v",
#             "1000k",
#             "-maxrate",
#             "1500k",
#             "-bufsize",
#             "10M",
#             "-c:a",
#             "aac",
#             "-b:a",
#             "128k",
#             "-f",
#             "flv",
#             "rtmp://a.rtmp.youtube.com/live2/fz7r-tbdx-swd0-m1vk-44j5",
#         ]
#     )
#     print("Time taken: ", time.time() - start_time)
