from datetime import datetime
from os import environ

from boto3 import client


s3_endpoint_url = f"https://{environ.get('AWS_S3_ENDPOINT')}"
s3_access_key = environ.get('AWS_ACCESS_KEY_ID')
s3_secret_key = environ.get('AWS_SECRET_ACCESS_KEY')
s3_bucket_name = environ.get('AWS_S3_BUCKET')

s3_client = client(
    's3', endpoint_url=s3_endpoint_url,
    aws_access_key_id=s3_access_key, aws_secret_access_key=s3_secret_key
)

timestamp = datetime.now().strftime('%y%m%d%H%M')
model_object_name = f'model-{timestamp}.bst'

try:
    s3_client.upload_file('model.bst', s3_bucket_name, model_object_name)
except Exception:
    print(f'S3 upload to bucket {s3_bucket_name} at {s3_endpoint_url} failed!')
    raise
print(f'model uploaded and available as "{model_object_name}"')