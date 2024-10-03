import traceback
from os import getenv

import boto3

from .helpers import format_response

table_name = getenv('DYNAMODB_EVENT_TABLE')
dynamo = boto3.resource('dynamodb').Table(table_name)


def create_event(event_data):
    try:
        dynamo.put_item(Item=event_data)
        return dynamo.get_item(
            Key={'identifier': event_data['identifier']})['Item']
    except Exception as e:
        return {'error': ''.join(traceback.format_exception(e)[:-1])}, 500


def lambda_handler(event, context):
    return format_response(create_event(event['body']))
