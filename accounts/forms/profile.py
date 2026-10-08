from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from PIL import Image, UnidentifiedImageError

from ..models import Profile


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField()
    remove_avatar = forms.BooleanField(required=False)

    class Meta:
        model = Profile
        fields = ["avatar", "bio"]
        widgets = {
            "avatar": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }

    def __init__(self, *args, user: User, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        self.fields["first_name"].initial = user.first_name
        self.fields["last_name"].initial = user.last_name
        self.fields["email"].initial = user.email
        self.fields["email"].widget.attrs["readonly"] = True
        self.fields["email"].help_text = "Email changes require verification and are currently disabled."

        for field_name in ("first_name", "last_name", "email"):
            self.fields[field_name].widget.attrs["class"] = "form-control"

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if email != self.user.email.strip().lower():
            raise forms.ValidationError("Email changes require verification and are not available here.")
        if User.objects.exclude(pk=self.user.pk).filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if avatar and hasattr(avatar, "size"):
            if avatar.size > 3 * 1024 * 1024:
                raise ValidationError("Profile photo must be 3 MB or less.")
            try:
                image = Image.open(avatar)
                if image.format not in {"JPEG", "PNG", "WEBP", "GIF"}:
                    raise ValidationError("Use a JPEG, PNG, WebP or GIF image.")
                image.verify()
                avatar.seek(0)
            except (UnidentifiedImageError, OSError, ValueError) as exc:
                raise ValidationError("Upload a valid image.") from exc
        return avatar

    def save(self, commit=True):
        profile = super().save(commit=False)

        self.user.first_name = self.cleaned_data["first_name"].strip()
        self.user.last_name = self.cleaned_data["last_name"].strip()
        self.user.email = self.cleaned_data["email"]

        old_name = profile.avatar.name if profile.avatar else None
        if self.cleaned_data.get("remove_avatar"):
            profile.avatar = None

        if commit:
            self.user.save(update_fields=["first_name", "last_name", "email"])
            profile.save()
            if old_name and old_name != (profile.avatar.name if profile.avatar else None):
                storage = profile._meta.get_field("avatar").storage
                transaction.on_commit(lambda name=old_name: storage.delete(name))

        return profile
