$(document).ready(function () {
    let video_url = $(".form-control.dwn-input");
    let video_dwn = $(".btn.btn-primary.dwn-bt");
    video_dwn.click(function () {
        if (validateYouTubeUrl(video_url.val())) {
            $.getJSON('/api/download?video='+video_url.val(), function (data) {
                if (data.status) {
                    alert(data.message);
                } else {
                    alert(data.message);
                }
            });
        } else {
            alert("This is not a valid YouTube Video Url");
        }
    });
    download_queue();
});

function validateYouTubeUrl(url) {
    if (url !== undefined || url !== '') {
        let regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=|\?v=)([^#\&\?]*).*/;
        let match = url.match(regExp);
        return !!(match && match[2].length === 11);
    }
}

function download_queue() {
    setInterval(function () {
        let que = $('#queue');
        $.getJSON('/api/queue', function (data) {
            if (data.status) {
                que.text(data.size.length);
            }
        });
    }, 1000);
}