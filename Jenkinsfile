// Jenkinsfile
pipeline {
    agent {
        // Use a Docker agent with necessary tools pre-installed or install them during the build.
        // A common practice is to build a custom Docker image for your Jenkins agents
        // that includes Python, Docker CLI, kubectl, and other common tools.
        // For simplicity, here we'll use a Python image and install missing tools.
        docker {
            image 'python:3.9-slim-buster'
            // Mount the Docker socket from the host to allow 'docker build' commands inside the container
            args '-v /var/run/docker.sock:/var/run/docker.sock'
            // If kubectl is not on the base image, you can install it here too:
            // args '-v /var/run/docker.sock:/var/run/docker.sock -u root --entrypoint="" -c "apt-get update && apt-get install -y curl && curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl && chmod +x kubectl && mv kubectl /usr/local/bin/ && pip install kubernetes requests && /usr/local/bin/python"'
        }
    }

    environment {
        // Define environment variables. Use Jenkins's 'Global credentials' for sensitive data.
        // Replace 'your_registry' with your actual Docker registry (e.g., 'docker.io/yourusername', 'your-ecr-repo-url')
        DOCKER_REGISTRY = 'your_registry' // <<<<< IMPORTANT: REPLACE THIS
        APP_NAME = 'my-flask-service'
        // For secure Docker login, define a Jenkins 'Username with password' credential with ID 'DOCKER_HUB_CREDENTIALS'
        // For Kubeconfig, define a Jenkins 'Secret file' credential with ID 'KUBECONFIG_SECRET'
        // And make sure the agent has 'kubectl' configured or the Python script handles auth
    }

    stages {
        stage('Checkout') {
            steps {
                // Checkout the SCM (Source Code Management) repository
                // Jenkins automatically handles this for Pipeline jobs linked to SCM
                script {
                    checkout scm
                }
            }
        }

        stage('Install Python Dependencies') {
            steps {
                // Install common Python tools and app dependencies
                sh '''
                    pip install -r requirements.txt
                    pip install flake8 black # Install tools for linting/formatting
                '''
            }
        }

        stage('Lint and Format') {
            steps {
                sh 'flake8 .'
                sh 'black --check .'
            }
        }

        stage('Run Tests') {
            steps {
                sh 'pytest app/tests/'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    // Authenticate to Docker registry
                    // This assumes a Jenkins 'Username with password' credential named 'DOCKER_HUB_CREDENTIALS'
                    // For AWS ECR, it would be 'aws ecr get-login-password | docker login --username AWS --password-stdin ...'
                    withCredentials([usernamePassword(credentialsId: 'DOCKER_HUB_CREDENTIALS', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                        sh "echo \"\$DOCKER_PASS\" | docker login -u \"\$DOCKER_USER\" --password-stdin ${env.DOCKER_REGISTRY}"
                    }
                    
                    sh "docker build -t ${env.DOCKER_REGISTRY}/${env.APP_NAME}:${env.GIT_COMMIT} ."
                    sh "docker push ${env.DOCKER_REGISTRY}/${env.APP_NAME}:${env.GIT_COMMIT}"
                }
            }
        }

        stage('Deploy to Staging') {
            steps {
                script {
                    // Ensure Kubernetes client is installed on the agent
                    // If your 'agent' image doesn't have it, install it here:
                    // sh "pip install kubernetes"

                    // Securely pass Kubeconfig to the script if needed (e.g., for external clusters)
                    // This assumes a Jenkins 'Secret file' credential with ID 'KUBECONFIG_SECRET'
                    // and your deploy_to_k8s.py uses KUBECONFIG env var or a specific path
                    withCredentials([file(credentialsId: 'KUBECONFIG_SECRET', variable: 'KUBECONFIG_PATH')]) {
                         sh "KUBECONFIG=${KUBECONFIG_PATH} python scripts/deploy_to_k8s.py --env staging --image ${env.DOCKER_REGISTRY}/${env.APP_NAME}:${env.GIT_COMMIT} --name ${env.APP_NAME} --namespace default"
                    }
                    // If Kubeconfig is already set up on the agent, simpler:
                    // sh "python scripts/deploy_to_k8s.py --env staging --image ${env.DOCKER_REGISTRY}/${env.APP_NAME}:${env.GIT_COMMIT} --name ${env.APP_NAME} --namespace default"
                }
            }
        }

        stage('Post-Deployment Health Check') {
            steps {
                script {
                    // Wait for Kubernetes service to get an IP/hostname if using LoadBalancer
                    // You might need a more sophisticated wait here, or simply assume it's ready.
                    // For LoadBalancer, the external IP might take a moment to be assigned.
                    echo "Waiting for LoadBalancer IP... (manual step or more sophisticated polling needed here)"
                    sleep 30 // Give LoadBalancer time to provision (adjust as needed)

                    // Construct the URL. Replace with your actual staging URL.
                    // If you have K8s external IP dynamically, fetch it here.
                    // For example, if minikube service is port-forwarded: http://localhost:<port>
                    // Or if a LoadBalancer exposes it: http://<external-ip>/health
                    def stagingUrl = "http://<YOUR_STAGING_K8S_SERVICE_IP_OR_HOSTNAME>/health" // <<< IMPORTANT: REPLACE THIS
                    sh "python scripts/health_check.py --url ${stagingUrl} --expected_status 200 --retries 20 --delay 10"
                }
            }
        }

        stage('Manual Approval for Production') {
            when {
                branch 'main' // Only offer for main branch
            }
            steps {
                timeout(time: 10, unit: 'MINUTES') { // Max 10 minutes to approve
                    input message: 'Proceed to deploy to Production?', ok: 'Deploy Now!'
                }
            }
        }

        stage('Deploy to Production') {
            when {
                expression { return jenkins.node.label == 'production-agent' } // Example: Deploy only to specific agent
                branch 'main'
            }
            steps {
                script {
                    // Similar to staging deployment, but potentially different Kubeconfig, namespace, etc.
                    withCredentials([file(credentialsId: 'PROD_KUBECONFIG_SECRET', variable: 'KUBECONFIG_PATH_PROD')]) {
                        sh "KUBECONFIG=${KUBECONFIG_PATH_PROD} python scripts/deploy_to_k8s.py --env production --image ${env.DOCKER_REGISTRY}/${env.APP_NAME}:${env.GIT_COMMIT} --name ${env.APP_NAME} --namespace production"
                    }
                }
            }
        }
        
        stage('Post-Production Health Check') {
            when {
                branch 'main'
            }
            steps {
                script {
                    echo "Waiting for LoadBalancer IP for Production... (manual step or more sophisticated polling needed here)"
                    sleep 30 // Give LoadBalancer time to provision (adjust as needed)
                    def productionUrl = "http://<YOUR_PRODUCTION_K8S_SERVICE_IP_OR_HOSTNAME>/health" // <<< IMPORTANT: REPLACE THIS
                    sh "python scripts/health_check.py --url ${productionUrl} --expected_status 200 --retries 20 --delay 10"
                }
            }
        }
    }

    post {
        always {
            cleanWs() // Clean up the workspace after the build
        }
        success {
            echo "Pipeline for ${env.APP_NAME} completed successfully!"
            // Add notification steps here (e.g., Slack, Email)
        }
        failure {
            echo "Pipeline for ${env.APP_NAME} failed!"
            // Add notification steps for failure
        }
    }
}