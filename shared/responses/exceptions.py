from django.utils.translation import gettext_lazy as _
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    original_data = response.data
    if isinstance(original_data, dict) and "detail" in original_data:
        message = original_data["detail"]
    else:
        message = _("Validation error.")

    response.data = {
        "success": False,
        "message": str(message),
        "data": original_data,
    }
    return response
