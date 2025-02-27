import functools
import html
import random
import re
import string
import time
from urllib.parse import quote

import django_rq
import requests
from django.conf import settings
from loguru import logger

from mastodon.utils import rating_to_emoji

from .models import MastodonApplication

# See https://docs.joinmastodon.org/methods/accounts/

# returns user info
# retruns the same info as verify account credentials
# GET
API_GET_ACCOUNT = "/api/v1/accounts/:id"

# returns user info if valid, 401 if invalid
# GET
API_VERIFY_ACCOUNT = "/api/v1/accounts/verify_credentials"

# obtain token
# GET
API_OBTAIN_TOKEN = "/oauth/token"

# obatin auth code
# GET
API_OAUTH_AUTHORIZE = "/oauth/authorize"

# revoke token
# POST
API_REVOKE_TOKEN = "/oauth/revoke"

# relationships
# GET
API_GET_RELATIONSHIPS = "/api/v1/accounts/relationships"

# toot
# POST
API_PUBLISH_TOOT = "/api/v1/statuses"

# create new app
# POST
API_CREATE_APP = "/api/v1/apps"

# search
# GET
API_SEARCH = "/api/v2/search"

USER_AGENT = settings.NEODB_USER_AGENT

get = functools.partial(requests.get, timeout=settings.MASTODON_TIMEOUT)
put = functools.partial(requests.put, timeout=settings.MASTODON_TIMEOUT)
post = functools.partial(requests.post, timeout=settings.MASTODON_TIMEOUT)


def get_api_domain(domain):
    app = MastodonApplication.objects.filter(domain_name=domain).first()
    return app.api_domain if app and app.api_domain else domain


# low level api below


def boost_toot(site, token, toot_url):
    domain = get_api_domain(site)
    headers = {
        "User-Agent": USER_AGENT,
        "Authorization": f"Bearer {token}",
    }
    url = (
        "https://"
        + domain
        + API_SEARCH
        + "?type=statuses&resolve=true&q="
        + quote(toot_url)
    )
    try:
        response = get(url, headers=headers)
        if response.status_code != 200:
            logger.warning(
                f"Error search {toot_url} on {domain} {response.status_code}"
            )
            return None
        j = response.json()
        if "statuses" in j and len(j["statuses"]) > 0:
            s = j["statuses"][0]
            url_id = toot_url.split("/posts/")[-1]
            url_id2 = s["uri"].split("/posts/")[-1]
            if s["uri"] != toot_url and s["url"] != toot_url and url_id != url_id2:
                logger.warning(
                    f"Error status url mismatch {s['uri']} or {s['uri']} != {toot_url}"
                )
                return None
            if s["reblogged"]:
                logger.warning(f"Already boosted {toot_url}")
                # TODO unboost and boost again?
                return None
            url = (
                "https://"
                + domain
                + API_PUBLISH_TOOT
                + "/"
                + j["statuses"][0]["id"]
                + "/reblog"
            )
            response = post(url, headers=headers)
            if response.status_code != 200:
                logger.warning(
                    f"Error search {toot_url} on {domain} {response.status_code}"
                )
                return None
            return response.json()
    except Exception:
        logger.warning(f"Error search {toot_url} on {domain}")
        return None


def boost_toot_later(user, post_url):
    if user and user.mastodon_token and user.mastodon_site and post_url:
        django_rq.get_queue("fetch").enqueue(
            boost_toot, user.mastodon_site, user.mastodon_token, post_url
        )


def post_toot_later(
    user,
    content,
    visibility,
    local_only=False,
    update_id=None,
    spoiler_text=None,
    img=None,
    img_name=None,
    img_type=None,
):
    if user and user.mastodon_token and user.mastodon_site and content:
        django_rq.get_queue("fetch").enqueue(
            post_toot,
            user.mastodon_site,
            content,
            visibility,
            user.mastodon_token,
            local_only,
            update_id,
            spoiler_text,
            img,
            img_name,
            img_type,
        )


def post_toot(
    site,
    content,
    visibility,
    token,
    local_only=False,
    update_id=None,
    spoiler_text=None,
    img=None,
    img_name=None,
    img_type=None,
):
    headers = {
        "User-Agent": USER_AGENT,
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": random_string_generator(16),
    }
    media_id = None
    if img and img_name and img_type:
        try:
            media_id = (
                requests.post(
                    "https://" + get_api_domain(site) + "/api/v1/media",
                    headers=headers,
                    data={},
                    files={"file": (img_name, img, img_type)},
                )
                .json()
                .get("id")
            )
            ready = False
            while ready is False:
                time.sleep(3)
                j = requests.get(
                    "https://" + get_api_domain(site) + "/api/v1/media/" + media_id,
                    headers=headers,
                ).json()
                ready = j.get("url") is not None
        except Exception as e:
            logger.warning(f"Error uploading image {e}")
        headers["Idempotency-Key"] = random_string_generator(16)
    response = None
    url = "https://" + get_api_domain(site) + API_PUBLISH_TOOT
    payload = {
        "status": content,
        "visibility": visibility,
    }
    if media_id:
        payload["media_ids[]"] = [media_id]
    if spoiler_text:
        payload["spoiler_text"] = spoiler_text
    if local_only:
        payload["local_only"] = True
    try:
        if update_id:
            response = put(url + "/" + update_id, headers=headers, data=payload)
        if not update_id or (response is not None and response.status_code != 200):
            headers["Idempotency-Key"] = random_string_generator(16)
            response = post(url, headers=headers, data=payload)
        if response is not None and response.status_code == 201:
            response.status_code = 200
        if response is not None and response.status_code != 200:
            logger.warning(f"Error {url} {response.status_code}")
    except Exception as e:
        logger.warning(f"Error posting {e}")
        response = None
    return response


def create_app(domain_name):
    # naive protocal strip
    is_http = False
    if domain_name.startswith("https://"):
        domain_name = domain_name.replace("https://", "")
    elif domain_name.startswith("http://"):
        is_http = True
        domain_name = domain_name.replace("http://", "")
    if domain_name.endswith("/"):
        domain_name = domain_name[0:-1]

    if not is_http:
        url = "https://" + domain_name + API_CREATE_APP
    else:
        url = "http://" + domain_name + API_CREATE_APP

    payload = {
        "client_name": settings.SITE_INFO["site_name"],
        "scopes": settings.MASTODON_CLIENT_SCOPE,
        "redirect_uris": settings.REDIRECT_URIS,
        "website": settings.SITE_INFO["site_url"],
    }

    response = post(url, data=payload, headers={"User-Agent": USER_AGENT})
    return response


def webfinger(site, username) -> dict | None:
    url = f"https://{site}/.well-known/webfinger?resource=acct:{username}@{site}"
    try:
        response = get(url, headers={"User-Agent": USER_AGENT})
        if response.status_code != 200:
            logger.warning(f"Error webfinger {username}@{site} {response.status_code}")
            return None
        j = response.json()
        return j
    except Exception:
        logger.warning(f"Error webfinger {username}@{site}")
        return None


# utils below
def random_string_generator(n):
    s = string.ascii_letters + string.punctuation + string.digits
    return "".join(random.choice(s) for i in range(n))


def verify_account(site, token):
    url = "https://" + get_api_domain(site) + API_VERIFY_ACCOUNT
    try:
        response = get(
            url, headers={"User-Agent": USER_AGENT, "Authorization": f"Bearer {token}"}
        )
        return response.status_code, (
            response.json() if response.status_code == 200 else None
        )
    except Exception:
        return -1, None


def get_related_acct_list(site, token, api):
    url = "https://" + get_api_domain(site) + api
    results = []
    while url:
        try:
            response = get(
                url,
                headers={"User-Agent": USER_AGENT, "Authorization": f"Bearer {token}"},
            )
            url = None
            if response.status_code == 200:
                results.extend(
                    map(
                        lambda u: (
                            u["acct"]
                            if u["acct"].find("@") != -1
                            else u["acct"] + "@" + site
                        )
                        if "acct" in u
                        else u,
                        response.json(),
                    )
                )
                if "Link" in response.headers:
                    for ls in response.headers["Link"].split(","):
                        li = ls.strip().split(";")
                        if li[1].strip() == 'rel="next"':
                            url = li[0].strip().replace(">", "").replace("<", "")
        except Exception as e:
            logger.warning(f"Error GET {url} : {e}")
            url = None
    return results


class TootVisibilityEnum:
    PUBLIC = "public"
    PRIVATE = "private"
    DIRECT = "direct"
    UNLISTED = "unlisted"


def detect_server_info(login_domain) -> tuple[str, str, str]:
    url = f"https://{login_domain}/api/v1/instance"
    try:
        response = get(url, headers={"User-Agent": USER_AGENT})
    except Exception as e:
        logger.warning(f"Error connecting {login_domain}: {e}")
        raise Exception(f"无法连接 {login_domain}")
    if response.status_code != 200:
        logger.warning(f"Error connecting {login_domain}: {response.status_code}")
        raise Exception(f"实例 {login_domain} 返回错误，代码: {response.status_code}")
    try:
        j = response.json()
        domain = j["uri"].lower().split("//")[-1].split("/")[0]
    except Exception as e:
        logger.warning(f"Error connecting {login_domain}: {e}")
        raise Exception(f"实例 {login_domain} 返回信息无法识别")
    server_version = j["version"]
    api_domain = domain
    if domain != login_domain:
        url = f"https://{domain}/api/v1/instance"
        try:
            response = get(url, headers={"User-Agent": USER_AGENT})
            j = response.json()
        except:
            api_domain = login_domain
    logger.info(
        f"detect_server_info: {login_domain} {domain} {api_domain} {server_version}"
    )
    return domain, api_domain, server_version


def get_or_create_fediverse_application(login_domain):
    domain = login_domain
    app = MastodonApplication.objects.filter(domain_name__iexact=domain).first()
    if not app:
        app = MastodonApplication.objects.filter(api_domain__iexact=domain).first()
    if app:
        return app
    if not settings.MASTODON_ALLOW_ANY_SITE:
        logger.warning(f"Disallowed to create app for {domain}")
        raise Exception("不支持其它实例登录")
    if settings.SITE_DOMAIN.lower() == login_domain.lower():
        raise ValueError("必须使用其它实例登录")
    domain, api_domain, server_version = detect_server_info(login_domain)
    if (
        settings.SITE_DOMAIN.lower() == domain.lower()
        or settings.SITE_DOMAIN.lower() == api_domain.lower()
    ):
        raise ValueError("必须使用其它实例登录")
    if "neodb/" in server_version:
        raise ValueError("必须使用非NeoDB实例登录")
    if login_domain != domain:
        app = MastodonApplication.objects.filter(domain_name__iexact=domain).first()
        if app:
            return app
    response = create_app(api_domain)
    if response.status_code != 200:
        logger.error(
            f"Error creating app for {domain} on {api_domain}: {response.status_code}"
        )
        raise Exception("实例注册应用失败，代码: " + str(response.status_code))
    try:
        data = response.json()
    except Exception:
        logger.error(f"Error creating app for {domain}: unable to parse response")
        raise Exception("实例注册应用失败，返回内容无法识别")
    app = MastodonApplication.objects.create(
        domain_name=domain.lower(),
        api_domain=api_domain.lower(),
        server_version=server_version,
        app_id=data["id"],
        client_id=data["client_id"],
        client_secret=data["client_secret"],
        vapid_key=data["vapid_key"] if "vapid_key" in data else "",
    )
    return app


def get_mastodon_login_url(app, login_domain, request):
    url = settings.REDIRECT_URIS
    version = app.server_version or ""
    scope = (
        settings.MASTODON_LEGACY_CLIENT_SCOPE
        if "Pixelfed" in version
        else settings.MASTODON_CLIENT_SCOPE
    )
    return (
        "https://"
        + login_domain
        + "/oauth/authorize?client_id="
        + app.client_id
        + "&scope="
        + quote(scope)
        + "&redirect_uri="
        + url
        + "&response_type=code"
    )


def obtain_token(site, request, code):
    """Returns token if success else None."""
    mast_app = MastodonApplication.objects.get(domain_name=site)
    redirect_uri = settings.REDIRECT_URIS
    payload = {
        "client_id": mast_app.client_id,
        "client_secret": mast_app.client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
        "code": code,
    }
    headers = {"User-Agent": USER_AGENT}
    auth = None
    if mast_app.is_proxy:
        url = "https://" + mast_app.proxy_to + API_OBTAIN_TOKEN
    else:
        url = (
            "https://"
            + (mast_app.api_domain or mast_app.domain_name)
            + API_OBTAIN_TOKEN
        )
    try:
        response = post(url, data=payload, headers=headers, auth=auth)
        # {"token_type":"bearer","expires_in":7200,"access_token":"VGpkOEZGR3FQRDJ5NkZ0dmYyYWIwS0dqeHpvTnk4eXp0NV9nWDJ2TEpmM1ZTOjE2NDg3ODMxNTU4Mzc6MToxOmF0OjE","scope":"block.read follows.read offline.access tweet.write users.read mute.read","refresh_token":"b1pXbGEzeUF1WE5yZHJOWmxTeWpvMTBrQmZPd0czLU0tQndZQTUyU3FwRDVIOjE2NDg3ODMxNTU4Mzg6MToxOnJ0OjE"}
        if response.status_code != 200:
            logger.warning(f"Error {url} {response.status_code}")
            return None, None
    except Exception as e:
        logger.warning(f"Error {url} {e}")
        return None, None
    data = response.json()
    return data.get("access_token"), data.get("refresh_token", "")


def refresh_access_token(site, refresh_token):
    pass


def revoke_token(site, token):
    mast_app = MastodonApplication.objects.get(domain_name=site)

    payload = {
        "client_id": mast_app.client_id,
        "client_secret": mast_app.client_secret,
        "token": token,
    }

    if mast_app.is_proxy:
        url = "https://" + mast_app.proxy_to + API_REVOKE_TOKEN
    else:
        url = "https://" + get_api_domain(site) + API_REVOKE_TOKEN
    post(url, data=payload, headers={"User-Agent": USER_AGENT})


def get_status_id_by_url(url):
    if not url:
        return None
    r = re.match(
        r".+/(\w+)$", url
    )  # might be re.match(r'.+/([^/]+)$', u) if Pleroma supports edit
    return r[1] if r else None


def get_spoiler_text(text, item):
    if text.find(">!") != -1:
        spoiler_text = f"关于《{item.display_title}》 可能有关键情节等敏感内容"
        return spoiler_text, text.replace(">!", "").replace("!<", "")
    else:
        return None, text


def get_toot_visibility(visibility, user):
    if visibility == 2:
        return TootVisibilityEnum.DIRECT
    elif visibility == 1:
        return TootVisibilityEnum.PRIVATE
    elif user.preference.post_public_mode == 0:
        return TootVisibilityEnum.PUBLIC
    else:
        return TootVisibilityEnum.UNLISTED


def share_comment(comment):
    from catalog.common import ItemCategory

    user = comment.owner.user
    visibility = get_toot_visibility(comment.visibility, user)
    tags = (
        "\n"
        + user.preference.mastodon_append_tag.replace(
            "[category]", str(ItemCategory(comment.item.category).label)
        )
        if user.preference.mastodon_append_tag
        else ""
    )
    content = f"评论《{comment.item.display_title}》\n{comment.text}\n{comment.item.absolute_url}{tags}"
    update_id = None
    if comment.metadata.get(
        "shared_link"
    ):  # "https://mastodon.social/@username/1234567890"
        r = re.match(
            r".+/(\w+)$", comment.metadata.get("shared_link")
        )  # might be re.match(r'.+/([^/]+)$', u) if Pleroma supports edit
        update_id = r[1] if r else None
    response = post_toot(
        user.mastodon_site, content, visibility, user.mastodon_token, False, update_id
    )
    if response is not None and response.status_code in [200, 201]:
        j = response.json()
        if "url" in j:
            comment.metadata["shared_link"] = j["url"]
            comment.save()
        return True
    else:
        return False


def share_mark(mark, post_as_new=False):
    from catalog.common import ItemCategory

    user = mark.owner.user
    visibility = get_toot_visibility(mark.visibility, user)
    tags = (
        "\n"
        + user.preference.mastodon_append_tag.replace(
            "[category]", str(ItemCategory(mark.item.category).label)
        )
        if user.preference.mastodon_append_tag
        else ""
    )
    site = MastodonApplication.objects.filter(domain_name=user.mastodon_site).first()
    stars = rating_to_emoji(
        mark.rating_grade,
        site.star_mode if site else 0,
    )
    spoiler_text, txt = get_spoiler_text(mark.comment_text or "", mark.item)
    content = f"{mark.action_label_for_feed}《{mark.item.display_title}》{stars}\n{mark.item.absolute_url}\n{txt}{tags}"
    update_id = (
        None
        if post_as_new
        else get_status_id_by_url((mark.shelfmember.metadata or {}).get("shared_link"))
    )
    response = post_toot(
        user.mastodon_site,
        content,
        visibility,
        user.mastodon_token,
        False,
        update_id,
        spoiler_text,
    )
    if response is not None and response.status_code in [200, 201]:
        j = response.json()
        if "url" in j:
            mark.shelfmember.metadata = {"shared_link": j["url"]}
            mark.shelfmember.save(update_fields=["metadata"])
        return True, 200
    else:
        logger.warning(response)
        return False, response.status_code if response is not None else -1


def share_review(review):
    from catalog.common import ItemCategory

    user = review.owner.user
    visibility = get_toot_visibility(review.visibility, user)
    tags = (
        "\n"
        + user.preference.mastodon_append_tag.replace(
            "[category]", str(ItemCategory(review.item.category).label)
        )
        if user.preference.mastodon_append_tag
        else ""
    )
    content = f"发布了关于《{review.item.display_title}》的评论\n{review.title}\n{review.absolute_url}{tags}"
    update_id = None
    if review.metadata.get(
        "shared_link"
    ):  # "https://mastodon.social/@username/1234567890"
        r = re.match(
            r".+/(\w+)$", review.metadata.get("shared_link")
        )  # might be re.match(r'.+/([^/]+)$', u) if Pleroma supports edit
        update_id = r[1] if r else None
    response = post_toot(
        user.mastodon_site, content, visibility, user.mastodon_token, False, update_id
    )
    if response is not None and response.status_code in [200, 201]:
        j = response.json()
        if "url" in j:
            review.metadata["shared_link"] = j["url"]
            review.save()
        return True
    else:
        return False


def share_collection(collection, comment, user, visibility_no, link):
    visibility = get_toot_visibility(visibility_no, user)
    tags = (
        "\n" + user.preference.mastodon_append_tag.replace("[category]", "收藏单")
        if user.preference.mastodon_append_tag
        else ""
    )
    user_str = (
        "我"
        if user == collection.owner.user
        else (
            " @" + collection.owner.user.mastodon_acct + " "
            if collection.owner.user.mastodon_acct
            else " " + collection.owner.username + " "
        )
    )
    content = f"分享{user_str}的收藏单《{collection.title}》\n{link}\n{comment}{tags}"
    response = post_toot(user.mastodon_site, content, visibility, user.mastodon_token)
    if response is not None and response.status_code in [200, 201]:
        return True
    else:
        return False
