import json
import os

def load_error_messages():
    file_path = os.path.join(os.path.dirname(__file__), 'message.json')
    with open(file_path, 'r') as f:
        return json.load(f)

# Load error messages at module load time.
ERROR_MESSAGES = load_error_messages()

def get_error_message(error_name, **kwargs):
    message_template = ERROR_MESSAGES.get(error_name, "Unknown error.")
    return message_template.format(**kwargs)
