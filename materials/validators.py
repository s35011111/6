import re
from django.core.exceptions import ValidationError


def validate_no_links(value):
    patterns = [
        r'https?://\S+',
        r'www\.\S+',
        r'\b\S+\.(?:com|org|net|io|gov|edu)\b',
    ]

    for pattern in patterns:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValidationError("Text cannot contain links or URLs.")
    return value


def validate_youtube_only(value):
    if value == "" or value is None:
        return value
    if "youtube.com" in value:
        return value
    else:
        raise ValidationError("Text cannot contain links or URLs.")
