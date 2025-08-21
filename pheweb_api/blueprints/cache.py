from flask_caching import Cache
from flask import Flask

cache = Cache(config={
    'CACHE_TYPE': 'NullCache',
    'CACHE_DEFAULT_TIMEOUT': 30
})

def init_cache(app:Flask, enable_cache:bool) -> None:
    if enable_cache:
        cache.config['CACHE_TYPE'] = 'SimpleCache'
    cache.init_app(app)
