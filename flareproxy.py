import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import socket

FLARESOLVERR_URL = os.getenv("FLARESOLVERR_URL", "http://flaresolverr:8191/v1")


class ProxyHTTPRequestHandler(BaseHTTPRequestHandler):

    def handle_get_request(self, url):
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
        url = self.path.replace("http://", "https://")
        self.handle_get_request(url)

    def do_CONNECT(self):
        self.send_response(501, "Not Implemented")
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        error_message = (
            "CONNECT method is not supported by FlareProxy.\n\n"
            "Please use HTTP URLs instead of HTTPS URLs in your client configuration.\n"
            "Example: http://www.discogs.com/sell/release/265683\n\n"
            "The proxy will automatically convert HTTP requests to HTTPS when forwarding to FlareSolverr, "
            "so your requests will still be secure.\n"
        )
        self.wfile.write(error_message.encode("utf-8"))


if __name__ == "__main__":
    server_address = ("", 8080)
    httpd = HTTPServer(server_address, ProxyHTTPRequestHandler)
    print("FlareProxy adapter running on port 8080")
    httpd.serve_forever()
