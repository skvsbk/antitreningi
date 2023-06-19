from flask import Flask, render_template, request, flash, redirect, url_for
import re
import config
from app.controller.antitreningi import DownloadMaterials
from app.controller.youtube import DownloadVideo


app = Flask(__name__)

app.config.from_object(config.Config)


@app.route('/', methods=['GET'])
def antitreningi():
    args = request.args
    if args.get('get_course', default='', type=str) == 'Скачать':
        login = args.get('login')
        password = args.get('password')
        url_course = args.get('url_course')
        if login != '' and password != '' and url_course != '':
            thread_a = DownloadMaterials(login, password, url_course)
            thread_a.start()
            title1 = 'Скачивание видео и pdf из https://antitreningi.ru/'
            title2 = 'Это займет несколько минут. Скачанный курс появится здесь:'
            files_url = '\\\\fsrv\\Обмен\\ОБУЧЕНИЕ_ПЕРСОНАЛА\\antitreningi\\' + re.findall(r"\d+", url_course)[0]
            # return redirect(url_for('finish', title1=title1, title2=title2, files_url=files_url))
            return render_template('finish.html', title1=title1, title2=title2, files_url=files_url)
        else:
            flash('Все поля должны быть заполнены!', 'info')

    return render_template('antitreningi.html')


@app.route('/ytb', methods=['GET'])
def youtube():
    args = request.args
    if args.get('get_video', default='', type=str) == 'Скачать':
        url_video = args.get('url_video')
        if url_video != '':
            thread_a = DownloadVideo(url_video)
            thread_a.start()
            title1 = 'Скачивание видео из YouTube'
            title2 = 'Это займет несколько минут. Скачанное видео появится здесь:'
            files_url = '\\\\fsrv\\Обмен\\ОБУЧЕНИЕ_ПЕРСОНАЛА\\youtube\\'
            # return redirect(url_for('finish', title1=title1, title2=title2, files_url=files_url))
            return render_template('finish.html', title1=title1, title2=title2, files_url=files_url)
        else:
            flash('Все поля должны быть заполнены!', 'info')

    return render_template('youtube.html')

# @app.route('/finish/<title1>/<title2>/<files_url>', methods=['GET'])
# def finish(title1, title2, files_url):
#     return render_template('finish.html', title1=title1, title2=title2, files_url=files_url)
