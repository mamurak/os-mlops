from datetime import datetime
from os import getenv

from pyspark.sql import SparkSession


s3_endpoint_url = getenv('AWS_S3_ENDPOINT')
s3_access_key_id = getenv('AWS_ACCESS_KEY_ID')
s3_secret_access_key = getenv('AWS_SECRET_ACCESS_KEY')
s3_bucket = 'spark-demo'


spark = SparkSession\
    .builder\
    .appName("PythonWordCount")\
    .getOrCreate()

hadoopConf = spark.sparkContext._jsc.hadoopConfiguration()
hadoopConf.set("fs.s3a.endpoint", s3_endpoint_url)
hadoopConf.set("fs.s3a.access.key", s3_access_key_id)
hadoopConf.set("fs.s3a.secret.key", s3_secret_access_key)
hadoopConf.set("fs.s3a.path.style.access", "true")
hadoopConf.set("fs.s3a.connection.ssl.enabled", "false")

text_file = spark.sparkContext \
                 .textFile(f's3a://{s3_bucket}/shakespeare.txt') \
                 .flatMap(lambda line: line.split(' ')) \
                 .map(
                    lambda x: x.replace(',',' ') \
                               .replace('.',' ') \
                               .replace('-',' ') \
                               .lower())

sorted_counts = text_file.flatMap(lambda line: line.split(' ')) \
                         .map(lambda word: (word, 1)) \
                         .reduceByKey(lambda a, b: a + b) \
                         .sortBy(
                            lambda wordCounts: wordCounts[1],
                            ascending=False)

i = 0
for word, count in sorted_counts.collect()[0:500]:
    print(f'{i} : {word} : {count} ')
    i += 1

now = datetime.now()
date_time = now.strftime('%d-%m-%Y_%H:%M:%S')

sorted_counts.saveAsTextFile(f's3a://{s3_bucket}/sorted_counts_{date_time}')

spark.stop()
