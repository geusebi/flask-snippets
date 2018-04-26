from flask import send_file, request, current_app
from warning import warn


def xsend_file(*args, uri=None, **kwargs):
    """
    Send a file with X-Sendfile.

    The configuration setting `app.use_x_sendfile' is honoured,
    if it's not True, then sends the file with `flask.send_file'.

    The server should provide the header `X-Sendfile-Capable'.
    The content of this header is the header name to use in the response
    (usually `X-Sendfile'). Accepted values are:

        X-Sendfile-Capable: X-Sendfile
        X-Sendfile-Capable: X-Accel-Redirect
        X-Sendfile-Capable: X-LIGHTTPD-send-file

    In case `X-Sendfile-Capable' is missing or is invalid a warning is
    issued and the response is served as is (through `flask.send_file').

    Accepts the same parameters of `flask.send_file' and an optional
    parameter, `uri'. If it is defined, then, it will be sent
    back to the server as the `filepath' to serve (the original filepath
    will be used for everything else).

    Ratio:
        1. If x-sendfile is enabled but the server is not able to handle
        it, then an empty response is served almost silently,
        2. some servers do not understand the usual `X-Sendfile' header,
        3. Nginx expect a URI in the header, not a file path.

    An example Nginx configuration might look like this:
        location /download/some/file {
            proxy_set_header X-Sendfile-Capable X-Accel-Redirect;
            proxy_pass URL;
        }

        location /protected/ {
            internal;
            add_header X-Sendfile-Served Yes;
            alias /path/to/protected/directory/;
        }

    An example flask view might look like this: 
        @app.route('/')
        def serve_large_file():
            file = "some_large_file"
            return xsend_file(
                f"/path/to/protected/directory/{file}",
                uri=f"/protected/{file}"
                )

    Turning on or off `flask.use_x_sendfile' shouldn't stop the server
    from serving content. To be sure that the file is actually served
    through the correct nginx rule, the header X-Sendfile-Served is set
    to Yes and exposed to the client.
    """

    response = send_file(*args, **kwargs)

    if not current_app.use_x_sendfile:
        return response

    req_headers = request.headers
    res_headers = response.headers

    header_name = req_headers.get("X-Sendfile-Capable")
    server_capable = header_name.lower() in (
        "x-sendfile",
        "x-accel-redirect",
        "x-lighttpd-send-file",
        )

    if server_capable:
        file = res_headers.pop("X-Sendfile")
        if uri is not None:
            file = uri
        if file is not None:
            res_headers.set(header_name, file)
    else:
        warn("Invalid `X-Sendfile-Capable' header in request.")

    return response

