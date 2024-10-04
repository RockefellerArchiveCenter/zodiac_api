import json
import traceback
from os import getenv

import boto3

from .helpers import format_response, parse_update

table_name = getenv('DYNAMODB_PACKAGE_TABLE')
dynamo = boto3.resource('dynamodb').Table(table_name)


def update_package(package_data):
    try:
        expression, values, names = parse_update(package_data)
        updated = dynamo.update_item(
            Key={'identifier': package_data['identifier']},
            UpdateExpression=expression,
            ExpressionAttributeValues=values,
            ExpressionAttributeNames=names,
            ReturnValues='UPDATED_NEW')
        return updated['Attributes'], 200
    except Exception as e:
        return {'error': ''.join(traceback.format_exception(e)[:-1])}, 500


def lambda_handler(event, context):
    package_data = json.loads(event['body'])
    return format_response(*update_package(package_data))
