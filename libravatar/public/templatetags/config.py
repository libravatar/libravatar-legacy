from django import template

from libravatar import settings

register = template.Library()

@register.simple_tag
def site_name():
    return settings.SITE_NAME

@register.simple_tag
def libravatar_version():
    return settings.LIBRAVATAR_VERSION

@register.simple_tag
def avatar_url():
    return settings.AVATAR_URL

@register.simple_tag
def media_url():
    return settings.MEDIA_URL
