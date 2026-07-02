"""数据缓存层，避免重复API调用"""
import json
import os
from datetime import datetime, timedelta

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', '.cache')


class DataCache:
    def __init__(self, ttl_minutes: int = 5):
        self.ttl = timedelta(minutes=ttl_minutes)
        os.makedirs(CACHE_DIR, exist_ok=True)

    def _key(self, prefix: str, **params) -> str:
        return f"{prefix}_{hash(frozenset(params.items()))}"

    def get(self, prefix: str, **params) -> dict | None:
        key = self._key(prefix, **params)
        path = os.path.join(CACHE_DIR, key)
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            age = datetime.now() - datetime.fromisoformat(data['_ts'])
            if age < self.ttl:
                return data
        return None

    def set(self, prefix: str, data: dict, **params):
        key = self._key(prefix, **params)
        path = os.path.join(CACHE_DIR, key)
        data['_ts'] = datetime.now().isoformat()
        with open(path, 'w') as f:
            json.dump(data, f, ensure_ascii=False)
