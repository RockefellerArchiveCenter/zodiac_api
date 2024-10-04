import json
from os import getenv
from pathlib import Path

import boto3
import pytest
from moto import mock_dynamodb

from src.create_package import create_package
from src.get_package import get_package
from src.list_packages import lambda_handler, list_packages
from src.update_package import update_package

TABLE_NAME = getenv('DYNAMODB_PACKAGE_TABLE')


@pytest.fixture(autouse=True)
def mock_table():
    with mock_dynamodb():
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[{'AttributeName': 'identifier', 'KeyType': 'HASH'}],
            AttributeDefinitions=[
                {'AttributeName': 'identifier', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 123, 'WriteCapacityUnits': 123})
        yield table
        # Tests run here
        table.delete()


@pytest.fixture
def package_data():
    path_to_file = Path(
        "tests",
        "fixtures",
        "packages",
        "f78742e5-6af9-4756-a94a-6cd297406d50.json")
    with open(path_to_file, "r") as read_file:
        data = json.load(read_file)
    return data


def test_create_package(package_data, mock_table):
    """Assert packages """
    created = create_package(package_data)
    response = mock_table.get_item(
        Key={'identifier': package_data['identifier']})
    actual_output = response['Item']
    assert actual_output == package_data
    assert created == {'Package created.'}


def test_get_package(package_data, mock_table):
    """Assert packages can be retrieved as expected"""
    mock_table.put_item(Item=package_data)
    response = get_package(package_data["identifier"])
    assert response == (package_data, 200)


def test_get_missing_package(package_data, mock_table):
    """Assert expected error is raised when item is missing"""
    mock_table.put_item(Item=package_data)
    response = get_package("12345")
    assert response == ({'error': 'Package 12345 not found'}, 404)


def test_list_packages(package_data, mock_table):
    for identifier in ["1", "2", "3"]:
        package_data['identifier'] = identifier
        mock_table.put_item(Item=package_data)
    response = list_packages()
    assert len(response[0]) == 3

    response = lambda_handler({}, None)
    assert len(json.loads(response['body'])) == 3


def test_update_package(package_data, mock_table):
    mock_table.put_item(Item=package_data)
    assert package_data['origin'] == 'digitization'
    package_data['origin'] = 'aurora'

    response = update_package(package_data)
    assert response[0]['origin'] == 'aurora'
