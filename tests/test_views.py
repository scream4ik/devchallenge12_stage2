from app.main import create_app
from app.settings import Settings

import aioredis

import json


async def test_data(test_client):
    """
    tests for HandleView
    :return: 200
    """
    client = await test_client(create_app)

    # request post without data
    resp = await client.post('/')
    assert resp.status == 400

    # request post with empty data
    resp = await client.post('/', json={})
    assert resp.status == 400

    # request post with invalid url
    data = {
        'urls': ['http://invalid-domain.qwerty']
    }
    resp = await client.post('/', json=data)
    assert resp.status == 200
    resp_json = await resp.json()
    assert list(resp_json[0].values())[0]['is_valid'] is False
    assert list(resp_json[0].values())[0]['reason'] == 'Something went wrong'

    # request post with invalid data
    data = {
        'urls': ['http://aaaa']
    }
    resp = await client.post('/', json=data)
    assert resp.status == 200
    resp_json = await resp.json()
    assert list(resp_json[0].values())[0]['is_valid'] is False
    assert list(resp_json[0].values())[0]['reason'] == 'Invalid url'

    # request post to our test page
    data = {
        'urls': ['http://{}:{}/test'.format(client.host, client.port)]
    }
    resp = await client.post('/', json=data)
    assert resp.status == 200
    resp_json = await resp.json()
    assert list(resp_json[0].values())[0]['is_valid'] is True
    assert list(resp_json[0].values())[0]['unused_css_percentage'] == 47
    assert list(resp_json[0].values())[0]['css'] == '@charset "utf-8";.content{display:block}h1{font-size:16px}'

    # request post with redirect url
    data = {
        'urls': ['http://google.com']
    }
    resp = await client.post('/', json=data)
    assert resp.status == 200
    resp_json = await resp.json()
    assert list(resp_json[0].values())[0]['is_valid'] is False
    assert list(resp_json[0].values())[0]['reason'] == 'Got redirect'


async def test_cache(test_client):
    """
    tests for cache data
    """
    client = await test_client(create_app)
    settings = Settings()

    data = {
        'urls': ['https://google.com']
    }
    resp = await client.post('/', json=data)
    assert resp.status == 200
    resp_json = await resp.json()

    redis_conn = await aioredis.create_connection(
        settings.REDIS_URL, encoding='utf-8'
    )
    pickled_object = json.loads(
        await redis_conn.execute('get', 'url::https://google.com')
    )

    assert resp_json[0] == pickled_object


async def test_cache_invalidate(test_client):
    """
    tests for CacheInvalidateView
    """
    client = await test_client(create_app)
    settings = Settings()

    redis_conn = await aioredis.create_connection(
        settings.REDIS_URL, encoding='utf-8'
    )
    await redis_conn.execute(
        'set', 'url::https://google.com', json.dumps({'is_valid': True})
    )

    # invalidate all cache
    resp = await client.get('/cache-invalidate')
    assert resp.status == 200
    resp_json = await resp.json()
    assert resp_json['success'] is True

    url_data = await redis_conn.execute('get', 'url::https://google.com')
    assert url_data is None

    # invalidate wrong url
    resp = await client.get('/cache-invalidate?url=dsfdsf')
    assert resp.status == 200
    assert resp_json['success'] is True

    await redis_conn.execute(
        'set', 'url::https://google.com', json.dumps({'is_valid': True})
    )
    # invalidate exists url
    resp = await client.get('/cache-invalidate?url=https://google.com')
    assert resp.status == 200
    assert resp_json['success'] is True
