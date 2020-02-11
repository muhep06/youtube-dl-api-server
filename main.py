from bottle import route, run, static_file, request
from youtube_dl import YoutubeDL
from queue import Queue
from threading import Thread
import json

app_defaults = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '256',
    }],
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
def stylesheets_map(filename):
    return static_file(filename, root='public/js', mimetype='application/javascript')


@route('/<language>', method='GET')
def frontend_download(language):
    return static_file('index.html', root='public/lang/'+language, mimetype='text/html')


@route('/api/<apiname>')
def api(apiname):
    try:
        query = request.query
        if apiname == 'info':
            return info(query['video'])
        elif apiname == 'download':
            url = query.video
            yt_queue.put(url)
            return {"success": True, "message": "Video successfully added to download queue."}
    except KeyError:
        return {'status': False, 'message': 'Some parameters is missing!'}


def info(video):
    with YoutubeDL(app_defaults) as ydl:
        info_dict = ydl.extract_info(video, download=False)
        return {
            'status': True,
            'id': info_dict.get("id", None),
            'title': info_dict.get('title', None),
            'description': info_dict.get('description', None),
            'url': info_dict.get("url", None)
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


yt_queue = Queue()
done = False
thread = Thread(target=work_to_me)
thread.start()

print("Started download thread")

run(host='0.0.0.0', port=1998)

done = True
thread.join()