from aiohttp import web

from .settings import Settings

from pyppeteer import launch
from pyppeteer.browser import Browser
from pyppeteer.errors import (
    PageError, BrowserError, NetworkError, TimeoutError
)
import validators
from css_html_js_minify import css_minify
import aioredis

import json
from json.decoder import JSONDecodeError


class HandleView(web.View):
    """
    Endpoint for minimize only used css styles for given url
    """

    async def post(self) -> web.Response:
        # request without any data
        try:
            data = await self.request.json()
        except JSONDecodeError:
            raise web.HTTPBadRequest

        # request with wrong data
        if 'urls' not in data:
            raise web.HTTPBadRequest

        result = []
        browser = await launch(args=['--no-sandbox'])

        for url in data['urls']:
            result.append(await self.proxy(url, browser))

        await browser.close()

        return web.json_response(result)

    async def proxy(self, url: str, browser: Browser) -> dict:
        """
        Method try return url results from cache.
        If it empty, handle data and save to cache
        """
        settings = Settings()
        redis_conn = await aioredis.create_connection(
            settings.REDIS_URL, encoding='utf-8'
        )

        data = await redis_conn.execute('get', 'url::{}'.format(url))
        if not data:
            if validators.url(url):
                data = await self.handler(url, browser)
            else:
                data = {
                    url: {'is_valid': False, 'reason': 'Invalid url'}
                }
            await redis_conn.execute(
                'set', 'url::{}'.format(url), json.dumps(data)
            )
            await redis_conn.execute(
                'expire', 'url::{}'.format(url), settings.URL_EXPIRE
            )
        else:
            data = json.loads(data)

        return data

    async def handler(self, url: str, browser: Browser) -> dict:
        """
        Handler get information about css styles
        and generate dict with results data
        """
        try:
            page = await browser.newPage()

            await page.coverage.startCSSCoverage()
            resp = await page.goto(url)

            if resp is None:
                await browser.close()
                return {
                    url: {'is_valid': False, 'reason': 'Something went wrong'}
                }

            if not hasattr(resp, 'url') or resp.url != url:
                await browser.close()
                return {url: {'is_valid': False, 'reason': 'Got redirect'}}

            css_coverage = await page.coverage.stopCSSCoverage()

            result = {url: {'is_valid': True}}
            for data in filter(lambda x: x['ranges'], css_coverage):
                css_slice = [
                    data['text'][x['start']:x['end']] for x in data['ranges']
                ]

                unused_css_percentage = await self.calc_unused_css_percentage(
                    css_minify(data['text']), data['ranges']
                )

                result[url].update(
                    dict(
                        css=css_minify(''.join(css_slice)),
                        unused_css_percentage=unused_css_percentage
                    )
                )
        except (PageError, BrowserError, NetworkError, TimeoutError):
            result = {
                url: {'is_valid': False, 'reason': 'Something went wrong'}
            }

        return result

    @staticmethod
    async def calc_unused_css_percentage(text: str, ranges: list) -> int:
        """
        Method calculate unused css percentage
        """
        used_len = sum([x['end'] - x['start'] for x in ranges])
        return 100 - round(used_len / len(text) * 100)


class CacheInvalidateView(web.View):
    """
    Endpoint for invalidate all cache or by given url
    """

    async def get(self) -> web.Response:
        settings = Settings()
        redis_conn = await aioredis.create_connection(
            settings.REDIS_URL, encoding='utf-8'
        )

        if self.request.rel_url.query.get('url') is not None:
            keys = [self.request.rel_url.query.get('url')]
        else:
            keys = await redis_conn.execute('keys', 'url::*')

        for key in keys:
            await redis_conn.execute('del', key)
        return web.json_response({'success': True})


class TestView(web.View):
    """
    Endpoint for test data for calc unused css styles
    """

    @staticmethod
    async def get() -> web.Response:
        base_page = """
        <!DOCTYPE html>
        <html lang="en">
            <head>
                <style>
                    .content {display: block;}
                    h1 {font-size: 16px;}
                    .some-class {position: absolute;}
                </style>
            </head>
            <body>
                <div class="content">
                    <h1>Title</h1>
                    <p>description</p>
                </div>
            </body>
        </html>
        """
        return web.Response(text=base_page, content_type='text/html')
