import re
from datetime import datetime
from functools import cached_property

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from markdownify import markdownify as md
from markdownx.models import MarkdownxField

from catalog.models import Item
from mastodon.api import boost_toot_later, share_review
from users.models import APIdentity

from .common import Content
from .rating import Rating
from .renderers import render_md

_RE_HTML_TAG = re.compile(r"<[^>]*>")
_RE_SPOILER_TAG = re.compile(r'<(div|span)\sclass="spoiler">.*</(div|span)>')


class Review(Content):
    url_path = "review"
    title = models.CharField(max_length=500, blank=False, null=False)
    body = MarkdownxField()

    @property
    def html_content(self):
        return render_md(self.body)

    @property
    def plain_content(self):
        html = render_md(self.body)
        return _RE_HTML_TAG.sub(
            " ", _RE_SPOILER_TAG.sub("***", html.replace("\n", " "))
        )

    @property
    def ap_object(self):
        return {
            "id": self.absolute_url,
            "type": "Review",
            "name": self.title,
            # "content": self.html_content,
            "content": self.body,
            "mediaType": "text/markdown",
            "published": self.created_time.isoformat(),
            "updated": self.edited_time.isoformat(),
            "attributedTo": self.owner.actor_uri,
            "withRegardTo": self.item.absolute_url,
            "href": self.absolute_url,
        }

    @classmethod
    def update_by_ap_object(cls, owner, item, obj, post_id, visibility):
        p = cls.objects.filter(owner=owner, item=item).first()
        if p and p.edited_time >= datetime.fromisoformat(obj["updated"]):
            return p  # incoming ap object is older than what we have, no update needed
        content = (
            obj["content"]
            if obj.get("mediaType") == "text/markdown"
            else md(obj["content"])
        )
        d = {
            "title": obj["name"],
            "body": content,
            "local": False,
            "remote_id": obj["id"],
            "visibility": visibility,
            "created_time": datetime.fromisoformat(obj["published"]),
            "edited_time": datetime.fromisoformat(obj["updated"]),
        }
        p, _ = cls.objects.update_or_create(owner=owner, item=item, defaults=d)
        p.link_post_id(post_id)
        return p

    @cached_property
    def mark(self):
        from .mark import Mark

        m = Mark(self.owner, self.item)
        m.review = self
        return m

    @cached_property
    def rating_grade(self):
        return Rating.get_item_rating(self.item, self.owner)

    @classmethod
    def update_item_review(
        cls,
        item: Item,
        owner: APIdentity,
        title: str | None,
        body: str | None,
        visibility=0,
        created_time=None,
        share_to_mastodon: bool = False,
    ):
        from takahe.utils import Takahe

        if title is None:
            review = Review.objects.filter(owner=owner, item=item).first()
            if review is not None:
                review.delete()
            return None
        defaults = {
            "title": title,
            "body": body,
            "visibility": visibility,
        }
        if created_time:
            defaults["created_time"] = (
                created_time if created_time < timezone.now() else timezone.now()
            )
        review, created = cls.objects.update_or_create(
            item=item, owner=owner, defaults=defaults
        )
        post = Takahe.post_review(review, created)
        if post and share_to_mastodon:
            if (
                owner.user.preference.mastodon_repost_mode == 1
                and owner.user.mastodon_site
            ):
                share_review(review)
            else:
                boost_toot_later(owner.user, post.url)
        return review
