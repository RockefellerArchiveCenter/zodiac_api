import json

from src.helpers import format_response, parse_update


def test_parse_update():
    data = {"id": "foo", "bar": None, "baz": ["buzz", "biz"]}
    expression, attributes, values = parse_update(data)
    assert expression == 'SET #id=:id,#baz=:baz'
    assert attributes == {':id': 'foo', ':baz': ['buzz', 'biz']}
    assert values == {'#id': 'id', '#baz': 'baz'}


def test_scan():
    # without args
    # with args
    pass


def test_format_response():
    # with response code
    body = "Request successful!"
    output = format_response(body)
    assert output['body'] == json.dumps(body)
    assert output['statusCode'] == 200

    # without response code
    body = {"error": "There was a problem with your request."}
    status_code = 500
    output = format_response(body, status_code)
    assert output['body'] == json.dumps(body)
    assert output['statusCode'] == status_code
