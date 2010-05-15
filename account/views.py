from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User


@login_required
def profile(request):
    u = request.user
    return render_to_response('account/profile.html', { 'user': u })

def new(request):
    username = request.POST['username']
    password = request.POST['password']
    password2 = request.POST['password2']

    errors = False
    if not username:
        errors = True
        username_error = 'Invalid username'
    if not password:
        errors = True
        password_error = 'Invalid password'
    if password != password2:
        errors = True
        password2_error = 'Passwords don\'t match'

    if errors:
        return render_to_response('account/new.html', {
            'username' : username,
            'password' : password,
            'password2' : password2,
            'username_error': username_error,
            'password_error' : password_error,
            'password2_error': password2_error,
    })

    user = User.objects.create_user(username, '', password)
    if user is None:
        # TODO: Return an error message

    user = authenticate(username=username, password=password)
    if user is None:
        # TODO: Return an 'invalid login' error message.

    login(request, user)
    # Redirect to a success page.
        
