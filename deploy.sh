#!/bin/bash

# Install local dependency
pip install -r requirements.txt -t ./

# Zip the package
zip -r ./myDeploymentPackage.zip . -x README.md -x "*.git*"

# Push to AWS
aws lambda update-function-code \
  --function-name pmc-timecard \
  --zip-file fileb://myDeploymentPackage.zip

rm ./myDeploymentPackage.zip 