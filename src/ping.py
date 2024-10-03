from src.helpers import format_response

def lambda_handler(event, context):
    return format_response(event, None)