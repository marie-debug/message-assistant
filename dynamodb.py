import boto3
import os
from datetime import datetime, timedelta

import User

aws_access_key_id = os.environ.get('AWS_ACCESS_KEY')
aws_secret_access_key = os.environ.get('AWS_SECRET_KEY')
dynamodb_client = boto3.client(
    'dynamodb',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name="ap-southeast-2"
)


def AddActiveUser(sent_message):
    return dynamodb_client.put_item(
        TableName="active_users",
        Item={
            'Id': {'S': sent_message.Id},
            'Type': {'S': sent_message.Type},
            'Name': {'S': sent_message.Name},
            'PhoneNumber': {'S': sent_message.PhoneNumber},
            'Relation': {'S': sent_message.Relation},
            'ExpirationTime': {'N': sent_message.ExpirationTime},
            'Error': {'S': str(sent_message.Error)},
        }
    )


def GetActiveUser(phone_number):
    response = dynamodb_client.get_item(
        Key={
            'PhoneNumber': {'S': phone_number},
        },
        TableName="active_users",
    )
    if 'Item' in response:
        item = response['Item']
        return SentMessage.User(
            item['Id'],
            item['Type'],
            item['Name'],
            item['PhoneNumber'],
            item['Relation'],
            item['Error']
        )
    else:
        return None


def RemoveActiveUser(phone_number):
    return dynamodb_client.delete_item(
        TableName="active_users",
        Key={
            'PhoneNumber': {'S': phone_number}
        }
    )
