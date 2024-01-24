# personal-wildlife-stream
## Installation
1. To setup Redis see https://redis.io/docs/install/install-redis/ or https://redis.io/docs/install/install-stack/docker/
1. Use anaconda or miniconda to make pytorch installation easier.
1. Create a new environment
1. Install poetry with `pip install poetry`
1. Go to the `src` directory
1. Run `poetry install`
2. Configure the .env files for the folders `api`, `audio_detection`, `image_detection`, `motion_detection`, `stream_downloader`, `stream_ranker`, `video_data_extractor`, `video_streamer`
3. Start all the separate services.
