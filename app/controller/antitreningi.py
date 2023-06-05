import re
import time
import os
from threading import Thread
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import lxml
import logging
from pytube import YouTube
from config import Config


class Antitreningi:
    _observers = []

    def __init__(self, login, password, url_course):
        self.login = login
        self.password = password
        self.url = 'https://antitreningi.ru'
        self.url_course = url_course
        self.completed_urls = []
        self.pdf_urls = {}
        self.youtube_urls = {}
        self.current_file_name = None
        self.file_set = set()  # None

        download_path = os.path.join(os.path.abspath(Config.DOWNLOAD_FOLDER), re.findall(r'\d+', url_course)[0])

        if not os.path.exists(download_path):
            os.makedirs(download_path)

        self.download_path = download_path

        # logging
        logging.basicConfig(level=logging.WARNING, filename=os.path.join(self.download_path, 'error.log'),
                            format='%(asctime)s %(name)s %(levelname)s:%(message)s')
        self.logger = logging.getLogger(__name__)

        driver_options = webdriver.ChromeOptions()
        driver_options.binary = "/usr/bin/google-chrome-stable"
        driver_options.binary_location = "/usr/bin/google-chrome-stable"
        # ver 109+
        driver_options.add_argument("--headless=new")
        # ver 96-108
        # driver_options.add_argument("--headless=chrome")
        driver_options.add_argument("--no-sandbox")
        driver_options.add_argument("--disable-dev-shm-usage")
        driver_options.add_argument("--disable-extensions")
        driver_options.add_argument("disable-infobars")
        driver_options.add_argument('--ignore-certificate-errors')
        driver_options.add_experimental_option('prefs', {
            "download.default_directory": self.download_path,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True
        })

        self.driver = webdriver.Chrome(options=driver_options)

    def run(self):
        self._do_login()
        self._get_lessons_urls()
        self._get_youtube_and_pdf_urls()
        self._download_pdf()
        self._download_youtube()

    def _do_login(self):
        self.driver.get(self.url + '/login')
        login_xpath = '//*[@id="react_root_loginPage"]/div[1]/div[2]/div/div/div/div/div/form/div/div[2]/div/div/input'
        login_input = self.driver.find_element(By.XPATH, login_xpath)
        login_input.clear()
        login_input.send_keys(self.login)
        time.sleep(.5)

        passwd_xpath = '//*[@id="react_root_loginPage"]/div[1]/div[2]/div/div/div/div/div/form/div/div[3]/div/div/input'
        password_input = self.driver.find_element(By.XPATH, passwd_xpath)
        password_input.clear()
        password_input.send_keys(self.password)
        time.sleep(.5)

        btn_xpath = '//*[@id="react_root_loginPage"]/div[1]/div[2]/div/div/div/div/div/form/div/div[4]/div[1]/button'
        button_login = self.driver.find_element(By.XPATH, btn_xpath)
        button_login.click()
        time.sleep(3)

    def _get_lessons_urls(self):

        # Get course html
        self.driver.get(self.url_course)
        time.sleep(3)

        # Expand the list of lessons starting from the second
        expand_button = self.driver.find_elements(By.CLASS_NAME, "MuiIconButton-label")
        for btn in expand_button[1:]:
            btn.click()
            time.sleep(1)

        course_html = self.driver.page_source

        bs = BeautifulSoup(course_html, 'lxml')

        for tag_a in bs.find('div', id="react-lessons").find_all('a', href=True):
            if tag_a.text.endswith('Зачет'):
                self.completed_urls.append(self.url + tag_a['href'])

    def _get_youtube_and_pdf_urls(self):

        for url in self.completed_urls[:]:
            self.driver.get(url)
            bs = BeautifulSoup(self.driver.page_source, 'lxml')

            module_title = bs.find('a', class_="theme_name").get_text().replace('\n', '').strip().split('.')
            lesson_title = bs.find('h3', class_="lesson_name").get_text().replace('\n', '').strip().split('.')

            all_lesson_tags_a = bs.find('div', class_="b-lesson__text").find_all('a', href=True)

            # for pdf downloads
            for number_tag, tag_a in enumerate(all_lesson_tags_a):
                base_file_name = f'{module_title[0].replace(" ", "_")}_{lesson_title[0].replace(" ", "_")}'
                if len(all_lesson_tags_a) == 1:
                    file_name = f'{base_file_name}_{tag_a.get_text()}'
                else:
                    file_name = f'{base_file_name}_{number_tag}_{tag_a.get_text()}'

                # Restrict length of filename
                if len(file_name) > 54:
                    extention = file_name.split('.')[1]
                    file_name = f'{file_name[:50]}.{extention}'

                # for other urls from external sites
                if tag_a['href'].startswith('http'):
                    # self.pdf_urls.update({f'{base_file_name}_{number_tag}_Презентация.pdf': tag_a['href']})
                    file_name = f'{base_file_name}_{number_tag}_Презентация.pdf'
                    file_url = tag_a['href']
                else:
                    # tag_a['href'] start with /...
                    # self.pdf_urls.update({file_name: self.url + tag_a['href']})
                    file_url = self.url + tag_a['href']

                # Check downloaded file. If no - update dict
                if not os.path.exists(os.path.join(self.download_path, file_name)):
                    self.pdf_urls.update({file_name: file_url})


            # For YouTube downloads
            if bs.find('div', class_="b-lesson__text").find_next('div').get('data-oembed-url'):
                # Restrict length of filename
                lesson_title = '_'.join(item.strip().replace(" ", "_")[:30] for item in lesson_title)

                file_name = f'{module_title[0].replace(" ", "_")}_{lesson_title}.mp4'

                # Check downloaded file. If no - update dict
                if not os.path.exists(os.path.join(self.download_path, file_name)):
                    self.youtube_urls.update(
                        {file_name: bs.find('div', class_="b-lesson__text").find_next('div').get('data-oembed-url')}
                    )

    def _download_pdf(self):
        for name_pdf, url_pdf in self.pdf_urls.items():
            # for notify subscriber
            self.file_set = set(os.listdir(self.download_path))
            self.current_file_name = os.path.join(self.download_path, name_pdf)

            try:
                self.driver.get(url_pdf)
                time.sleep(10)
                self.notify()
            except:
                self.logger.warning(f'Can not get {url_pdf} for {name_pdf}')

    def _download_youtube(self):

        for name_yt, url_yt in self.youtube_urls.items():
            try:
                yt = YouTube(url_yt)
                streams = yt.streams
            except:
                # write the error file with theme, lesson - video not found
                return
            # for notify subscriber
            self.file_set = set(os.listdir(self.download_path))

            video = None

            # Get link to video
            try:
                video = streams.filter(progressive=True).desc().first()
            except:
                self.logger.warning(f'Can not get {url_yt} for {name_yt}')

            # Download video
            if video:
                video.download(self.download_path)

            if video is None:
                self.logger.warning(f'Can not get video {url_yt} for {name_yt}')
            else:
                # video was downloaded and need to rename
                self.current_file_name = os.path.join(self.download_path, name_yt)
                self.notify()

    def attach(self, observer):
        self._observers.append(observer)

    def detach(self, observer):
        self._observers.remove(observer)

    def notify(self):
        for observer in self._observers:
            observer.update(self)


class RenameFileObserver:
    @staticmethod
    def update(subjact: Antitreningi):
        """ check directory for a new file and rename it """
        new_file_set = set(os.listdir(subjact.download_path))
        downloaded_file = new_file_set - subjact.file_set
        if len(downloaded_file) == 1:
            os.rename(os.path.join(subjact.download_path, downloaded_file.pop()), subjact.current_file_name)
            time.sleep(2)


class DownloadMaterials(Thread):
    def __init__(self, login, password, url_course):
        Thread.__init__(self)
        self.login = login
        self.password = password
        self.url_course = url_course

    def run(self) -> None:
        course = Antitreningi(self.login, self.password, self.url_course)
        rename_observer = RenameFileObserver()
        course.attach(rename_observer)
        course.run()
        course.detach(rename_observer)
