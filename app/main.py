from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def hello_world():
    return jsonify(message="Hello from Flask Microservice!"), 200

@app.route('/health')
def health_check():
    # In a real app, you'd check database connections, external services, etc.
    return jsonify(status="healthy", app="my-flask-service", version="1.0.0"), 200

if __name__ == '__main__':
    # Use Gunicorn for production, Flask's built-in server for local dev
    from gunicorn.app.base import BaseApplication

    class FlaskApplication(BaseApplication):
        def __init__(self, app, options=None):
            self.application = app
            self.options = options or {}
            super().__init__()

        def load_config(self):
            for key, value in self.options.items():
                if key in self.cfg.settings and value is not None:
                    self.cfg.set(key.lower(), value)

        def load(self):
            return self.application

    options = {
        'bind': '%s:%s' % ('0.0.0.0', '5000'),
        'workers': 4, # You can adjust this based on your server's cores
    }
    FlaskApplication(app, options).run()