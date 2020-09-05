import os
from queue import Queue
from threading import Thread
from urllib.parse import urlparse, parse_qs

from bottle import route, run, static_file, request
from youtube_dl import YoutubeDL

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


@route('/play/<video_id>', method='GET')
def serve_webm(video_id):
    return static_file(video_id + '.webm', root='downloaded/webm', mimetype='audio/webm')


@route('/play/<file_format>/<video_id>', method='GET')
def serve_audio(file_format, video_id):
    return static_file(video_id + '.' + file_format, root='downloaded/' + file_format, mimetype='audio/' + file_format)


@route('/api/<apiname>')
def api(apiname):
    try:
        query = request.query
        if apiname == 'info':
            forced = False
            file_format = 'webm'
            if query.get('forced'):
                forced = str2bool(query.get('forced'))
            if query.get('format'):
                file_format = query.get('format')
            return info(query['video'], forced, file_format)
        elif apiname == 'download':
            url = query.video
            yt_queue.put(url)
            return {"success": True, "message": "Video successfully added to download queue."}
    except KeyError:
        return {'status': False, 'message': 'Some parameters is missing!'}


def info(video, forced=False, file_format='webm'):
    can_internal_uri = forced
    allowed_formats = get_allowed_formats()
    conf = adjust_conf(info_conf, file_format)

    if not file_format in allowed_formats:
        return {
            'status': False,
            'message': 'Wrong file format. Supported file formats: ' + ', '.join(allowed_formats)
        }

    if os.path.isfile('./downloaded/' + file_format + '/' + extract_video_id(video) + '.' + file_format):
        forced = False

    with YoutubeDL(conf) as ydl:
        info_dict = ydl.extract_info(video, forced)
        if can_internal_uri:
            url = get_host() + '/play/'
            if file_format in allowed_formats and file_format != 'webm':
                url += file_format + '/'
            url += info_dict.get("id", None)
        else:
            url = info_dict.get("url", None)

        return {
            'status': True,
            'id': info_dict.get("id", None),
            'title': info_dict.get('title', None),
            'description': info_dict.get('description', None),
            'url': url
        }


def adjust_conf(conf=None, file_format='webm'):
    if conf is None:
        conf = {}
    if file_format == 'mp3':
        conf.update({
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '256',
            }]
        })
    elif file_format == 'm4a':
        conf.update({
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
                'preferredquality': '256',
            }]
        })

    conf.update({
        'outtmpl': './downloaded/' + file_format + '/%(id)s.%(ext)s',
    })
    return conf


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


def get_host():
    env = os.environ.get('YOUTUBEDL_API_HOST')
    if not env:
        parts = request.urlparts
        env = parts.scheme + '://' + parts.netloc
    return env


def get_allowed_formats():
    formats = ['webm', 'm4a', 'mp3']
    env = os.environ.get('YOUTUBEDL_API_FORMATS')
    if env:
        formats = env.split(',')
    return formats


yt_queue = Queue()
done = False
thread = Thread(target=work_to_me)
thread.start()

print("Started download thread")

run(host='0.0.0.0', port=1998)

done = True
thread.join()
