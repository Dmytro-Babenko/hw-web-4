from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib import parse
import mimetypes
import pathlib
import socket
from datetime import datetime
import json
from threading import Thread

UDP_IP = '127.0.0.1'
UDP_PORT = 5000
CL_PORT = 3000


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/contact':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).is_file():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        server = UDP_IP, UDP_PORT
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(data, server)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def send_static(self):
        self.send_response(200)
        mt= mimetypes.guess_type(self.path)
        if mt:
            self.send_header('Content-type', mt[0])
        else:
            self.send_header('Content-type', 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

def run_webclient(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('', CL_PORT)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()

def run_server(ip, port):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        server = ip, port
        sock.bind(server)
        while True:
            data, _ = sock.recvfrom(1024)
            if not data:
                break
            data = {k:v for k, v in [kwarg.split('=') for kwarg in data.decode().split('&')]}
            time = str(datetime.now())
            with open('storage/data.json', 'r') as fh:
                try:
                    dct = json.load(fh)
                except:
                    dct = {}                
            dct[time] = data
            with open('storage/data.json', 'w') as fh:
                json.dump(dct, fh)


if __name__ == '__main__':
    web_client = Thread(target=run_webclient)
    server = Thread(target=run_server, args=(UDP_IP, UDP_PORT))
    web_client.start()
    server.start()
    web_client.join()
    server.join()