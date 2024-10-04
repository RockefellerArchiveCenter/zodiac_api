import json


def format_response(body, status_code=200):
    return {
        "isBase64Encoded": False,
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body)
    }


def scan(table, **kwargs):
    response = table.scan(**kwargs)
    yield from response['Items']
    while response.get('LastEvaluatedKey'):
        response = table.scan(
            ExclusiveStartKey=response['LastEvaluatedKey'], **kwargs)
        yield from response['Items']


def parse_update(data):
    """Prepares data for update request.

    Removes null values and identifier from dict.
    """
    filtered_data = {
        key: value for key,
        value in data.items() if (
            value and key != 'identifier')}
    update_expression = 'SET {}'.format(
        ','.join(f'#{k}=:{k}' for k in filtered_data))
    expression_attribute_values = {
        f':{k}': v for k,
        v in filtered_data.items()}
    expression_attribute_names = {f'#{k}': k for k in filtered_data}
    return update_expression, expression_attribute_values, expression_attribute_names
