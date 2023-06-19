import os
import logging
from pytube import YouTube
from config import Config
from threading import Thread


class YoutubeDownload:
    download_path = os.path.abspath(Config.DOWNLOAD_FOLDER_YTB)

    # logging
    logging.basicConfig(level=logging.ERROR, filename=os.path.join(download_path, 'error.log'),
                        format='%(asctime)s %(name)s %(levelname)s:%(message)s')
    logger = logging.getLogger(__name__)

    @classmethod
    def download(cls, url_yt):
        try:
            yt = YouTube(url_yt)
            streams = yt.streams
        except:
            # write the error file with theme, lesson - video not found
            cls.logger.warning(f'Can not get {url_yt}')
            return

        video = None

        # Get link to video
        try:
            video = streams.filter(progressive=True).desc().first()
        except:
            cls.logger.warning(f'Can not get {url_yt}')

        # Download video
        if video:
            video.download(cls.download_path)


class DownloadVideo(Thread):
    def __init__(self, url_video):
        Thread.__init__(self)

        self.url_video = url_video

    def run(self) -> None:
        YoutubeDownload.download(self.url_video)


if __name__ == '__main__':
    YoutubeDownload.download('https://www.youtube.com/watch?v=YbUv4LU8tAA')
