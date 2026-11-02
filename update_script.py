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
            
            # 1. Lưu file JSON gốc
            with open('xoilac.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("Đã lưu file xoilac.json thành công!")
            
            extracted_items = []
            seen_links = set()

            def is_root_homepage(url):
                if not url or not isinstance(url, str):
                    return True
                url_lower = url.lower()
                has_stream = any(kw in url_lower for kw in ['.m3u8', '.ts', 'playlist', 'live', 'play', 'stream', 'token', 'server', 'hls'])
                if url.count('/') <= 3 and not has_stream:
                    return True
                return False

            def parse_obj(obj, current_group="Bóng Đá"):
                if isinstance(obj, list):
                    for item in obj:
                        parse_obj(item, current_group)
                elif isinstance(obj, dict):
                    # Cập nhật tên nhóm nếu object này đại diện cho provider hoặc group
                    group = obj.get("name") or obj.get("title") or current_group
                    if "providers" in obj or "matches" in obj or "list" in obj or "items" in obj:
                        if obj.get("name"):
                            group = obj.get("name")

                    # Lấy thông tin tên trận đấu
                    home = obj.get("home_team") or obj.get("home") or obj.get("team_home") or ""
                    away = obj.get("away_team") or obj.get("away") or obj.get("team_away") or ""
                    
                    match_title = ""
                    if home and away:
                        match_title = f"{home} vs {away}"
                    else:
                        match_title = obj.get("match_name") or obj.get("title") or obj.get("name") or ""

                    logo = obj.get("logo") or obj.get("icon") or ""
                    ua = obj.get("user_agent", "Mozilla/5.0")
                    referer = obj.get("referer", "")

                    # Thu thập tất cả các link stream trong object này
                    streams_to_check = []
                    
                    for k in ["stream_url", "url", "link", "m3u8", "source", "play_url"]:
                        if k in obj and isinstance(obj[k], str):
                            streams_to_check.append((obj[k], "Server chính"))
                    
                    for k in ["streams", "links", "servers", "sources", "playlist"]:
                        if k in obj and isinstance(obj[k], list):
                            for s in obj[k]:
                                if isinstance(s, str):
                                    streams_to_check.append((s, "Server"))
                                elif isinstance(s, dict):
                                    s_url = s.get("url") or s.get("link") or s.get("stream_url") or ""
                                    s_name = s.get("name") or s.get("server_name") or "Server"
                                    if s_url:
                                        streams_to_check.append((s_url, s_name))

                    for s_url, s_name in streams_to_check:
                        if s_url and isinstance(s_url, str) and s_url.startswith("http"):
                            if not is_root_homepage(s_url) and s_url not in seen_links:
                                seen_links.add(s_url)
                                display_title = match_title if match_title and match_title != group else "Trận đấu trực tiếp"
                                if len(streams_to_check) > 1 and s_name != "Server chính":
                                    display_title += f" [{s_name}]"
                                
                                final_group = current_group if current_group != "Bóng Đá" else group
                                extracted_items.append({
                                    "group": final_group,
                                    "title": display_title,
                                    "url": s_url,
                                    "logo": logo,
                                    "ua": ua,
                                    "referer": referer
                                })

                    # Quét sâu tiếp vào các nhánh con
                    for k, v in obj.items():
                        if isinstance(v, (list, dict)):
                            next_grp = group if k in ["providers", "groups", "matches", "list", "items", "data", "servers", "streams"] else current_group
                            parse_obj(v, next_grp)

            parse_obj(data)

            # Xây dựng nội dung file M3U
            m3u_content = "#EXTM3U x-tvg-url=\"\"\n"
            count = 0

            for item in extracted_items:
                m3u_content += f"#EXTINF:-1 tvg-logo=\"{item['logo']}\" group-title=\"{item['group']}\",{item['title']}\n"
                final_link = item["url"]
                if item["referer"]:
                    final_link = f"{item['url']}|User-Agent={item['ua']}&Referer={item['referer']}"
                elif item["ua"] != "Mozilla/5.0":
                    final_link = f"{item['url']}|User-Agent={item['ua']}"
                
                m3u_content += f"{final_link}\n"
                count += 1

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
                
            print(f"Đã tạo xong file playlist.m3u với {count} trận đấu chính xác!")
            
        else:
            print(f"Lỗi server: {response.status_code}")
            
    except Exception as e:
        print(f"Lỗi thực thi: {e}")

if __name__ == "__main__":
    generate_m3u_and_json()
    
