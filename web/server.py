import dataclasses
import json
import traceback
from http.server import HTTPServer, SimpleHTTPRequestHandler

import os
import sys
print()
sys.path.append(os.path.join(sys.path[0], '..'))
from lib import Lib

class DataClassJSONEncoder(json.JSONEncoder):
  def default(self, o):
    if dataclasses.is_dataclass(o):
      return dataclasses.asdict(o)
    return super().default(o)

class LibHandler(SimpleHTTPRequestHandler):
  def __init__(self, lib, *args, **kwargs):
    # https://stackoverflow.com/a/71399394/771768
    self.lib = lib
    super().__init__(*args, **kwargs)

  def do_POST(self):
    length = int(self.headers.get('content-length'))
    body = json.loads(self.rfile.read(length))
    text = body['text']
    print(body['rule'], body['text'])

    try:
      result = self.lib.parse(body['text'], ('rule', body['rule']))
      success = True
    except Exception as e:
      result = traceback.format_exc()
      success = False

    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()
  
    body = dict(result=result, success=success)
    self.wfile.write(json.dumps(body, cls=DataClassJSONEncoder).encode('utf-8'))

def run_server():
  lib = Lib(show_parse=True)
  lib.load_defs()
  server_address = ('', 8001)
  httpd = HTTPServer(server_address, lambda *_: LibHandler(lib, *_, directory=sys.path[0]))
  print('serving http://localhost:8001')
  httpd.serve_forever()

if __name__ == '__main__':
  run_server()
