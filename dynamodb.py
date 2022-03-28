import boto3
import os
from datetime import datetime, timedelta

aws_access_key_id = os.environ.get('AWS_ACCESS_KEY')
aws_secret_access_key = os.environ.get('AWS_SECRET_KEY')
dynamodb_client = boto3.client(
    'dynamodb',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name="ap-southeast-2"
)


def AddActiveUser(_from):
    return dynamodb_client.put_item(
        TableName="active_users",
        Item={
            'From': {'S': _from},
            'ExpirationTime': {'N': str(int((datetime.utcnow() + timedelta(minutes=30)).timestamp()))}
        }
    )


def IsUserActive(_from):
    response = dynamodb_client.get_item(
        Key={
            'From': {'S': _from},
        },
        TableName="active_users",
    )
    if 'Item' in response:
        return True
    else:
        return False


def RemoveActiveUser(_from):
    return dynamodb_client.delete_item(
        TableName="active_users",
        Key={
            'From': {'S': _from}
        }
    )
