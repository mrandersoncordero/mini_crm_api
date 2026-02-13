import phonenumbers
from typing import Optional


def validate_phone(phone: str, country: str = "VE") -> str:
    """
    Validates and formats phone number to E164 format.

    Args:
        phone: Phone number string
        country: ISO country code (default: VE for Venezuela)

    Returns:
        Formatted phone number in E164 format (+584123456789)

    Raises:
        ValueError: If phone number is invalid
    """
    if not phone:
        raise ValueError("Phone number is required")

    try:
        parsed = phonenumbers.parse(phone, country)
        if not phonenumbers.is_valid_number(parsed):
            raise ValueError(f"Invalid phone number: {phone}")
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException as e:
        raise ValueError(f"Invalid phone number format: {phone}. Error: {str(e)}")


def format_phone_display(phone: str, country: str = "VE") -> Optional[str]:
    """
    Formats phone number for display (optional utility).

    Args:
        phone: Phone number in E164 format
        country: ISO country code

    Returns:
        Formatted phone number or None if invalid
    """
    if not phone:
        return None

    try:
        parsed = phonenumbers.parse(phone, country)
        return phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
        )
    except phonenumbers.NumberParseException:
        return phone
