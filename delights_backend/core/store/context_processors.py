from django.conf import settings


def contact_context(request):
    whatsapp_number = str(getattr(settings, 'WHATSAPP_NUMBER', '') or '').strip()
    whatsapp_digits = ''.join(ch for ch in whatsapp_number if ch.isdigit())
    if len(whatsapp_digits) == 10:
        whatsapp_link_number = f"91{whatsapp_digits}"
    else:
        whatsapp_link_number = whatsapp_digits

    return {
        'whatsapp_number': whatsapp_link_number,
        'whatsapp_message': getattr(settings, 'WHATSAPP_MESSAGE', ''),
        'phone_number': getattr(settings, 'PHONE_NUMBER', ''),
        'phone_number_raw': getattr(settings, 'PHONE_NUMBER_RAW', ''),
    }
