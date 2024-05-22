import json
import boto3
import datetime import date, datetime, timedelta
import os

cloudwatch_client = boto3.client('cloudwatch')
s3_client = boto3.client('s3')
cluster = os.getenv("TARGET_CLUSTER")
minitoring_bucket = os.getenv("MINITORING_BUCKET")

def run(event, context):
    metric_names = [
        'ApproximateAgeOfOldestMessage',
        'ApproximateNumberOfMessagesDelayed',
        'ApproximateNumberOfMessagesNotVisible',
        'ApproximateNumberOfMessagesVisible'
        'NumberOfEmptyReceives',
        'NumberOfMessagesDeleted',
        'NumberOfMessagesReceived',
        'NumberOfMessagesSent',
        'SentMessageSize'
    ]

    queue_names = [
        'queue_name_1',
        'queue_name_2',
        'queue_name_3',
        'queue_name_4',
        'queue_name_5',
        'queue_name_6'
    ]

    print(f"NOTICE:--------- getting sqs data from queues: ")
    describe_services = describe_services(queue_names, metric_names)
    print(f'Describe_services: {describe_services}')
    print(f"Notice:----------- Writing to monitoring bucket: {minitoring_bucket} for sqs queues: {queue_names}")
    write_to_minitoring_bucket(describe_services)
    return describe_services


def describe_services(queue_names, metric_names):
    service_obj = {}
    sqs_obj = {}
    metric_data = {}
    queue_data = {}


    for queue in queue_names:
        metric_data = {}
        for metric_name in metric_names:
            cloudwatch_request = cloudwatch_client.get_metric_statistics(
                Namespace = 'AWS/SQS',
                MetricName = metric_name,
                Dimensions = [
                             {
                                 'Name': 'QueueName',
                                 'Value': queue
                             },
                ],

                period=300,
                Statistics=['Average'],
                StartTime=datetime.now() - timedelta(minutes=5),
                EndTime=datetime.now()
            )

            # metric_data[metric_name] = cloudwatch_request
            metric_data[metric_name] = json.dumps(cloudwatch_request, default=str)
        queue_data[queue] = metric_data
        service_obj = queue_data

    return service_obj


def write_to_monitoring_bucket(data):
    outputs = {
        "results": data
    }

    dt = datetime.now()
    date_today = str(dt).split(" ")[0]
    timestamp = str(dt.timestamp().split("."))[0]
    result = s3_client.put_object(
        Bucket=f"companyname-daily-monitoring",
        Key=f"sqs/{date_today}/{timestamp}.json",
        Body=bytes(json.dumps(outputs), "utf-8"),
        ServerSideEncryption="AES256"
    )
    return result
