from django.conf import settings


def contact_context(request):
    return {
        'whatsapp_number': getattr(settings, 'WHATSAPP_NUMBER', ''),
        'whatsapp_message': getattr(settings, 'WHATSAPP_MESSAGE', ''),
        'phone_number': getattr(settings, 'PHONE_NUMBER', ''),
        'phone_number_raw': getattr(settings, 'PHONE_NUMBER_RAW', ''),
    }
