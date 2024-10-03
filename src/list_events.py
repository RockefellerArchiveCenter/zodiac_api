import traceback
from os import getenv

import boto3

from .helpers import format_response, scan

table_name = getenv('DYNAMODB_EVENT_TABLE')
dynamo = boto3.resource('dynamodb').Table(table_name)


def list_events(outcome=None):
    try:
        if outcome:
            return list(scan(dynamo, FilterExpression=boto3.dynamodb.conditions.Attr(
                'outcome').eq(outcome)))
        else:
            return list(scan(dynamo, **{}))
    except Exception as e:
        return {'error': ''.join(traceback.format_exception(e)[:-1])}, 500


def lambda_handler(event, context):
    processed_path = event['rawPath'].rstrip('/')
    outcome = processed_path.split(
        '/')[-1].replace('-', ' ') if len(processed_path.split('/')) > 2 else None
    return format_response(list_events(outcome))
