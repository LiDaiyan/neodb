from django import forms
from django.utils.translation import gettext_lazy as _
from markdownx.fields import MarkdownxFormField

from common.forms import PreviewImageInput

from .models import *


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["id", "item", "title", "body", "visibility"]
        widgets = {
            "item": forms.TextInput(attrs={"hidden": ""}),
        }

    title = forms.CharField(label=_("评论标题"))
    body = MarkdownxFormField(label=_("评论正文 (Markdown格式可参考下方语法范例)"), strip=False)
    share_to_mastodon = forms.BooleanField(
        label=_("分享到联邦宇宙"), initial=False, required=False
    )
    id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    visibility = forms.TypedChoiceField(
        label=_("可见性"),
        initial=0,
        coerce=int,
        choices=VisibilityType.choices,
        widget=forms.RadioSelect,
    )


COLLABORATIVE_CHOICES = [
    (0, _("仅限创建者")),
    (1, _("创建者及其互关用户")),
]


class CollectionForm(forms.ModelForm):
    # id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    title = forms.CharField(label=_("标题"))
    brief = MarkdownxFormField(label=_("介绍 (Markdown)"), strip=False)
    # share_to_mastodon = forms.BooleanField(label=_("分享到联邦宇宙"), initial=True, required=False)
    visibility = forms.TypedChoiceField(
        label=_("可见性"),
        initial=0,
        coerce=int,
        choices=VisibilityType.choices,
        widget=forms.RadioSelect,
    )
    collaborative = forms.TypedChoiceField(
        label=_("协作整理权限"),
        initial=0,
        coerce=int,
        choices=COLLABORATIVE_CHOICES,
        widget=forms.RadioSelect,
    )

    class Meta:
        model = Collection
        fields = [
            "title",
            "cover",
            "visibility",
            "collaborative",
            "brief",
        ]

        widgets = {
            "cover": PreviewImageInput(),
        }
