# pmc-timecard



## Deployment

```
./deploy.sh
```

#### Initial:

```
aws lambda create-function \
  --function-name pmc-timecard \
  --runtime python3.7 \
  --role arn:aws:iam::281685048228:role/ServiceLambdaBasic \
  --handler handler \
  --timeout 60 \
  --zip-file fileb://myDeploymentPackage.zip
```