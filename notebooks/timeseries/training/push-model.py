from datetime import datetime
import os

import boto3


s3_endpoint_url = os.environ.get('S3_ENDPOINT_URL')
s3_access_key = os.environ.get('S3_ACCESS_KEY')
s3_secret_key = os.environ.get('S3_SECRET_KEY')
s3_bucket_name = os.environ.get('S3_BUCKET_NAME')

timestamp = datetime.now().strftime('%y%m%d%H%M')
model_name = f'model-{timestamp}.joblib'
s3_model_location = f's3://{s3_bucket_name}/{model_name}'

print(f'Uploading model to bucket {s3_bucket_name}'
      f'to S3 storage at {s3_endpoint_url}')
s3_client = boto3.client(
    's3', endpoint_url=s3_endpoint_url,
    aws_access_key_id=s3_access_key, aws_secret_access_key=s3_secret_key
)
with open('model.joblib', 'rb') as model_file:
    s3_client.upload_fileobj(model_file, s3_bucket_name, model_name)

with open('model.joblib', 'rb') as model_file:
    s3_client.upload_fileobj(model_file, s3_bucket_name, 'model-latest.joblib')

with open('model_object_name', 'w') as outputfile:
    outputfile.write(model_name)