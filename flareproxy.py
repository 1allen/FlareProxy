import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import socket

FLARESOLVERR_URL = os.getenv("FLARESOLVERR_URL", "http://flaresolverr:8191/v1")


class ProxyHTTPRequestHandler(BaseHTTPRequestHandler):

    def handle_get_request(self, url):
        """Send request to FlareSolverr and return response."""
        try:
            headers = {"Content-Type": "application/json"}
            data = {
                "cmd": "request.get",
                "url": url,
                "maxTimeout": 60000
            }

            response = requests.post(FLARESOLVERR_URL, headers=headers, json=data)
            json_response = response.json()

            self.send_response(response.status_code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(bytes(json_response.get("solution", {}).get("response", ""), "utf-8"))

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            error_message = json.dumps({"error": str(e)})
            self.wfile.write(error_message.encode("utf-8"))

    def do_GET(self):
        """Handle GET requests."""
        url = self.path.replace("http://", "https://")
        self.handle_get_request(url)

    def do_CONNECT(self):
        """Handle CONNECT requests by reading the subsequent HTTP request."""
        try:
            host_port = self.path
            host = host_port.split(':')[0]

            self.send_response(200, 'Connection Established')
            self.end_headers()

            request_line = self.rfile.readline().decode('utf-8').strip()

            if request_line:
                parts = request_line.split(' ')
                if len(parts) >= 2:
                    method = parts[0]
                    path = parts[1]

                    url = f"https://{host}{path}"

                    while True:
                        header_line = self.rfile.readline().decode('utf-8').strip()
                        if not header_line:
                            break

                    self.handle_get_request(url)
                else:
                    self.send_error(400, "Bad Request")
            else:
                self.send_error(400, "Bad Request")

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            error_message = json.dumps({"error": str(e)})
            self.wfile.write(error_message.encode("utf-8"))


if __name__ == "__main__":
    server_address = ("", 8080)
    httpd = HTTPServer(server_address, ProxyHTTPRequestHandler)
    print("FlareProxy adapter running on port 8080")
    httpd.serve_forever()
