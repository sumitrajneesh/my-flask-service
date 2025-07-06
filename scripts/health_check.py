import argparse
import requests
import time

def perform_health_check(url: str, expected_status: int, retries: int = 5, delay: int = 10):
    """
    Performs an HTTP health check on the given URL.
    Retries multiple times if the check fails.
    """
    print(f"Starting health check for URL: {url} (expected status: {expected_status})")
    for i in range(retries):
        try:
            response = requests.get(url, timeout=5) # 5 second timeout for request
            print(f"Attempt {i+1}: Received status code {response.status_code} from {url}")
            if response.status_code == expected_status:
                print(f"Health check successful! Service is healthy.")
                return True
            else:
                print(f"Health check failed: Expected {expected_status}, got {response.status_code}. Retrying in {delay} seconds...")
        except requests.exceptions.ConnectionError as e:
            print(f"Attempt {i+1}: Connection error: {e}. Service not reachable yet. Retrying in {delay} seconds...")
        except requests.exceptions.Timeout:
            print(f"Attempt {i+1}: Request timed out. Retrying in {delay} seconds...")
        except Exception as e:
            print(f"Attempt {i+1}: An unexpected error occurred: {e}. Retrying in {delay} seconds...")
        
        time.sleep(delay)
    
    print(f"Health check failed after {retries} attempts. Service might not be healthy.")
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Perform HTTP health check.")
    parser.add_argument("--url", required=True, help="URL to check (e.g., http://localhost:5000/health)")
    parser.add_argument("--expected_status", type=int, default=200, help="Expected HTTP status code")
    parser.add_argument("--retries", type=int, default=10, help="Number of retry attempts")
    parser.add_argument("--delay", type=int, default=15, help="Delay between retries in seconds")

    args = parser.parse_args()

    if not perform_health_check(args.url, args.expected_status, args.retries, args.delay):
        exit(1) # Exit with error code if health check fails