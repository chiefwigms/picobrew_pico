function delete_file(filename, session_type) {
    delete_server_file(filename, session_type, `${session_type}_history`);
}

function download_session(filename, session_type){
    download_server_session(filename, session_type);
};