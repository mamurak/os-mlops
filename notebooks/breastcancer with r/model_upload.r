library(aws.s3)

s3_bucket <- Sys.getenv('AWS_S3_BUCKET')

# Format the time as a string suitable for filenames
current_time <- Sys.time()
timestamp <- format(current_time, "%Y%m%d_%H%M%S")

# Create the filename using the formatted timestamp

object_name <- paste0("model_", timestamp, ".bst")
print('Uploading model to: ')
print(object_name)

put_object(file = "model.bst", object = object_name, bucket = s3_bucket, region = "")

print('Model upload complete')