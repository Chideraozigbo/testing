#!/bin/bash

# Exit script on any error
set -e

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

# Upgrade pip
pip install --upgrade pip

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
echo "To start the Airflow web server, run: airflow webserver --port 8080"
echo "To start the Airflow scheduler, run: airflow scheduler"
