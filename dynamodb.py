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
            'Conversation': {'L': ListToDynamoList(sent_message.Conversation)}
        }
    )


def ListToDynamoList(list):
    dynamo_list = []
    for item in list:
        dic = {'S': item}
        dynamo_list.append(dic)
    return dynamo_list


def DynamoListToList(dynamo_list):
    list = []
    for item in dynamo_list:
        list.append(item['S'])
    return list


def UpdateActiveUserConversation(sent_message):
    return dynamodb_client.update_item(
        TableName="active_users",
        Key={'PhoneNumber': {'S': sent_message.PhoneNumber}},
        UpdateExpression="set Conversation=:element",
        ExpressionAttributeValues={":element": {"L": ListToDynamoList(sent_message.Conversation)}}
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
        return User.User(
            item['Id']['S'],
            item['Type']['S'],
            item['Name']['S'],
            item['PhoneNumber']['S'],
            item['Relation']['S'],
            item['Error']['S'],
            DynamoListToList(item['Conversation']['L'])
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
