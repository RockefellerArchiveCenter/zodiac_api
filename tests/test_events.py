import json
from os import getenv
from pathlib import Path

import boto3
import pytest
from moto import mock_dynamodb

from src import list_events, list_package_events
from src.create_event import create_event
from src.get_event import get_event
from src.update_event import update_event

TABLE_NAME = getenv('DYNAMODB_EVENT_TABLE')


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
def event_data():
    path_to_file = Path(
        "tests",
        "fixtures",
        "events",
        "f78742e5-6af9-4756-a94a-6cd297406d50.json")
    with open(path_to_file, "r") as read_file:
        data = json.load(read_file)
    return data


def test_create_event(event_data, mock_table):
    """Assert events are created as expected."""
    created = create_event(event_data)
    response = mock_table.get_item(
        Key={'identifier': event_data['identifier']})
    actual_output = response['Item']
    assert actual_output == event_data
    assert created == {'Event created.'}


def test_get_event(event_data, mock_table):
    """Assert events can be retrieved as expected."""
    mock_table.put_item(Item=event_data)
    response = get_event(event_data["identifier"])
    assert response == (event_data, 200)


def test_get_missing_event(event_data, mock_table):
    """Assert expected error is raised when item is missing"""
    mock_table.put_item(Item=event_data)
    response = get_event("12345")
    assert response == ({'error': 'Event not found'}, 404)


def test_list_events(event_data, mock_table):
    """Assert events are listed as expected, including filtering by outcome."""
    for identifier in ["1", "2", "3"]:
        event_data['identifier'] = identifier
        mock_table.put_item(Item=event_data)
    response = list_events.list_events()
    assert len(response[0]) == 3

    response = list_events.lambda_handler({}, None)
    assert len(json.loads(response['body'])) == 3


def test_list_package_events(event_data, mock_table):
    """Assert events are listed as expected, including filtering by outcome."""
    for identifier, package_identifier in [
            ("1", "a"),
            ("2", "b"),
            ("3", "b"),]:
        event_data['identifier'] = identifier
        event_data['package_identifier'] = package_identifier
        mock_table.put_item(Item=event_data)

    response = list_package_events.list_package_events('a')
    assert len(response[0]) == 1

    response = list_package_events.lambda_handler(
        {'pathParameters': {'package_id': 'a'}}, None)
    assert len(json.loads(response['body'])) == 1

    response = list_package_events.list_package_events('b')
    assert len(response[0]) == 2

    response = list_package_events.lambda_handler(
        {'pathParameters': {'package_id': 'b'}}, None)
    assert len(json.loads(response['body'])) == 2


def test_update_event(event_data, mock_table):
    mock_table.put_item(Item=event_data)
    assert event_data['outcome'] == 'success'
    event_data['outcome'] = 'failure'

    response = update_event(event_data)
    assert response[0]['outcome'] == 'failure'
