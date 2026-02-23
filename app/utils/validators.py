import phonenumbers
from phonenumbers import PhoneNumberFormat
from typing import Optional


def validate_phone(phone: str, default_country: str = "VE") -> str:
    """
    Validates and formats phone number to E164 format.
    Supports international numbers and auto-detection.

    Args:
        phone: Phone number string (can include +country code or not)
        default_country: ISO country code to use if no country code detected (default: VE)

    Returns:
        Formatted phone number in E164 format (+584123456789)

    Raises:
        ValueError: If phone number is invalid
    """
    if not phone:
        raise ValueError("Phone number is required")

    # Clean the phone string - remove spaces, dashes, parentheses
    phone = phone.strip()

    # Remove any leading + for processing, we'll add it back
    original_has_plus = phone.startswith("+")
    if original_has_plus:
        phone = phone[1:]

    # Try with default country first (most common for local numbers in Venezuela)
    try:
        parsed = phonenumbers.parse(phone, default_country)
        # Use is_possible_number instead of is_valid_number for more lenient validation
        if phonenumbers.is_possible_number(parsed):
            return phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        pass

    # Try to parse as international number (with country code in the number)
    try:
        # Try with "00" prefix
        if not original_has_plus:
            try:
                parsed = phonenumbers.parse(f"00{phone}", None)
                if phonenumbers.is_possible_number(parsed):
                    return phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
            except phonenumbers.NumberParseException:
                pass

        # Try with + prefix
        if original_has_plus or not phone.isdigit():
            parsed = phonenumbers.parse(phone, None)
            if phonenumbers.is_possible_number(parsed):
                return phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        pass

    # Try with common country codes
    common_countries = [
        "VE",
        "AR",
        "CO",
        "MX",
        "US",
        "ES",
        "BR",
        "CL",
        "PE",
        "EC",
        "GB",
        "FR",
        "DE",
        "IT",
        "PT",
    ]

    for country_code in common_countries:
        try:
            parsed = phonenumbers.parse(phone, country_code)
            if phonenumbers.is_possible_number(parsed):
                return phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            continue

    # Last resort: try with the raw phone (in case it already has country code)
    try:
        parsed = phonenumbers.parse(phone, None)
        if phonenumbers.is_possible_number(parsed):
            return phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        pass

    raise ValueError(f"Invalid phone number: {phone}")


def extract_country_from_phone(phone: str) -> Optional[str]:
    """
    Extract country code from phone number if present.

    Args:
        phone: Phone number string

    Returns:
        Country code (e.g., 'VE', 'AR') or None if not detected
    """
    if not phone:
        return None

    try:
        # Try to parse as international number
        parsed = phonenumbers.parse(phone, None)
        if parsed:
            region_code = phonenumbers.region_code_for_number(parsed)
            return region_code
    except phonenumbers.NumberParseException:
        pass

    return None


def format_phone_display(phone: str, default_country: str = "VE") -> Optional[str]:
    """
    Formats phone number for display (optional utility).

    Args:
        phone: Phone number in E164 format
        default_country: ISO country code for fallback

    Returns:
        Formatted phone number or None if invalid
    """
    if not phone:
        return None

    try:
        # Try to parse as E164 (no region needed)
        parsed = phonenumbers.parse(phone, None)
        return phonenumbers.format_number(parsed, PhoneNumberFormat.INTERNATIONAL)
    except phonenumbers.NumberParseException:
        # Fallback: try with default country
        try:
            parsed = phonenumbers.parse(phone, default_country)
            return phonenumbers.format_number(parsed, PhoneNumberFormat.INTERNATIONAL)
        except phonenumbers.NumberParseException:
            return phone
