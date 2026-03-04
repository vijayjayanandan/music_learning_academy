from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class CustomAccountAdapter(DefaultAccountAdapter):
    """Custom adapter to auto-generate username from email."""

    def populate_username(self, request, user):
        from allauth.account.utils import user_username

        email = user.email or ""
        base = email.split("@")[0] if email else "user"
        username = base
        i = 1
        User = user.__class__
        while User.objects.filter(username=username).exists():
            username = f"{base}{i}"
            i += 1
        user_username(user, username)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Links social accounts to existing users by email, sets verified flag."""

    def pre_social_login(self, request, sociallogin):
        """If a user with this email already exists, connect the social account."""
        email = sociallogin.account.extra_data.get("email") or ""
        if not email:
            return
        if sociallogin.is_existing:
            return

        from apps.accounts.models import User

        try:
            user = User.objects.get(email__iexact=email)
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            pass

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        user.email_verified = True
        data = sociallogin.account.extra_data
        if not user.first_name:
            user.first_name = data.get("given_name") or data.get("first_name") or ""
        if not user.last_name:
            user.last_name = data.get("family_name") or data.get("last_name") or ""
        user.save(update_fields=["email_verified", "first_name", "last_name"])
        return user

    def is_auto_signup_allowed(self, request, sociallogin):
        return True
