from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from shared.validators.common import (
    validate_egyptian_phone,
    validate_letters_only,
    validate_strong_password,
)


class ValidatorTests(SimpleTestCase):
    def test_egyptian_phone_accepts_valid_mobile_numbers(self):
        validate_egyptian_phone("01012345678")
        validate_egyptian_phone("+201112345678")

    def test_egyptian_phone_rejects_invalid_numbers(self):
        with self.assertRaises(ValidationError):
            validate_egyptian_phone("01234")

    def test_letters_only_supports_arabic_and_english(self):
        validate_letters_only("Ahmed Ali")
        validate_letters_only("أحمد علي")

    def test_letters_only_rejects_digits(self):
        with self.assertRaises(ValidationError):
            validate_letters_only("Ahmed 123")

    def test_password_requires_length_letter_and_special_character(self):
        validate_strong_password("Ghaith!123")
        with self.assertRaises(ValidationError):
            validate_strong_password("abcdefgh")
