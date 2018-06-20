# General information
Application generate only used styles from given url and minimize them

Project use next technologies:
* Python 3.6
* AIOHTTP - asynchronous HTTP Client/Server
* Redis - in-memory data structure store
* Docker - container platform

### Setup
At root of the project run:
```
docker-compose up --build
```

_Note: When you run pyppeteer first time, it downloads a recent version of Chromium (~100MB)._

Also available API documentation at `http://127.0.0.1:8000/api/doc#/base`

### Testing
Request to get only used css styles
```bash
curl -X POST --header 'Content-Type: application/json' --header 'Accept: application/json' -d '{"urls": ["https://habr.com/"]}' 'http://127.0.0.1:8000/'
```

Response
```json
[
  {
    "https://habr.com/": {
      "is_valid": true,
      "css": "@charset \"utf-8\";.MathJax_SVG_ExBox{display:block !important;overflow:hidden;width:1px;height:60ex;min-height:0;max-height:none;padding:0;border:0;margin:0}.MathJax_SVG_LineBox{display:table !important}.MathJax_SVG_LineBox span{display:table-cell !important;width:10000em !important;min-width:0;max-width:none;padding:0;border:0;margin:0}",
      "unused_css_percentage": 6086
    }
  }
]
```

Request to invalidate all cache
```bash
curl -X GET --header 'Accept: application/json' 'http://127.0.0.1:8000/cache-invalidate'
```

Response
```json
{
  "success": true
}
```

Request to invalidate cache by given url
```bash
curl -X GET --header 'Accept: application/json' 'http://127.0.0.1:8000/cache-invalidate?url=https%3A%2F%2Fhabr.com%2F'
```

Response
```json
{
  "success": true
}
```
