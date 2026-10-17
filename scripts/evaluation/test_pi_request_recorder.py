"""Transport checks: preserve streamed responses and capture actual request caps."""
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
import unittest

from pi_request_recorder import LocalRequestRecorder


class RecorderTests(unittest.TestCase):
    def test_stream_and_payload_preserved_without_auth_headers(self):
        observed = {}

        class Upstream(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                observed["body"] = self.rfile.read(int(self.headers["Content-Length"]))
                observed["authorization"] = self.headers.get("Authorization")
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(b'data: {"delta":"ok"}\n\ndata: [DONE]\n\n')
                self.close_connection = True

        upstream = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
        thread = threading.Thread(target=upstream.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as directory:
                payload = {"model": "transport-test-fixture", "max_tokens": 4096,
                           "chat_template_kwargs": {"enable_thinking": True}, "stream": True}
                raw = json.dumps(payload).encode()
                with LocalRequestRecorder(Path(directory), upstream.server_port) as recorder:
                    connection = HTTPConnection("127.0.0.1", recorder.server.server_port, timeout=5)
                    connection.request("POST", "/v1/chat/completions", body=raw,
                                       headers={"Authorization": "test-header-not-recorded"})
                    response = connection.getresponse()
                    self.assertEqual(response.status, 200)
                    self.assertEqual(response.read(), b'data: {"delta":"ok"}\n\ndata: [DONE]\n\n')
                    connection.close()
                    self.assertEqual(observed["body"], raw)
                    self.assertIsNone(observed["authorization"])
                    self.assertEqual(json.loads((Path(directory) / "request-0001.json").read_text()), payload)
                    self.assertEqual(recorder.requests[0]["max_tokens"], 4096)
                    self.assertNotIn("test-header-not-recorded", (Path(directory) / "request-0001.json").read_text())
        finally:
            upstream.shutdown()
            upstream.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
