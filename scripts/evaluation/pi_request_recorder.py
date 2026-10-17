"""Record local inference JSON bodies outside Git while forwarding SSE unchanged."""
from contextlib import AbstractContextManager
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading


class LocalRequestRecorder(AbstractContextManager):
    def __init__(self, directory: Path, upstream_port: int = 18080):
        self.directory = directory
        self.upstream_port = upstream_port
        self.requests = []
        self.lock = threading.Lock()

    def __enter__(self):
        owner = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *args):
                pass

            def do_POST(self):
                if self.path != "/v1/chat/completions":
                    self.send_error(404)
                    return
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 16 * 1024 * 1024:
                    self.send_error(413)
                    return
                body = self.rfile.read(length)
                try:
                    payload = json.loads(body)
                except ValueError:
                    self.send_error(400)
                    return
                with owner.lock:
                    index = len(owner.requests) + 1
                    path = owner.directory / f"request-{index:04d}.json"
                    path.write_text(json.dumps(payload, indent=2)+"\n")
                    owner.requests.append({"path": str(path), "model": payload.get("model"),
                                           "max_tokens": payload.get("max_tokens"),
                                           "chat_template_kwargs": payload.get("chat_template_kwargs"),
                                           "temperature": payload.get("temperature"),
                                           "top_p": payload.get("top_p"), "top_k": payload.get("top_k"),
                                           "seed": payload.get("seed")})
                upstream = HTTPConnection("127.0.0.1", owner.upstream_port, timeout=250)
                try:
                    # Never record or forward caller authorization/cookie headers.
                    upstream.request("POST", self.path, body=body,
                                     headers={"Content-Type": "application/json"})
                    response = upstream.getresponse()
                    self.send_response(response.status)
                    for key, value in response.getheaders():
                        if key.lower() not in {"connection", "transfer-encoding", "content-length"}:
                            self.send_header(key, value)
                    self.send_header("Connection", "close")
                    self.end_headers()
                    self.close_connection = True
                    while chunk := response.read1(65536):
                        self.wfile.write(chunk)
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    pass
                finally:
                    upstream.close()

        self.directory.mkdir(parents=True, exist_ok=True)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}/v1"
        return self

    def __exit__(self, *args):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
