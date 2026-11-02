import json
import requests

def generate_m3u_and_json():
    target_url = "https://tinyurl.com/xoilacz3" 
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        print("Đang kết nối lấy dữ liệu...")
        response = requests.get(target_url, headers=headers, timeout=30, allow_redirects=True)
        
        if response.status_code == 200:
            data = response.json()
            
            with open('xoilac.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("Đã lưu file xoilac.json thành công!")
            
            valid_items = []
            seen_links = set()

            # Hàm tìm giá trị linh hoạt bằng cách quét các từ khóa trong key
            def get_val(d, keywords):
                if not isinstance(d, dict):
                    return ""
                for k, v in d.items():
                    if any(kw in k.lower() for kw in keywords):
                        if isinstance(v, (str, int, float)) and str(v).strip():
                            val_str = str(v).strip()
                            if val_str.lower() not in ["null", "undefined", "none"]:
                                return val_str
                return ""

            def find_all_matches(node, current_group="Trực Tiếp"):
                if isinstance(node, list):
                    for item in node:
                        find_all_matches(item, current_group)
                elif isinstance(node, dict):
                    group = get_val(node, ["provider", "group", "category_name", "channel_name", "name"]) or current_group
                    
                    # Dò tìm tên đội bóng qua nhiều biến thể key khác nhau
                    home = get_val(node, ["home_name", "home_team", "team1", "home", "host", "t1", "h_name"])
                    away = get_val(node, ["away_name", "away_team", "team2", "away", "guest", "visitor", "t2", "a_name"])
                    match_name = get_val(node, ["match_name", "match_title", "title", "subject", "fullname"])
                    
                    if home and away:
                        match_title = f"{home} vs {away}"
                    elif match_name:
                        match_title = match_name
                    else:
                        match_title = ""

                    league = get_val(node, ["league", "tournament", "competition", "category", "giai", "cup"])
                    time_str = get_val(node, ["time", "date", "start", "schedule", "hour", "gio"])
                    blv = get_val(node, ["blv", "commentator", "caster", "binhluan", "speaker"])
                    logo = get_val(node, ["logo", "icon", "thumb", "image", "avatar", "img"])
                    ua = get_val(node, ["user_agent", "ua"]) or "Mozilla/5.0"
                    referer = get_val(node, ["referer", "ref"]) or ""

                    # Quét tìm các luồng stream trong node hiện tại
                    streams = []
                    for k, v in node.items():
                        if any(kw in k.lower() for kw in ["url", "link", "m3u8", "stream", "source", "play"]):
                            if isinstance(v, str) and v.startswith("http"):
                                streams.append((v, "Server chính"))
                            elif isinstance(v, list):
                                for item in v:
                                    if isinstance(item, str) and item.startswith("http"):
                                        streams.append((item, "Server"))
                                    elif isinstance(item, dict):
                                        u = get_val(item, ["url", "link", "stream", "m3u8", "src"])
                                        nm = get_val(item, ["name", "title", "server"]) or "Server"
                                        if u and u.startswith("http"):
                                            streams.append((u, nm))

                    # Nếu bắt được trận đấu và có luồng stream
                    if streams and match_title:
                        parts = []
                        if time_str:
                            parts.append(f"[{time_str}]")
                        parts.append(match_title)
                        if league:
                            parts.append(f"({league})")
                        if blv:
                            parts.append(f"- BLV: {blv}")
                        
                        full_title = " ".join(parts)

                        for idx, (s_url, s_name) in enumerate(streams):
                            s_lower = s_url.lower()
                            if any(ext in s_lower for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif']):
                                continue
                            if s_url not in seen_links:
                                seen_links.add(s_url)
                                item_title = full_title
                                if len(streams) > 1 and s_name != "Server chính":
                                    item_title += f" [{s_name}]"

                                valid_items.append({
                                    "group": group,
                                    "title": item_title,
                                    "url": s_url,
                                    "logo": logo,
                                    "ua": ua,
                                    "referer": referer
                                })

                    # Tiếp tục đệ quy xuống các cấp con
                    for k, v in node.items():
                        if isinstance(v, (list, dict)):
                            find_all_matches(v, group)

            find_all_matches(data)

            # Cơ chế vét cạn dự phòng (Fallback) nếu cấu trúc phân cấp quá dị biệt
            if len(valid_items) == 0:
                print("Chạy quét vét cạn dự phòng...")
                def fallback_search(node):
                    if isinstance(node, list):
                        for item in node:
                            fallback_search(item)
                    elif isinstance(node, dict):
                        t = get_val(node, ["title", "name", "match", "team", "home", "away"])
                        u = get_val(node, ["url", "link", "m3u8", "stream"])
                        if u and u.startswith("http") and not any(ext in u.lower() for ext in ['.png', '.jpg', '.webp']):
                            if u not in seen_links:
                                seen_links.add(u)
                                valid_items.append({
                                    "group": "Trực Tiếp",
                                    "title": t if t else "Trận đấu trực tiếp",
                                    "url": u,
                                    "logo": "",
                                    "ua": "Mozilla/5.0",
                                    "referer": ""
                                })
                        for k, v in node.items():
                            if isinstance(v, (list, dict)):
                                fallback_search(v)
                fallback_search(data)

            # Ghi file M3U chuẩn
            m3u_content = "#EXTM3U x-tvg-url=\"\"\n"
            for item in valid_items:
                m3u_content += f"#EXTINF:-1 tvg-logo=\"{item['logo']}\" group-title=\"{item['group']}\",{item['title']}\n"
                final_link = item["url"]
                if item["referer"]:
                    final_link = f"{item['url']}|User-Agent={item['ua']}&Referer={item['referer']}"
                elif item["ua"] != "Mozilla/5.0":
                    final_link = f"{item['url']}|User-Agent={item['ua']}"
                m3u_content += f"{final_link}\n"

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
            print(f"Đã tạo xong playlist.m3u với {len(valid_items)} luồng đầy đủ!")
            
        else:
            print(f"Lỗi HTTP: {response.status_code}")
    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == "__main__":
    generate_m3u_and_json()
    
