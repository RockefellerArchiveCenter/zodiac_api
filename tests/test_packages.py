import json
from os import getenv
from pathlib import Path

import boto3
import pytest
from moto import mock_dynamodb

from src.create_package import create_package
from src.get_package import get_package
from src.list_packages import list_packages, lambda_handler
from src.update_package import update_package

TABLE_NAME = getenv('DYNAMODB_PACKAGE_TABLE')


@pytest.fixture(autouse=True)
def mock_table():
    with mock_dynamodb():
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[{'AttributeName': 'identifier','KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'identifier','AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 123, 'WriteCapacityUnits': 123})
        yield table
        # Tests run here
        table.delete()
        

@pytest.fixture
def package_data():
    path_to_file = Path("tests", "fixtures", "packages", "f78742e5-6af9-4756-a94a-6cd297406d50.json")
    with open(path_to_file, "r") as read_file:
        data = json.load(read_file)
    return data


def test_create_package(package_data, mock_table):
    """Assert packages """       
    created = create_package(package_data)
    response = mock_table.get_item(Key={'identifier':package_data['identifier']})
    actual_output = response['Item']
    assert actual_output == package_data
    assert created == package_data


def test_get_package(package_data, mock_table):
    """Assert packages can be retrieved as expected"""
    mock_table.put_item(Item=package_data)
    response = get_package({"identifier": package_data["identifier"]})
    assert response == package_data


def test_get_missing_package(package_data, mock_table):
    """Assert expected error is raised when item is missing"""
    mock_table.put_item(Item=package_data)
    response = get_package({"identifier": "12345"})
    assert response == ({'error': 'Package not found'}, 404)


def test_list_packages(package_data, mock_table):
    for identifier, status in [
            ("1", "completed"),
            ("2", "completed"),
            ("3", "errored"),
            ("4", "in progress"),
            ("5", "failed")]:
        package_data['identifier'] = identifier
        package_data['status'] = status
        mock_table.put_item(Item=package_data)
    response = list_packages()
    assert len(response) == 5

    response = lambda_handler({'rawPath': '/packages'}, None)
    assert len(response['body']) == 5

    response = list_packages('completed')
    assert len(response) == 2

    response = lambda_handler({'rawPath': '/packages/completed/'}, None)
    assert len(response['body']) == 2

    response = list_packages('errored')
    assert len(response) == 1

    response = lambda_handler({'rawPath': '/packages/errored'}, None)
    assert len(response['body']) == 1

    response = list_packages('failed')
    assert len(response) == 1

    response = lambda_handler({'rawPath': '/packages/failed'}, None)
    assert len(response['body']) == 1

    response = list_packages('in progress')
    assert len(response) == 1

    response = lambda_handler({'rawPath': '/packages/in-progress'}, None)
    assert len(response['body']) == 1

    response = list_packages('fake status')
    assert len(response) == 0

    response = lambda_handler({'rawPath': '/packages/fake-status'}, None)
    assert len(response['body']) == 0


def test_update_package(package_data, mock_table):
    mock_table.put_item(Item=package_data)
    assert package_data['origin'] == 'digitization'
    package_data['origin'] = 'aurora'

    response = update_package(package_data)
    assert response['origin'] == 'aurora'

