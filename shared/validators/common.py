import re
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


EGYPTIAN_PHONE_REGEX = re.compile(r"^(?:\+20|0020|0)?1[0125][0-9]{8}$")
LETTERS_ONLY_REGEX = re.compile(r"^[A-Za-z\u0600-\u06FF\s]+$")
SPECIAL_CHARACTER_REGEX = re.compile(r"[^\w\s]")

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
DOCUMENT_EXTENSIONS = IMAGE_EXTENSIONS | {".pdf"}


def validate_egyptian_phone(value):
    if not EGYPTIAN_PHONE_REGEX.match(str(value)):
        raise ValidationError(_("Enter a valid Egyptian mobile phone number."))


def validate_letters_only(value):
    if not LETTERS_ONLY_REGEX.match(str(value).strip()):
        raise ValidationError(_("Name must contain letters and spaces only."))


def validate_strong_password(value):
    password = str(value)
    if len(password) < 8:
        raise ValidationError(_("Password must be at least 8 characters long."))
    if not any(char.isalpha() for char in password):
        raise ValidationError(_("Password must contain at least one letter."))
    if not SPECIAL_CHARACTER_REGEX.search(password):
        raise ValidationError(_("Password must contain at least one special character."))


def validate_file_size(file_obj):
    if file_obj.size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise ValidationError(
            _("File size cannot exceed %(size)s MB.")
            % {"size": settings.MAX_UPLOAD_SIZE_MB}
        )


def validate_image_file(file_obj):
    validate_file_size(file_obj)
    ext = Path(file_obj.name).suffix.lower()
    if ext not in IMAGE_EXTENSIONS:
        raise ValidationError(_("Only JPG, PNG, and WEBP image files are allowed."))


def validate_document_file(file_obj):
    validate_file_size(file_obj)
    ext = Path(file_obj.name).suffix.lower()
    if ext not in DOCUMENT_EXTENSIONS:
        raise ValidationError(_("Only PDF or image files are allowed."))
