import asyncio
import json
import os
import uuid
from typing import Optional

import yt_dlp
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()
tasks: dict = {}


class InfoRequest(BaseModel):
    url: str
    browser: Optional[str] = None  # e.g. "chrome", "firefox"


class DownloadRequest(BaseModel):
    url: str
    height: int
    output_dir: str
    browser: Optional[str] = None
    entries: Optional[list[int]] = None


@app.post("/api/info")
async def get_info(req: InfoRequest):
    def _extract():
        base = {"quiet": True}
        if req.browser:
            base["cookiesfrombrowser"] = (req.browser,)

        with yt_dlp.YoutubeDL({**base, "extract_flat": True}) as ydl:
            flat = ydl.extract_info(req.url, download=False)

        entries = []
        first_url = req.url
        if flat.get("_type") == "playlist":
            for i, e in enumerate(flat.get("entries") or []):
                entries.append({"index": i, "title": e.get("title", f"第{i+1}集")})
            if flat.get("entries"):
                first_url = flat["entries"][0].get("url") or flat["entries"][0].get("webpage_url") or req.url

        with yt_dlp.YoutubeDL(base) as ydl:
            info = ydl.extract_info(first_url, download=False)

        heights = sorted(
            {f["height"] for f in info.get("formats", []) if f.get("height") and f.get("vcodec", "none") != "none"},
            reverse=True,
        )
        return {
            "title": flat.get("title") or info.get("title", ""),
            "thumbnail": info.get("thumbnail", ""),
            "formats": [{"height": h, "label": f"{h}p"} for h in heights],
            "entries": entries,
        }

    try:
        result = await asyncio.get_event_loop().run_in_executor(None, _extract)
        return result
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/download")
async def start_download(req: DownloadRequest):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "pending", "progress": 0, "message": ""}
    asyncio.create_task(_do_download(task_id, req))
    return {"task_id": task_id}


async def _do_download(task_id: str, req: DownloadRequest):
    def progress_hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            done = d.get("downloaded_bytes", 0)
            pct = int(done / total * 100) if total else 0
            tasks[task_id] = {"status": "downloading", "progress": pct, "message": d.get("_speed_str", "")}
        elif d["status"] == "finished":
            tasks[task_id] = {"status": "merging", "progress": 99, "message": "合并中..."}

    os.makedirs(req.output_dir, exist_ok=True)
    opts = {
        "format": f"bestvideo[height<={req.height}]+bestaudio/best[height<={req.height}]",
        "outtmpl": os.path.join(req.output_dir, "%(title)s.%(ext)s"),
        "merge_output_format": "mp4",
        "progress_hooks": [progress_hook],
        "quiet": True,
    }
    if req.browser:
        opts["cookiesfrombrowser"] = (req.browser,)
    if req.entries is not None:
        opts["playlist_items"] = ",".join(str(i + 1) for i in req.entries)

    def _run():
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([req.url])

    try:
        await asyncio.get_event_loop().run_in_executor(None, _run)
        tasks[task_id] = {"status": "done", "progress": 100, "message": "下载完成", "output_dir": req.output_dir}
    except Exception as e:
        tasks[task_id] = {"status": "error", "progress": 0, "message": str(e)}


@app.get("/api/progress/{task_id}")
async def progress(task_id: str):
    async def stream():
        while True:
            t = tasks.get(task_id, {})
            yield f"data: {json.dumps(t)}\n\n"
            if t.get("status") in ("done", "error"):
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(stream(), media_type="text/event-stream")


app.mount("/", StaticFiles(directory="static", html=True), name="static")
