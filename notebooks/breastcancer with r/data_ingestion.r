library(aws.s3)

s3_bucket <- Sys.getenv('AWS_S3_BUCKET')

print('loading data from bucket')
save_object("BreastCancerWisconsinDataSet.csv", file = "raw_data.csv", bucket = s3_bucket, region ="")
print('data ingestion complete.')