import os
from aiohttp import web, ClientError
from urllib.parse import urlparse
from re import search
import aiohttp
import asyncio

class DirectDownloadLinkException(Exception):
    pass

async def terabox(url, video_quality="HD Video"):
    """Terabox direct link generator"""
    supported_domains = [
        "terabox.com", "nephobox.com", "4funbox.com", "mirrobox.com",
        "momerybox.com", "teraboxapp.com", "1024tera.com", "terabox.app",
        "gibibox.com", "goaibox.com", "terasharelink.com", "teraboxlink.com",
        "freeterabox.com", "1024terabox.com", "teraboxshare.com"
    ]
    
    pattern = r"/s/(\w+)|surl=(\w+)"
    parsed_url = urlparse(url)
    if not search(pattern, url) or parsed_url.netloc not in supported_domains:
        raise DirectDownloadLinkException("Invalid terabox URL")

    terabox_url = url.replace(parsed_url.netloc, "1024tera.com")

    urls = [
        "https://ytshorts.savetube.me/api/v1/terabox-downloader",
        "https://teraboxvideodownloader.nepcoderdevs.workers.dev/?url={}",
        "https://terabox.udayscriptsx.workers.dev/?url={}",
        "https://mavimods.serv00.net/Mavialt.php?url={}",
        "https://mavimods.serv00.net/Mavitera.php?url={}"
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Content-Type": "application/json",
        "Origin": "https://ytshorts.savetube.me",
    }

    response_data = None
    
    async with aiohttp.ClientSession() as session:
        for base_url in urls:
            api_url = base_url.format(terabox_url) if "{}" in base_url else base_url
            try:
                if "api/v1" in api_url:
                    async with session.post(api_url, headers=headers, json={"url": terabox_url}, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status == 200:
                            response_data = await resp.json()
                            break
                else:
                    async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status == 200:
                            response_data = await resp.json()
                            break
            except (ClientError, asyncio.TimeoutError):
                continue
    
    if not response_data:
        raise DirectDownloadLinkException("No working API endpoints found")

    details = {"contents": [], "title": "", "total_size": 0}

    if "response" in response_data:  # Old format
        for item in response_data["response"]:
            title = item.get("title", "Untitled")
            resolutions = item.get("resolutions", {})
            if zlink := resolutions.get(video_quality):
                details["contents"].append({"url": zlink, "filename": title})
            details["title"] = title
    else:  # New format
        title = response_data.get("file_name", "Untitled")
        direct_link = response_data.get("direct_link") or response_data.get("link")
        if direct_link:
            details["contents"].append({"url": direct_link, "filename": title})
            details["title"] = title
            details["total_size"] = response_data.get("sizebytes", 0)

    if not details["contents"]:
        raise DirectDownloadLinkException("No valid download links found")

    return details

async def get_terabox_link(request):
    url = request.query.get('url')
    if not url:
        return web.json_response({"error": "URL parameter is required"}, status=400)

    try:
        result = await terabox(url)
        return web.json_response({
            "status": "success",
            "title": result["title"],
            "contents": result["contents"],
            "total_size": result["total_size"]
        })
    except DirectDownloadLinkException as e:
        return web.json_response({"status": "error", "message": str(e)}, status=400)
    except Exception as e:
        return web.json_response({"status": "error", "message": f"Unexpected error: {str(e)}"}, status=500)

async def home(request):
    return web.json_response({
        "message": "Welcome to TheBongPirate Terabox Downloader API",
        "usage": "GET /TheBongPirate?url=<terabox_url>"
    })

app = web.Application()
app.router.add_get('/', home)
app.router.add_get('/TheBongPirate', get_terabox_link)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    web.run_app(app, host='0.0.0.0', port=port)
