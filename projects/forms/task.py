from django import forms

from ..models import Category, Task


class TaskForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categories"].queryset = (
            Category.objects.filter(owner=user).order_by("name")
            if user is not None
            else Category.objects.none()
        )

    class Meta:
        model = Task

        fields = [
            "title",
            "description",
            "status",
            "priority",
            "due_date",
            "categories",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Task title",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Task description",
                    "rows": 4,
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "priority": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "due_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "categories": forms.SelectMultiple(
                attrs={
                    "class": "form-select",
                }
            ),
        }

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if not title:
            raise forms.ValidationError("Task title cannot be empty.")
        return title
