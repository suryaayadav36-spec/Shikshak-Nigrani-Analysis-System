import sys
import os
from pathlib import Path
import json
from urllib.parse import urlencode

# Add parent directory to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

os.environ['FLASK_ENV'] = 'production'

from app import app
from werkzeug.serving import WSGIRequestHandler

def handler(event, context):
    """Netlify Functions handler for Flask WSGI app"""
    try:
        # Parse the event
        method = event.get('httpMethod', 'GET').upper()
        path = event.get('path', '/')
        body = event.get('body', '')
        headers = event.get('headers', {})
        query_string = event.get('rawQueryString', '')
        
        # Prepare the environ dict for WSGI
        environ = {
            'REQUEST_METHOD': method,
            'SCRIPT_NAME': '',
            'PATH_INFO': path,
            'QUERY_STRING': query_string,
            'CONTENT_TYPE': headers.get('content-type', 'text/html'),
            'CONTENT_LENGTH': headers.get('content-length', '0'),
            'SERVER_NAME': headers.get('host', 'localhost').split(':')[0],
            'SERVER_PORT': headers.get('host', 'localhost').split(':')[1] if ':' in headers.get('host', '') else '443',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'https',
            'wsgi.input': None,
            'wsgi.errors': None,
            'wsgi.multithread': False,
            'wsgi.multiprocess': True,
            'wsgi.run_once': False,
        }
        
        # Add headers to environ
        for key, value in headers.items():
            key = key.upper().replace('-', '_')
            if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                key = f'HTTP_{key}'
            environ[key] = value
        
        # Call the WSGI app
        response_data = []
        response_status = None
        response_headers = {}
        
        def start_response(status, response_headers_list):
            nonlocal response_status, response_headers
            response_status = int(status.split()[0])
            response_headers = dict(response_headers_list)
        
        # Handle the request
        with app.test_request_context(
            method=method,
            path=path,
            query_string=query_string,
            data=body,
            headers=headers
        ):
            response = app.full_dispatch_request()
            status_code = response.status_code
            body_text = response.get_data(as_text=True)
            headers_dict = dict(response.headers)
        
        return {
            'statusCode': status_code,
            'body': body_text,
            'headers': headers_dict,
            'isBase64Encoded': False
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {'Content-Type': 'application/json'}
        }
