#!/bin/bash
# helper script to deploy infrastructure based on environment
# usage: ./deploy.sh aws create

set -e

environment=${1}
action=${2:-create}
script_location=$(dirname "$0")

# validate input(s)
if [[ -z "$environment" ]]; then
  echo "Positional parameter 'environment' must be provided"
  exit 1
fi

# validate environment variable(s)
if [[ ${environment} == "gcp" ]]; then
    # check for required GCP project ID environment variable
    if [[ -z "$GOOGLE_PROJECT_ID" ]]; then
        echo "Environment variable 'GOOGLE_PROJECT_ID' must be provided"
        exit 1
    fi
    echo "project_id = \"${GOOGLE_PROJECT_ID}\"" > terraform.tfvars
fi
if [[ -z "$ARTIFACTORY_SERVER" ]]; then
    echo "Environment variable 'ARTIFACTORY_SERVER' must be provided"
    exit 1
fi

# install python dependencies
python3 -m venv venv && source venv/bin/activate
pip install -r ${script_location}/requirements.txt

# note: running on linux/unix may require sudo
tf_command=""
if [[ ${USE_SUDO} == "true" ]]; then
    echo "Using sudo, expect a password prompt."
  tf_command+="sudo "
fi
tf_command+="terraform"

# support create|delete|show
if [[ ${action} == "create" ]]; then
    ${tf_command} init ${script_location}/terraform/${environment}
    ${tf_command} apply -auto-approve ${script_location}/terraform/${environment}
    ${tf_command} output -json
    echo $(${tf_command} output -json) | jq .deployment_info.value -r > deployment_info.json
elif [[ ${action} == "delete" ]]; then
    ${tf_command} init ${script_location}/terraform/${environment}
    ${tf_command} destroy -auto-approve ${script_location}/terraform/${environment}
elif [[ ${action} == "show" ]]; then
    ${tf_command} output -json
    echo $(${tf_command} output -json) | jq .deployment_info.value -r > deployment_info.json
else
    echo "Unknown action: ${action}"
    exit 1
fi

# perform any cleanup necessary
deactivate && rm -rf venv


