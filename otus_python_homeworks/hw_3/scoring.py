import hashlib
import json
import datetime


def get_score(
        storage, phone=None, email=None, birthday=None, gender=None,
        first_name=None, last_name=None
        ):
    key_parts = [
        first_name or "",
        last_name or "",
        datetime.datetime.strptime(birthday, '%d.%m.%Y').strftime("%Y%m%d")
        if birthday is not None else "",
    ]
    key = "uid:" + hashlib.md5("".join(key_parts)).hexdigest()
    # Try get from cache, else fall back to calculation considered to be heavy.
    score = storage.cache_get(key) or 0
    if score:
        return float(score)
    if phone:
        score += 1.5
    if email:
        score += 1.5
    if birthday and gender:
        score += 1.5
    if first_name and last_name:
        score += 0.5
    storage.cache_set(key, score,  60 * 60)
    return score


def get_interests(storage, cid):
    r = storage.get("i:%s" % cid)
    return json.loads(r) if r else []
