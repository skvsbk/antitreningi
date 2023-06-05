from flask import Flask, render_template, request, flash, redirect, url_for
import re
import config
from app.controller.antitreningi import DownloadMaterials


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
            files_url = '\\\\fsrv\\Обмен\\ОБУЧЕНИЕ_ПЕРСОНАЛА\\antitreningi\\' + re.findall(r"\d+", url_course)[0]
            return redirect(url_for('finish', files_url=files_url))
        else:
            flash('Все поля должны быть заполнены!', 'info')

    return render_template('antitreningi.html')


@app.route('/finish/<files_url>', methods=['GET'])
def finish(files_url):
    return render_template('finish.html', files_url=files_url)
