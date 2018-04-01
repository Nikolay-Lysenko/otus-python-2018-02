import hashlib
import json


def get_score(
        store, phone=None, email=None, birthday=None, gender=None,
        first_name=None, last_name=None
        ):
    key_parts = [
        first_name or "",
        last_name or "",
        birthday.strftime("%Y%m%d") if birthday is not None else "",
    ]
    key = "uid:" + hashlib.md5("".join(key_parts)).hexdigest()
    # Try get from cache, else fall back to heavy calculation.
    score = store.cache_get(key) or 0
    if score:
        return float(score)  # `memcached` values are strings.
    if phone:
        score += 1.5
    if email:
        score += 1.5
    if birthday and gender:
        score += 1.5
    if first_name and last_name:
        score += 0.5
    # Cache for 60 minutes.
    store.cache_set(key, score,  60 * 60)
    return score


def get_interests(store, cid):
    r = store.get("i:%s" % cid)
    return json.loads(r) if r else []
