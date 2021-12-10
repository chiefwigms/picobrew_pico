function delete_file(filename, session_type) {
    delete_server_file(filename, session_type, `${session_type}_history`);
}

function download_session(filename, session_type){
    download_server_session(filename, session_type);
};

const fetchMore = async (url) => {
    let headers = new Headers()
    headers.append("X-Requested-With", "XMLHttpRequest")
    return fetch(url, { headers })
}

let end = false;

async function loadMore() {
    let scrollElement = document.getElementById("accordion");
    let $loader = $("#load-more");
    let $spinner = $("#loading");

    $spinner.removeClass("d-none");
    $loader.hide();
    let offset = scrollElement.children.length
    let url = `${window.location.href}?offset=${offset}`;
    let req = await fetchMore(url);
    if (req.ok) {
        let body = await req.text();
        // Be careful of XSS if you do this. Make sure
        // you remove all possible sources of XSS.
        scrollElement.innerHTML += body;
        
        // dynamically load scripts within loaded content (html5 doesn't allow embedding <script> within innerHTML)
        var doc = document.createElement( 'html' );
        doc.innerHTML = body;
        var arr = doc.getElementsByTagName("script")
        for (var n = 0; n < arr.length; n++)
            eval(arr[n].innerHTML) //run script inside div
        
        $loader.show();
    } else {
        // If it returns a 404, stop requesting new items
        end = true;
        $loader.hide();
    }
    $spinner.addClass("d-none");
}

document.addEventListener("DOMContentLoaded", () => {
    let sentinel = document.getElementById("sentinel");

    let observer = new IntersectionObserver(async (entries) => {
        entry = entries[0];
        if (!end && entry.intersectionRatio > 0) {
            loadMore(end);
        }
    })
    observer.observe(sentinel);
})

$(function() {
    $("#load-more").click(function() {
        loadMore(end);
    })
});