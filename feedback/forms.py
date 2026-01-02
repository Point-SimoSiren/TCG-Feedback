from django import forms


class PublicFeedbackForm(forms.Form):
    ERROR_TEXT: dict[str, dict[str, str]] = {
        "fi": {
            "rating_invalid": "Arvosanan tulee olla 1–5.",
            "comment_placeholder": "Vapaa palaute (valinnainen)",
        },
        "sv": {
            "rating_invalid": "Betyget måste vara 1–5.",
            "comment_placeholder": "Kommentar (valfri)",
        },
        "en": {
            "rating_invalid": "Rating must be between 1 and 5.",
            "comment_placeholder": "Optional comment",
        },
    }

    rating = forms.ChoiceField(
        choices=[(str(i), str(i)) for i in range(5, 0, -1)],
        widget=forms.RadioSelect,
    )
    comment = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 4, "placeholder": ""}),
    )
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, lang: str = "fi", **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = lang if lang in self.ERROR_TEXT else "fi"
        self.fields["comment"].widget.attrs["placeholder"] = self.ERROR_TEXT[self.lang][
            "comment_placeholder"
        ]

    def clean_rating(self) -> int:
        raw = self.cleaned_data["rating"]
        rating = int(raw)
        if rating < 1 or rating > 5:
            raise forms.ValidationError(self.ERROR_TEXT[self.lang]["rating_invalid"])
        return rating
