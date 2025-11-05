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

        # Setup mock response
        mock_post.return_value = MockFlareSolverrResponse()

        # Create a minimal handler by mocking __init__
        with patch.object(ProxyHTTPRequestHandler, '__init__', lambda self, *args, **kwargs: None):
            handler = ProxyHTTPRequestHandler(None, None, None)
            handler.path = "http://example.com/test"
            handler.command = "GET"

            # Mock the response methods
            handler.send_response = MagicMock()
            handler.send_header = MagicMock()
            handler.end_headers = MagicMock()
            handler.wfile = MagicMock()

            # Execute
            handler.do_GET()

            # Verify FlareSolverr was called with correct URL
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            self.assertEqual(call_args[1]['json']['url'], 'https://example.com/test')
            self.assertEqual(call_args[1]['json']['cmd'], 'request.get')

    @patch('flareproxy.requests.post')
    def test_do_CONNECT_reads_full_request(self, mock_post):
        """Test that CONNECT requests read and construct full URL with path"""
        from flareproxy import ProxyHTTPRequestHandler

        # Setup mock response
        mock_post.return_value = MockFlareSolverrResponse()

        # Create a minimal handler
        with patch.object(ProxyHTTPRequestHandler, '__init__', lambda self, *args, **kwargs: None):
            handler = ProxyHTTPRequestHandler(None, None, None)
            handler.path = "www.example.com:443"
            handler.command = "CONNECT"

            # Mock the HTTP request that comes after CONNECT
            request_data = b"GET /test/path HTTP/1.1\r\nHost: www.example.com\r\n\r\n"
            handler.rfile = BytesIO(request_data)

            # Mock the response methods
            handler.send_response = MagicMock()
            handler.send_header = MagicMock()
            handler.end_headers = MagicMock()
            handler.wfile = MagicMock()

            # Execute
            handler.do_CONNECT()

            # Verify FlareSolverr was called with full URL including path
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            self.assertEqual(call_args[1]['json']['url'], 'https://www.example.com/test/path')
            self.assertEqual(call_args[1]['json']['cmd'], 'request.get')

    @patch('flareproxy.requests.post')
    def test_handle_get_request_includes_timeout(self, mock_post):
        """Test that requests include maxTimeout parameter"""
        from flareproxy import ProxyHTTPRequestHandler

        # Setup mock response
        mock_post.return_value = MockFlareSolverrResponse()

        # Create a minimal handler
        with patch.object(ProxyHTTPRequestHandler, '__init__', lambda self, *args, **kwargs: None):
            handler = ProxyHTTPRequestHandler(None, None, None)

            # Mock the response methods
            handler.send_response = MagicMock()
            handler.send_header = MagicMock()
            handler.end_headers = MagicMock()
            handler.wfile = MagicMock()

            # Execute
            handler.handle_get_request("https://example.com")

            # Verify timeout is included
            call_args = mock_post.call_args
            self.assertEqual(call_args[1]['json']['maxTimeout'], 60000)

    @patch('flareproxy.requests.post')
    def test_error_handling(self, mock_post):
        """Test that errors are handled gracefully"""
        from flareproxy import ProxyHTTPRequestHandler

        # Setup mock to raise an exception
        mock_post.side_effect = Exception("Connection failed")

        # Create a minimal handler
        with patch.object(ProxyHTTPRequestHandler, '__init__', lambda self, *args, **kwargs: None):
            handler = ProxyHTTPRequestHandler(None, None, None)

            # Mock the response methods
            handler.send_response = MagicMock()
            handler.send_header = MagicMock()
            handler.end_headers = MagicMock()
            handler.wfile = MagicMock()

            # Execute
            handler.handle_get_request("https://example.com")

            # Verify error response is sent
            handler.send_response.assert_called_with(500)
            handler.wfile.write.assert_called_once()

            # Verify error message contains the exception
            written_data = handler.wfile.write.call_args[0][0]
            error_json = json.loads(written_data.decode('utf-8'))
            self.assertIn('error', error_json)
            self.assertIn('Connection failed', error_json['error'])

    @patch('flareproxy.requests.post')
    def test_connect_with_query_parameters(self, mock_post):
        """Test that CONNECT requests preserve query parameters"""
        from flareproxy import ProxyHTTPRequestHandler

        # Setup mock response
        mock_post.return_value = MockFlareSolverrResponse()

        # Create a minimal handler
        with patch.object(ProxyHTTPRequestHandler, '__init__', lambda self, *args, **kwargs: None):
            handler = ProxyHTTPRequestHandler(None, None, None)
            handler.path = "www.example.com:443"
            handler.command = "CONNECT"

            # Mock the HTTP request with query parameters
            request_data = b"GET /search?q=test&page=2 HTTP/1.1\r\nHost: www.example.com\r\n\r\n"
            handler.rfile = BytesIO(request_data)

            # Mock the response methods
            handler.send_response = MagicMock()
            handler.send_header = MagicMock()
            handler.end_headers = MagicMock()
            handler.wfile = MagicMock()

            # Execute
            handler.do_CONNECT()

            # Verify URL includes query parameters
            call_args = mock_post.call_args
            self.assertEqual(call_args[1]['json']['url'], 'https://www.example.com/search?q=test&page=2')

    @patch('flareproxy.requests.post')
    def test_flaresolverr_url_env_default(self, mock_post):
        """Test that FLARESOLVERR_URL defaults correctly"""
        import flareproxy
        # Verify the default URL is set
        self.assertEqual(flareproxy.FLARESOLVERR_URL, "http://flaresolverr:8191/v1")


if __name__ == '__main__':
    unittest.main()