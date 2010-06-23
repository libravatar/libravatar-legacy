import settings

"""
Default useful variables for the base page template.
"""
def basepage(request):
    context = {}
    context["site_name"] = settings.SITE_NAME
    context["libravatar_version"] = settings.LIBRAVATAR_VERSION
    context["avatar_url"] = settings.AVATAR_URL
    context["media_url"] = settings.MEDIA_URL
    context["disable_signup"] = settings.DISABLE_SIGNUP
    return context

