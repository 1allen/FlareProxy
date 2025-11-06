import unittest
import json
from unittest.mock import patch, MagicMock, Mock, PropertyMock
from io import BytesIO


class MockFlareSolverrResponse:
    """Mock response from FlareSolverr"""
    def __init__(self, status_code=200, response_text="Mock response"):
        self.status_code = status_code
        self._json_data = {
            "solution": {
                "response": response_text
            }
        }

    def json(self):
        return self._json_data


class TestFlareProxy(unittest.TestCase):
    """Basic smoke tests for FlareProxy"""

    @patch('flareproxy.requests.post')
    def test_do_GET_constructs_url_correctly(self, mock_post):
        """Test that GET requests construct URLs correctly"""
        from flareproxy import ProxyHTTPRequestHandler

        mock_post.return_value = MockFlareSolverrResponse()

        with patch.object(ProxyHTTPRequestHandler, '__init__', lambda self, *args, **kwargs: None):
            handler = ProxyHTTPRequestHandler(None, None, None)
            handler.path = "http://example.com/test"
            handler.command = "GET"

            handler.send_response = MagicMock()
            handler.send_header = MagicMock()
            handler.end_headers = MagicMock()
            handler.wfile = MagicMock()

            handler.do_GET()

            mock_post.assert_called_once()
            call_args = mock_post.call_args
            self.assertEqual(call_args[1]['json']['url'], 'https://example.com/test')
            self.assertEqual(call_args[1]['json']['cmd'], 'request.get')

    @patch('flareproxy.requests.post')
    def test_do_CONNECT_returns_error(self, mock_post):
        """Test that CONNECT requests return a 501 Not Implemented error"""
        from flareproxy import ProxyHTTPRequestHandler

        with patch.object(ProxyHTTPRequestHandler, '__init__', lambda self, *args, **kwargs: None):
            handler = ProxyHTTPRequestHandler(None, None, None)
            handler.path = "www.example.com:443"
            handler.command = "CONNECT"

            handler.send_response = MagicMock()
            handler.send_header = MagicMock()
            handler.end_headers = MagicMock()
            handler.wfile = MagicMock()

            handler.do_CONNECT()

            handler.send_response.assert_called_with(501, "Not Implemented")
            handler.send_header.assert_called_with("Content-Type", "text/plain; charset=utf-8")
            handler.wfile.write.assert_called_once()

            written_data = handler.wfile.write.call_args[0][0]
            error_message = written_data.decode('utf-8')
            self.assertIn('CONNECT method is not supported', error_message)
            self.assertIn('use HTTP URLs instead', error_message)

            mock_post.assert_not_called()

    @patch('flareproxy.requests.post')
    def test_handle_get_request_includes_timeout(self, mock_post):
        """Test that requests include maxTimeout parameter"""
        from flareproxy import ProxyHTTPRequestHandler

        mock_post.return_value = MockFlareSolverrResponse()

        with patch.object(ProxyHTTPRequestHandler, '__init__', lambda self, *args, **kwargs: None):
            handler = ProxyHTTPRequestHandler(None, None, None)

            handler.send_response = MagicMock()
            handler.send_header = MagicMock()
            handler.end_headers = MagicMock()
            handler.wfile = MagicMock()

            handler.handle_get_request("https://example.com")

            call_args = mock_post.call_args
            self.assertEqual(call_args[1]['json']['maxTimeout'], 60000)

    @patch('flareproxy.requests.post')
    def test_error_handling(self, mock_post):
        """Test that errors are handled gracefully"""
        from flareproxy import ProxyHTTPRequestHandler

        mock_post.side_effect = Exception("Connection failed")

        with patch.object(ProxyHTTPRequestHandler, '__init__', lambda self, *args, **kwargs: None):
            handler = ProxyHTTPRequestHandler(None, None, None)

            handler.send_response = MagicMock()
            handler.send_header = MagicMock()
            handler.end_headers = MagicMock()
            handler.wfile = MagicMock()

            handler.handle_get_request("https://example.com")

            handler.send_response.assert_called_with(500)
            handler.wfile.write.assert_called_once()

            written_data = handler.wfile.write.call_args[0][0]
            error_json = json.loads(written_data.decode('utf-8'))
            self.assertIn('error', error_json)
            self.assertIn('Connection failed', error_json['error'])

    @patch('flareproxy.requests.post')
    def test_flaresolverr_url_env_default(self, mock_post):
        """Test that FLARESOLVERR_URL defaults correctly"""
        import flareproxy

        self.assertEqual(flareproxy.FLARESOLVERR_URL, "http://flaresolverr:8191/v1")


if __name__ == '__main__':
    unittest.main()