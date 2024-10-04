import traceback
from os import getenv

import boto3

from .helpers import format_response

table_name = getenv('DYNAMODB_PACKAGE_TABLE')
dynamo = boto3.resource('dynamodb').Table(table_name)


def get_package(package_id):
    try:
        return dynamo.get_item(Key={'identifier': package_id})['Item'], 200
    except KeyError:
        return {'error': f'Package {package_id} not found'}, 404
    except Exception as e:
        return {'error': ''.join(traceback.format_exception(e)[:-1])}, 500


def lambda_handler(event, context):
    package_id = event['pathParameters']['package_id']
    return format_response(*get_package(package_id))
