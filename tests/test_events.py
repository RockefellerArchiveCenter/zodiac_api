import json
from os import getenv
from pathlib import Path

import boto3
import pytest
from moto import mock_dynamodb

from src import list_events
from src import list_package_events
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
            KeySchema=[{'AttributeName': 'identifier','KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'identifier','AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 123, 'WriteCapacityUnits': 123})
        yield table
        # Tests run here
        table.delete()
        

@pytest.fixture
def event_data():
    path_to_file = Path("tests", "fixtures", "events", "f78742e5-6af9-4756-a94a-6cd297406d50.json")
    with open(path_to_file, "r") as read_file:
        data = json.load(read_file)
    return data


def test_create_event(event_data, mock_table):
    """Assert events are created as expected."""       
    created = create_event(event_data)
    response = mock_table.get_item(Key={'identifier':event_data['identifier']})
    actual_output = response['Item']
    assert actual_output == event_data
    assert created == event_data


def test_get_event(event_data, mock_table):
    """Assert events can be retrieved as expected."""
    mock_table.put_item(Item=event_data)
    response = get_event({"identifier": event_data["identifier"]})
    assert response == event_data


def test_get_missing_event(event_data, mock_table):
    """Assert expected error is raised when item is missing"""
    mock_table.put_item(Item=event_data)
    response = get_event({"identifier": "12345"})
    assert response == ({'error': 'Event not found'}, 404)


def test_list_events(event_data, mock_table):
    """Assert events are listed as expected, including filtering by outcome."""
    for identifier, outcome in [
            ("1", "completed"),
            ("2", "completed"),
            ("3", "errored"),
            ("4", "in progress"),
            ("5", "failed")]:
        event_data['identifier'] = identifier
        event_data['outcome'] = outcome
        mock_table.put_item(Item=event_data)
    response = list_events.list_events()
    assert len(response) == 5

    response = list_events.lambda_handler({'rawPath': '/events'}, None)
    assert len(response['body']) == 5

    response = list_events.list_events('completed')
    assert len(response) == 2

    response = list_events.lambda_handler({'rawPath': '/events/completed/'}, None)
    assert len(response['body']) == 2

    response = list_events.list_events('errored')
    assert len(response) == 1

    response = list_events.lambda_handler({'rawPath': '/events/errored'}, None)
    assert len(response['body']) == 1

    response = list_events.list_events('failed')
    assert len(response) == 1

    response = list_events.lambda_handler({'rawPath': '/events/failed'}, None)
    assert len(response['body']) == 1

    response = list_events.list_events('in progress')
    assert len(response) == 1

    response = list_events.lambda_handler({'rawPath': '/events/in-progress'}, None)
    assert len(response['body']) == 1

    response = list_events.list_events('fake status')
    assert len(response) == 0

    response = list_events.lambda_handler({'rawPath': '/events/fake-status'}, None)
    assert len(response['body']) == 0


def test_list_package_events(event_data, mock_table):
    """Assert events are listed as expected, including filtering by outcome."""
    for identifier, package_identifier in [
            ("1", "a"),
            ("2", "b"),
            ("3", "b"),]:
        event_data['identifier'] = identifier
        event_data['package_identifier'] = package_identifier
        mock_table.put_item(Item=event_data)
    response = list_package_events.list_package_events()
    assert len(response) == 3
    
    response = list_package_events.list_package_events('a')
    assert len(response) == 1

    response = list_package_events.lambda_handler({'rawPath': '/packages/a/events'}, None)
    assert len(response['body']) == 1

    response = list_package_events.list_package_events('b')
    assert len(response) == 2

    response = list_package_events.lambda_handler({'rawPath': '/packages/b/events'}, None)
    assert len(response['body']) == 2


def test_update_event(event_data, mock_table):
    mock_table.put_item(Item=event_data)
    assert event_data['outcome'] == 'success'
    event_data['outcome'] = 'failure'

    response = update_event(event_data)
    assert response['outcome'] == 'failure'

