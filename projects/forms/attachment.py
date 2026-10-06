from django import forms

from ..models import TaskAttachment

MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024


class TaskAttachmentForm(forms.ModelForm):
    class Meta:
        model = TaskAttachment
        fields = ["file"]
        widgets = {
            "file": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                }
            ),
        }

    def clean_file(self):
        uploaded_file = self.cleaned_data["file"]

        if uploaded_file.size > MAX_ATTACHMENT_SIZE:
            raise forms.ValidationError("File size must be 10 MB or less.")

        return uploaded_file
