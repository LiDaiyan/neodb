from django.contrib.auth.decorators import login_required
from django.core.exceptions import BadRequest, ObjectDoesNotExist, PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from common.utils import AuthedHttpRequest, get_uuid_or_404, target_identity_required
from mastodon.api import boost_toot_later
from takahe.utils import Takahe

from ..forms import *
from ..models import *


@login_required
def piece_replies(request: AuthedHttpRequest, piece_uuid: str):
    piece = get_object_or_404(Piece, uid=get_uuid_or_404(piece_uuid))
    if not piece.is_visible_to(request.user):
        raise PermissionDenied()
    replies = piece.get_replies(request.user.identity)
    return render(
        request, "replies.html", {"post": piece.latest_post, "replies": replies}
    )


@login_required
def post_replies(request: AuthedHttpRequest, post_id: int):
    replies = Takahe.get_replies_for_posts([post_id], request.user.identity.pk)
    return render(
        request, "replies.html", {"post": Takahe.get_post(post_id), "replies": replies}
    )


@require_http_methods(["POST"])
@login_required
def post_reply(request: AuthedHttpRequest, post_id: int):
    content = request.POST.get("content", "").strip()
    visibility = Takahe.Visibilities(int(request.POST.get("visibility", -1)))
    if not content:
        raise BadRequest()
    Takahe.reply_post(post_id, request.user.identity.pk, content, visibility)
    replies = Takahe.get_replies_for_posts([post_id], request.user.identity.pk)
    return render(
        request, "replies.html", {"post": Takahe.get_post(post_id), "replies": replies}
    )


@require_http_methods(["POST"])
@login_required
def post_boost(request: AuthedHttpRequest, post_id: int):
    # classic_repost = request.user.preference.mastodon_repost_mode == 1
    post = Takahe.get_post(post_id)
    if not post:
        raise BadRequest()
    if request.user.mastodon_site:
        boost_toot_later(request.user, post.object_uri)
    else:
        Takahe.boost_post(post_id, request.user.identity.pk)
    return render(request, "action_boost_post.html", {"post": post})


@require_http_methods(["POST"])
@login_required
def post_like(request: AuthedHttpRequest, post_id: int):
    Takahe.like_post(post_id, request.user.identity.pk)
    return render(request, "action_like_post.html", {"post": Takahe.get_post(post_id)})


@require_http_methods(["POST"])
@login_required
def post_unlike(request: AuthedHttpRequest, post_id: int):
    if request.method != "POST":
        raise BadRequest()
    Takahe.unlike_post(post_id, request.user.identity.pk)
    return render(request, "action_like_post.html", {"post": Takahe.get_post(post_id)})
