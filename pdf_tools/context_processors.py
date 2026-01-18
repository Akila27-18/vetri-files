from django.conf import settings

def google_credentials(request):
    return {
        "GOOGLE_CLIENT_ID": settings.GOOGLE_CLIENT_ID,
        "GOOGLE_API_KEY": settings.GOOGLE_API_KEY,
    }
