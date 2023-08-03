from operator import add
from random import random
from os import getenv
from socket import gethostname, gethostbyname

from pyspark import SparkConf
from pyspark.sql import SparkSession


hostname = gethostname()
ip_address = gethostbyname(hostname)
kubernetes_service_host = getenv('KUBERNETES_SERVICE_HOST')
pyspark_runtime_image =\
    'quay.io/opendatahub-contrib/pyspark:s3.3.1-h3.3.4_v0.1.1'

with open('/var/run/secrets/kubernetes.io/serviceaccount/namespace', 'r') as f:
    current_namespace = f.readline()

sparkConf = SparkConf()
sparkConf.setMaster(f'k8s://https://{kubernetes_service_host}:443')
sparkConf.set('spark.submit.deployMode', 'client')
sparkConf.set('spark.kubernetes.container.image', pyspark_runtime_image)
sparkConf.set('spark.kubernetes.namespace', current_namespace)
sparkConf.set('spark.driver.host', ip_address)
sparkConf.set('spark.executor.instances', '3')
sparkConf.set('spark.executor.memory', '512m')
sparkConf.set('spark.executor.cores', '1')
sparkConf.set('spark.kubernetes.pyspark.pythonVersion', '3')

spark = SparkSession.builder.config(conf=sparkConf).getOrCreate()
sc = spark.sparkContext


def f(_):
    x = random() * 2 - 1
    y = random() * 2 - 1
    return 1 if x ** 2 + y ** 2 <= 1 else 0


partitions = 7
n = 10000000 * partitions

count = sc.parallelize(range(1, n + 1), partitions).map(f).reduce(add)
print(f'Pi is roughly {4.0 * count / n}')

sc.stop()
