import json
import boto3
import os
import uuid
from datetime import date, datetime
from dateutil.tz import tzutc

s3_client = boto3.client('s3')
sns_client = boto3.client('sns')
monitoring_bucket = os.getenv("MONITORING_BUCKET")

thresholds = {
        'ApproximateAgeOfOldestMessage':{
            'value': 30000,
            'unit': "seconds"
        }, 
        'ApproximateNumberOfMessagesDelayed':{
            'value': 300,
            'unit': "count"
        }, 
        'ApproximateNumberOfMessagesNotVisible':{
            'value': 30,
            'unit': "count"
        }, 
        'ApproximateNumberOfMessagesVisible':{
            'value': 100,
            'unit': "count"
        }, 
        'NumberOfEmptyReceives':{
            'value': 1,
            'unit': "count" 
        }, 
        'NumberOfMessagesDeleted':{
            'value': 20,
            'unit': "count"
        }, 
        'NumberOfMessagesReceived':{
            'value': 20,
            'unit': "count"
        }, 
        'NumberOfMessagesSent':{
            'value': 100,
            'unit': "count"
        }, 
       'SentMessageSize':{
            'value': 10000,
            'unit': "bytes"
        }
    }

def run(event, context):
    if event["Records"] == None:
        return
    
    print(f"NOTICE:---------- getting sqs data for analysis in bucket: {monitoring_bucket}")
    for object in event["Records"]:
        print(object)
        if (object["eventName"].split(":")[0] == "ObjectCreated"):
            object_key = object["s3"]["object"]["key"]
            print(f'The object key is: {object_key}')
            analyze_rds(object_key)

def analyze_rds(key):
    obj = get_object('vodasure-daily-monitoring', key)
    rds_run_results = json.loads(obj["Body"].read())

    analyze_rds_metrics(rds_run_results)

def analyze_rds_metrics(data):

    for metric in data:
        for i in thresholds:
            if data[i]["Datapoints"][0]["Average"] >= thresholds[i]['value']:
                message = f"""
                Seems SQS {i} is over {thresholds[i]['value']}{thresholds[i]['unit']},
                The service is currently on {data[i]["Datapoints"][0]["Average"]} Utilization
                """
                
                publish_message(message, "Services Status")
                print(f"NOTICE:---------- published \n message: {message}")
    
    
def publish_message(message, subject):
    """
    Publishes a message to a topic.
    """
    try:
        response = sns_client.publish(
            TopicArn=os.getenv("ECS_SNS_TOPIC"),
           Message=message,
            Subject=subject,
        )
        print(response)
    except Exception as e:
        print("Error: an error ocurred Getting object \n\r {0}".format(e))
        return None

    return response['MessageId']

def get_object(bucket, prefix):
    """
    Get a single object inside  a prefix
    """
    try:
        result = s3_client.get_object(
            Bucket=bucket,
            Key=prefix
        )
    except Exception as e:
        print("Error: an error ocurred Getting object \n\r {0}".format(e))
        result = None

    return result