from bottle import route, run, static_file, request
from youtube_dl import YoutubeDL
from queue import Queue
from threading import Thread
import json
import os
from urllib.parse import urlparse, parse_qs

app_defaults = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '256',
    }],
}

info_conf = {
    'format': 'bestaudio/best',
    'outtmpl': './downloaded/%(id)s.%(ext)s',
}


@route('/', method='GET')
def index():
    return static_file('index.html', root='public', mimetype='text/html')


@route('/css/<filename:re:.*\.css>', method='GET')
def stylesheets(filename):
    return static_file(filename, root='public/css', mimetype='text/css')


@route('/css/<filename:re:.*\.map>', method='GET')
def stylesheets_map(filename):
    return static_file(filename, root='public/css', mimetype='application/octet-stream')


@route('/js/<filename:re:.*\.js>', method='GET')
def javascripts(filename):
    return static_file(filename, root='public/js', mimetype='application/javascript')


@route('/<language>', method='GET')
def frontend_download(language):
    return static_file('index.html', root='public/lang/' + language, mimetype='text/html')


@route('/play/<vide_id>', method='GET')
def serve_webm(vide_id):
    return static_file(vide_id + '.webm', root='downloaded', mimetype='audio/webm')


@route('/api/<apiname>')
def api(apiname):
    try:
        query = request.query
        if apiname == 'info':
            forced = False
            if query.get('forced'):
                forced = str2bool(query.get('forced'))
            return info(query['video'], forced)
        elif apiname == 'download':
            url = query.video
            yt_queue.put(url)
            return {"success": True, "message": "Video successfully added to download queue."}
    except KeyError:
        return {'status': False, 'message': 'Some parameters is missing!'}


def info(video, forced=False):
    download = forced
    if os.path.isfile('./downloaded/' + extract_video_id(video) + '.webm'):
        download = False

    with YoutubeDL(info_conf) as ydl:
        info_dict = ydl.extract_info(video, download)
        parts = request.urlparts
        if forced:
            url = getHost() + '/play/' + info_dict.get("id", None)
        else:
            url = info_dict.get("url", None)

        return {
            'status': True,
            'id': info_dict.get("id", None),
            'title': info_dict.get('title', None),
            'description': info_dict.get('description', None),
            'url': url
        }


def download(url):
    with YoutubeDL(app_defaults) as ydl:
        ydl.download([url])


@route('/api/queue', method='GET')
def q_size():
    return {"status": True, "size": list(yt_queue.queue)}


def work_to_me():
    while not done:
        url = yt_queue.get()
        download(url)
        yt_queue.task_done()


def extract_video_id(url):
    url_data = urlparse(url)
    query = parse_qs(url_data.query)
    return query["v"][0]


def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


def getHost():
    env = os.environ.get('YOUTUBEDL_API_HOST')
    if not env:
        parts = request.urlparts
        env = parts.scheme + '://' + parts.netloc
    return env


yt_queue = Queue()
done = False
thread = Thread(target=work_to_me)
thread.start()

print("Started download thread")

run(host='0.0.0.0', port=1998)

done = True
thread.join()
