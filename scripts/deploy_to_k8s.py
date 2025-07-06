import argparse
import os
import time
from kubernetes import client, config
from kubernetes.client.rest import ApiException

def deploy_to_k8s(env: str, image: str, deployment_name: str, namespace: str = "default"):
    """
    Updates a Kubernetes deployment with a new image.
    Applies the deployment and service manifests if they don't exist.
    """
    try:
        # Load Kubernetes configuration
        # This will try in-cluster config, then KUBECONFIG env var, then default ~/.kube/config
        config.load_kube_config()
        # Alternatively, for in-cluster: config.load_incluster_config()
    except Exception as e:
        print(f"Error loading Kubernetes config: {e}")
        print("Ensure you have a valid ~/.kube/config or are running inside a cluster.")
        exit(1)

    api_apps = client.AppsV1Api()
    api_core = client.CoreV1Api()

    # --- Apply Kubernetes manifests (Deployment and Service) ---
    # In a real scenario, you'd use a templating engine (Helm, Kustomize)
    # or ensure these are already created. For simplicity, we'll
    # apply them first, and then patch the image.
    try:
        # Load and apply deployment manifest
        with open(os.path.join(os.path.dirname(__file__), '../k8s/deployment.yaml'), 'r') as f:
            dep_manifest = client.ApiClient().read_yaml(f)
        
        # Override image in the loaded manifest for the first time or if it's new
        dep_manifest['spec']['template']['spec']['containers'][0]['image'] = image
        
        try:
            api_apps.read_namespaced_deployment(name=deployment_name, namespace=namespace)
            print(f"Deployment '{deployment_name}' already exists. Patching...")
            api_apps.patch_namespaced_deployment(name=deployment_name, namespace=namespace, body=dep_manifest)
        except ApiException as e:
            if e.status == 404:
                print(f"Deployment '{deployment_name}' not found. Creating...")
                api_apps.create_namespaced_deployment(body=dep_manifest, namespace=namespace)
            else:
                raise

        # Load and apply service manifest
        with open(os.path.join(os.path.dirname(__file__), '../k8s/service.yaml'), 'r') as f:
            svc_manifest = client.ApiClient().read_yaml(f)
        
        try:
            api_core.read_namespaced_service(name=svc_manifest['metadata']['name'], namespace=namespace)
            print(f"Service '{svc_manifest['metadata']['name']}' already exists. Skipping creation.")
            # We don't patch service unless there are changes in ports etc.
        except ApiException as e:
            if e.status == 404:
                print(f"Service '{svc_manifest['metadata']['name']}' not found. Creating...")
                api_core.create_namespaced_service(body=svc_manifest, namespace=namespace)
            else:
                raise

    except Exception as e:
        print(f"Error applying Kubernetes manifests: {e}")
        exit(1)

    # --- Wait for Deployment Rollout ---
    print(f"Waiting for deployment '{deployment_name}' to roll out...")
    
    # Simple polling for rollout status
    timeout_seconds = 300 # 5 minutes
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        try:
            resp = api_apps.read_namespaced_deployment_status(name=deployment_name, namespace=namespace)
            if resp.status.unavailable_replicas is None or resp.status.unavailable_replicas == 0:
                print(f"Deployment '{deployment_name}' successfully rolled out.")
                return True
        except ApiException as e:
            print(f"Error reading deployment status: {e}")
        
        time.sleep(10) # Check every 10 seconds

    print(f"Deployment '{deployment_name}' did not roll out within {timeout_seconds} seconds. Check logs.")
    exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy microservice to Kubernetes.")
    parser.add_argument("--env", required=True, help="Deployment environment (e.g., staging, production)")
    parser.add_argument("--image", required=True, help="Docker image to deploy (e.g., myregistry/my-flask-service:latest)")
    parser.add_argument("--name", default="my-flask-service", help="Name of the Kubernetes deployment")
    parser.add_argument("--namespace", default="default", help="Kubernetes namespace")

    args = parser.parse_args()

    print(f"Attempting to deploy image '{args.image}' to '{args.env}' environment in namespace '{args.namespace}'...")
    deploy_to_k8s(args.env, args.image, args.name, args.namespace)
    print("Deployment script finished.")