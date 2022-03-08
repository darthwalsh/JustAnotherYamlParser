from http.server import HTTPServer, SimpleHTTPRequestHandler
import json

import os
import sys
print()
sys.path.append(os.path.join(sys.path[0], '..'))
from lib import Lib

class LibHandler(SimpleHTTPRequestHandler):
  def __init__(self, lib, *args, **kwargs):
    # https://stackoverflow.com/a/71399394/771768
    self.lib = lib
    super().__init__(*args, **kwargs)

  def _set_headers(self):
    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()

  def do_POST(self):
    length = int(self.headers.get('content-length'))
    message = self.rfile.read(length).decode('utf-8')
    print(message)

    self._set_headers()
    self.wfile.write(json.dumps({'success': True}).encode('utf-8'))

def run_server():
  lib = Lib()
  lib.load_defs()
  server_address = ('', 8001)
  httpd = HTTPServer(server_address, lambda *_: LibHandler(lib, *_, directory=sys.path[0]))
  print('serving http://localhost:8001')
  httpd.serve_forever()

if __name__ == '__main__':
  run_server()
