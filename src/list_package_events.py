import traceback
from os import getenv

import boto3

from .helpers import format_response, scan

table_name = getenv('DYNAMODB_EVENT_TABLE')
dynamo = boto3.resource('dynamodb').Table(table_name)


def list_package_events(package_id):
    try:
        return list(scan(dynamo, FilterExpression=boto3.dynamodb.conditions.Attr(
            'package_identifier').eq(package_id))), 200
    except Exception as e:
        return {'error': ''.join(traceback.format_exception(e)[:-1])}, 500


def lambda_handler(event, context):
    package_id = event['pathParameters']['package_id']
    return format_response(*list_package_events(package_id))
