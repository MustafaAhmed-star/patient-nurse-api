from django.utils.translation import gettext_lazy as _
from rest_framework.response import Response


def api_response(success=True, message=None, data=None, status_code=200):
    return Response(
        {
            "success": success,
            "message": str(message or _("Request completed successfully.")),
            "data": data if data is not None else {},
        },
        status=status_code,
    )


class ApiResponseMixin:
    success_message = _("Request completed successfully.")

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if (
            hasattr(response, "data")
            and response.data is not None
            and response.status_code < 400
            and not (
                isinstance(response.data, dict)
                and {"success", "message", "data"}.issubset(response.data.keys())
            )
        ):
            response.data = {
                "success": True,
                "message": str(self.success_message),
                "data": response.data,
            }
        return response
