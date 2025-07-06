import pytest
from app.main import app as flask_app # Import the Flask app object

@pytest.fixture
def client():
    # Configure the Flask app for testing
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client

def test_hello_world_route(client):
    """Test the root '/' endpoint."""
    response = client.get('/')
    assert response.status_code == 200
    assert "Hello from Flask Microservice!" in response.json['message']

def test_health_check_route(client):
    """Test the '/health' endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'
    assert response.json['app'] == 'my-flask-service'