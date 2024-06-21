#!/bin/bash

# Exit script on any error
set -e

# Update package list and install necessary dependencies
sudo apt update
sudo apt install -y python3 python3-venv python3-pip curl

# Create and activate a virtual environment
python3 -m venv airflow_env
source airflow_env/bin/activate

# Upgrade pip
pip install --upgrade pip

# Define Airflow version and Python version
AIRFLOW_VERSION=2.6.3
PYTHON_VERSION=$(python --version | cut -d " " -f 2 | cut -d "." -f 1-2)
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

# Verify if the constraint URL is correct
if curl --output /dev/null --silent --head --fail "$CONSTRAINT_URL"; then
    echo "Constraint URL is valid, proceeding with installation..."
else
    echo "Constraint URL is not found. Exiting..."
    exit 1
fi

# Install Apache Airflow
pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"

# Initialize the Airflow database
airflow db init

# Create an Airflow admin user
airflow users create \
    --username datadom \
    --password admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email chideraozigbo@gmail.com

echo "Apache Airflow installation and setup complete."
echo "To start the Airflow web server, run: source airflow_env/bin/activate && airflow webserver --port 8080"
echo "To start the Airflow scheduler, run: source airflow_env/bin/activate && airflow scheduler"
