import traceback
from os import getenv

import boto3

from .helpers import format_response

table_name = getenv('DYNAMODB_EVENT_TABLE')
dynamo = boto3.resource('dynamodb').Table(table_name)


def get_event(event_id):
    try:
        return dynamo.get_item(Key={'identifier': event_id})['Item'], 200
    except KeyError:
        return {'error': 'Event not found'}, 404
    except Exception as e:
        return {'error': ''.join(traceback.format_exception(e)[:-1])}, 500


def lambda_handler(event, context):
    event_id = event['pathParameters']['event_id']
    return format_response(*get_event(event_id))
