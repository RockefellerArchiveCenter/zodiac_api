import traceback
from os import getenv

import boto3

from .helpers import format_response, scan

table_name = getenv('DYNAMODB_EVENT_TABLE')
dynamo = boto3.resource('dynamodb').Table(table_name)


def list_package_events(package_id=None):
    try:
        if package_id:
            return list(scan(dynamo, FilterExpression=boto3.dynamodb.conditions.Attr(
                'package_identifier').eq(package_id)))
        else:
            return list(scan(dynamo, **{}))
    except Exception as e:
        return {'error': ''.join(traceback.format_exception(e)[:-1])}, 500


def lambda_handler(event, context):
    # /packages/2/events
    processed_path = event['rawPath'].rstrip('/')
    package_id = processed_path.split(
        '/')[-2] if len(processed_path.split('/')) > 3 else None
    return format_response(list_package_events(package_id))
