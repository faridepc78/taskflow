from django import forms

from ..models import Task


class TaskForm(forms.ModelForm):
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
