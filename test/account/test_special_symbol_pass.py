
from django.core.exceptions import ValidationError
from django.test.testcases import TestCase

from accounts.validators import SpecialCharacterValidator

class SpecialCharacterValidatorTestCase(TestCase):
    def setUp(self):
        self.validator = SpecialCharacterValidator()


    def test_password_with_special_character_passes(self):
        password = 'Password123!'
        # No exception means the password is valid
        try:
            self.validator.validate(password)
        except ValidationError:
            self.fail("ValidationError raised for valid password with special character.")

    def test_password_without_special_character_fails(self):
        password = 'Password123'
        with self.assertRaises(ValidationError) as context:
            self.validator.validate(password)
        self.assertIn("special character", str(context.exception))

    def test_get_help_text(self):
        help_text = self.validator.get_help_text()
        self.assertIn("special character", help_text)
