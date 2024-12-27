from dotenv import load_dotenv
import logging
import logging.handlers
import os
from wsgiref.simple_server import make_server, WSGIServer
from socketserver import ThreadingMixIn

# Load environment variables from .env file
load_dotenv()

# Configuration
LOG_FILE = os.getenv('LOG_FILE', '/tmp/sample-app/sample-app.log')
PORT = int(os.getenv('PORT', 8000))
MAX_LOG_SIZE = int(os.getenv('MAX_LOG_SIZE', 1048576))

# Logging Configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=5)
console_handler = logging.StreamHandler()

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# HTML Templates
WELCOME_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Welcome</title>
</head>
<body>
  <h1>Congratulations!</h1>
  <p>Your Docker Container is running in Elastic Beanstalk on AWS.</p>
</body>
</html>
"""

ERROR_404_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>404 Not Found</title>
</head>
<body>
  <h1>404 Not Found</h1>
  <p>The requested resource was not found on this server.</p>
</body>
</html>
"""

ERROR_500_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>500 Internal Server Error</title>
</head>
<body>
  <h1>500 Internal Server Error</h1>
  <p>Something went wrong while processing your request. Please try again later.</p>
</body>
</html>
"""

# Response Helpers
def generate_response(status, body, content_type='text/html'):
    """Generate an HTTP response."""
    headers = [('Content-Type', content_type)]
    return status, headers, body.encode()

# WSGI Application
def application(environ, start_response):
    try:
        path = environ.get('PATH_INFO', '/')
        method = environ.get('REQUEST_METHOD', 'GET')
        client_ip = environ.get('REMOTE_ADDR', 'Unknown')

        logger.info("Received %s request for %s from %s", method, path, client_ip)

        if method == 'POST':
            if path == '/':
                try:
                    request_body_size = int(environ.get('CONTENT_LENGTH', 0))
                    request_body = environ['wsgi.input'].read(request_body_size).decode('utf-8')
                    logger.info("POST to / with body: %s", request_body)
                except (TypeError, ValueError) as e:
                    logger.warning("Error reading POST body: %s", str(e))
                return generate_response('200 OK', "")
            elif path == '/scheduled':
                task_name = environ.get('HTTP_X_AWS_SQSD_TASKNAME', 'Unknown')
                scheduled_at = environ.get('HTTP_X_AWS_SQSD_SCHEDULED_AT', 'Unknown')
                logger.info("Scheduled task: %s at %s", task_name, scheduled_at)

                # Example of handling different tasks
                if task_name == 'task1':
                    logger.info("Executing task1...")
                    # Add the task-specific logic here (e.g., background processing)
                    response_body = f"Task {task_name} processed successfully."
                else:
                    logger.warning("Unknown task: %s", task_name)
                    response_body = f"Unknown task: {task_name}"

                return generate_response('200 OK', response_body)
            else:
                logger.warning("Unhandled POST path: %s", path)
                return generate_response('404 Not Found', ERROR_404_HTML)
        elif method == 'GET':
            if path == '/':
                return generate_response('200 OK', WELCOME_HTML)
            else:
                logger.warning("Unhandled GET path: %s", path)
                return generate_response('404 Not Found', ERROR_404_HTML)
        else:
            logger.warning("Unhandled HTTP method: %s", method)
            return generate_response('405 Method Not Allowed', "<h1>405 Method Not Allowed</h1>")

    except Exception as e:
        logger.error("Unhandled exception: %s", str(e))
        return generate_response('500 Internal Server Error', ERROR_500_HTML)

    finally:
        logger.info("Request processing completed.")

# Threaded Server
class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    pass

if __name__ == '__main__':
    httpd = make_server('', PORT, application, ThreadingWSGIServer)
    logger.info(f"Serving on port {PORT}...")
    try:
        httpd.serve_forever()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down server gracefully.")
    except Exception as e:
        logger.error("Error while running server: %s", str(e))
