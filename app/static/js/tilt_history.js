function delete_file(filename){
    delete_server_file(filename, 'tilt', 'tilt_history');
};

function download_session(filename){
    download_server_session(filename, 'tilt');
};