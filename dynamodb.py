import boto3
import os
from datetime import datetime, timedelta

from User import User

aws_access_key_id = os.environ.get('AWS_ACCESS_KEY')
aws_secret_access_key = os.environ.get('AWS_SECRET_KEY')
dynamodb_client = boto3.client(
    'dynamodb',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name="ap-southeast-2"
)


def AddActiveUser(sent_message):
    """
    Adds active user to the database
    :param sent_message:
    :type :list
    """
    return dynamodb_client.put_item(
        TableName="active_users",
        Item={
            'Age': {'S': sent_message.Age},
            'Id': {'S': sent_message.Id},
            'Name': {'S': sent_message.Name},
            'PhoneNumber': {'S': sent_message.PhoneNumber},
            'Relation': {'S': sent_message.Relation},
            'ExpirationTime': {'N': sent_message.ExpirationTime},
            'Error': {'S': str(sent_message.Error)},
            'Conversation': {'L': ListToDynamoList(sent_message.Conversation)}
        }
    )


def ListToDynamoList(list):
    """
    converts a list to a dynamodb list
    :param list:
    :type:list
    :return dynamo_list:
    :rtype list:
    """
    dynamo_list = []
    for item in list:
        dic = {'S': item}
        dynamo_list.append(dic)
    return dynamo_list


def DynamoListToList(dynamo_list):
    """
    converts dynamodb list to a python list
    :param dynamo_list:
    :type: list
    :return list:
    """
    list = []
    for item in dynamo_list:
        list.append(item['S'])
    return list


def UpdateActiveUserConversation(sent_message):
    """
    updates active user conversation in dynamodb
    :param sent_message:
    :type sent_message: User

    """
    return dynamodb_client.update_item(
        TableName="active_users",
        Key={'PhoneNumber': {'S': sent_message.PhoneNumber}},
        UpdateExpression="set Conversation=:element",
        ExpressionAttributeValues={":element": {"L": ListToDynamoList(sent_message.Conversation)}}
    )


def GetActiveUser(phone_number):
    """
    gets  active users if they exist
    :param phone_number
    :type :str
    :return User class:
    :rtype: User
    """
    response = dynamodb_client.get_item(
        Key={
            'PhoneNumber': {'S': phone_number},
        },
        TableName="active_users",
    )
    if 'Item' in response:
        item = response['Item']
        return User(
            item['Id']['S'],
            item['Name']['S'],
            item['PhoneNumber']['S'],
            item['Relation']['S'],
            item['Error']['S'],
            DynamoListToList(item['Conversation']['L']),
            item['Age']['S']
        )
    else:
        return None


def RemoveActiveUser(phone_number):
    """
    removes active users from dynamodb
    :param phone_number:
    :type phone_number: str
    """
    return dynamodb_client.delete_item(
        TableName="active_users",
        Key={
            'PhoneNumber': {'S': phone_number}
        }
    )
