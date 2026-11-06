#!/usr/bin/env python3
"""Создаёт набор анимированных кастомных эмодзи Sonata VPN через Bot API и сохраняет custom_emoji_id.

Запуск:   python3 upload_pack.py BOT_TOKEN OWNER_USER_ID [--size 100|512]
  BOT_TOKEN      токен бота, от имени которого создаётся набор (набор будет называться sonata_anim_by_<логин_бота>)
  OWNER_USER_ID  ваш Telegram ID (владелец набора; вы должны хотя бы раз написать этому боту /start)
  --size         100 (по умолчанию, формат для кастомных эмодзи) или 512 (файлы под требование @Stickers)

Результат: ссылка на набор + файл emoji_ids.json  { "имя": "custom_emoji_id", ... } — он нужен, чтобы подставить
эмодзи в кнопки и тексты бота.
"""
import json, os, sys, urllib.request, urllib.parse, uuid

def api(token, method, fields=None, files=None):
    boundary = uuid.uuid4().hex
    body = b""
    for k, v in (fields or {}).items():
        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    for k, (fname, data) in (files or {}).items():
        body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{fname}\"\r\n"
                 f"Content-Type: video/webm\r\n\r\n").encode() + data + b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/{method}", data=body,
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=300))
    except urllib.error.HTTPError as e:
        return json.load(e)

def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    token, user_id = sys.argv[1], int(sys.argv[2])
    size = "512" if "--size" in sys.argv and sys.argv[sys.argv.index("--size") + 1] == "512" else "100"
    here = os.path.dirname(os.path.abspath(__file__))
    manifest = json.load(open(os.path.join(here, "manifest.json"), encoding="utf-8"))
    me = api(token, "getMe")["result"]["username"]
    set_name = f"sonata_anim_by_{me}"
    names = list(manifest)
    stickers, files = [], {}
    for i, n in enumerate(names):
        stickers.append({"sticker": f"attach://f{i}", "format": "video", "emoji_list": [manifest[n]["emoji"]]})
        files[f"f{i}"] = (f"{n}.webm", open(os.path.join(here, f"webm_{size}", f"{n}.webm"), "rb").read())
    first, rest = 50, names  # createNewStickerSet принимает до 50 стикеров за раз; у нас их меньше
    r = api(token, "createNewStickerSet",
            {"user_id": user_id, "name": set_name, "title": "Sonata VPN Animated", "sticker_type": "custom_emoji",
             "stickers": json.dumps(stickers, ensure_ascii=False)}, files)
    if not r.get("ok"):
        sys.exit(f"Ошибка Telegram: {r}")
    info = api(token, "getStickerSet", {"name": set_name})["result"]
    ids = {}
    for n, st in zip(names, info["stickers"]):
        ids[n] = st["custom_emoji_id"]
    json.dump(ids, open(os.path.join(here, "emoji_ids.json"), "w"), ensure_ascii=False, indent=2)
    print(f"Готово! Набор: https://t.me/addemoji/{set_name}\nID сохранены в emoji_ids.json ({len(ids)} шт.)")

main()
