from django.contrib.auth import get_user_model
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.models import EmailAddress


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Gộp (merge) đăng nhập Google vào tài khoản có cùng email nếu đã tồn tại.
    Mặc định allauth sẽ báo lỗi "email đã được dùng"; adapter này thay vào đó
    sẽ liên kết SocialAccount với user hiện có.
    """

    def pre_social_login(self, request, sociallogin):
        # Nếu đã có SocialAccount (người này từng login Google), bỏ qua.
        if sociallogin.is_existing:
            return

        email = (sociallogin.user.email or "").strip().lower()
        if not email:
            return

        User = get_user_model()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return

        # Đánh dấu email đã verify và đặt primary
        EmailAddress.objects.get_or_create(
            user=user,
            email=user.email,
            defaults={"verified": True, "primary": True},
        )

        # Liên kết social account với user có sẵn
        sociallogin.connect(request, user)

