import hashlib
import json
import pathlib
import urllib.request

SRC = "https://raw.githubusercontent.com/liu666666667/awesome-zhuiju-free/main/resources/resources.json"
MY_FILE = pathlib.Path("config/sources.json")
WANTED = {"tvbox_config"}

def norm(u: str) -> str:
    return (u or "").strip().rstrip("/")

def fetch_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)

def make_id(name: str) -> str:
    h = hashlib.md5(name.encode("utf-8")).hexdigest()[:8]
    return f"zhuiju_{h}"

up = fetch_json(SRC)
items = up.get("resources", up) if isinstance(up, dict) else up

data = json.loads(MY_FILE.read_text(encoding="utf-8"))
sources = data.setdefault("sources", [])

# 已有 URL 集合 + name 到 source 的映射
seen_urls = set()
name_to_source = {}
existing_ids = set()
for src in sources:
    if src.get("id"):
        existing_ids.add(src["id"])
    name = src.get("name")
    if name:
        name_to_source[name] = src
    for u in src.get("urls", []):
        seen_urls.add(norm(u))

added_new = 0
added_url = 0
for it in items:
    if it.get("category") not in WANTED:
        continue

    verify = (it.get("verification") or {}).get("status")
    if verify in ("removed", "temporarily_unavailable"):
        continue

    url = (it.get("link_url") or it.get("url") or "").strip()
    if not url:
        continue
    key = norm(url)
    if key in seen_urls:
        continue

    name = it.get("name") or it.get("title") or "未命名"

    if name in name_to_source:
        # 同名已存在 → 追加 URL 到已有条目
        src = name_to_source[name]
        src.setdefault("urls", []).append(url)
        added_url += 1
    else:
        # 新资源 → 新建条目
        new_id = make_id(name)
        base_id = new_id
        i = 1
        while new_id in existing_ids:
            new_id = f"{base_id}_{i}"
            i += 1
        new_src = {"id": new_id, "name": name, "urls": [url]}
        sources.append(new_src)
        name_to_source[name] = new_src
        existing_ids.add(new_id)
        added_new += 1

    seen_urls.add(key)

MY_FILE.write_text(
    json.dumps(data, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print(f"新增 source 条目: {added_new} 个，追加 URL 到已有条目: {added_url} 条")
print(f"当前 sources 总数: {len(sources)}")
