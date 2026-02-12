from django import forms
from apps.jobs.models import JobDescription

class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def clean(self, data, initial=None):
        if data in (None, "", []):
            if self.required:
                raise forms.ValidationError("Please upload at least one resume.")
            return []
        if isinstance(data, (list, tuple)):
            return [super().clean(d, initial) for d in data]
        return [super().clean(data, initial)]

class RankUploadForm(forms.Form):
    job = forms.ModelChoiceField(
        queryset=JobDescription.objects.none(),
        empty_label="-- Select Job Description --",
        widget=forms.Select(attrs={"class": "form-select"}),
        required=True,
    )
    resumes = MultipleFileField(
        required=True,
        widget=MultiFileInput(attrs={
            "multiple": True,
            "class": "form-control",
            "accept": ".pdf,.docx",
        }),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = JobDescription.objects.all()
        if user and not user.is_superuser:
            qs = qs.filter(created_by=user)
        self.fields["job"].queryset = qs.order_by("-id")
