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
            
            m3u_content = "#EXTM3U x-tvg-url=\"\"\n"
            count = 0
            seen_links = set()

            def recursive_parse(obj, current_group="Bóng Đá"):
                nonlocal count
                if isinstance(obj, list):
                    for item in obj:
                        recursive_parse(item, current_group)
                elif isinstance(obj, dict):
                    # Cập nhật tên nhóm/danh mục nếu tìm thấy tên nhà cung cấp hoặc group
                    group = obj.get("name") or obj.get("title") or obj.get("group") or obj.get("category") or current_group
                    if current_group != "Bóng Đá" and obj.get("name"):
                        group = obj.get("name")

                    # Lấy link stream hoặc url
                    url = (obj.get("stream_url") or obj.get("url") or obj.get("link") or 
                           obj.get("m3u8") or obj.get("source") or obj.get("play_url") or "")
                    
                    # Lấy tên trận đấu hoặc tên kênh
                    home = obj.get("home_team") or obj.get("home") or ""
                    away = obj.get("away_team") or obj.get("away") or ""
                    
                    title = ""
                    if home and away:
                        title = f"{home} vs {away}"
                    else:
                        title = obj.get("match_name") or obj.get("title") or obj.get("name") or obj.get("channel") or ""

                    logo = obj.get("logo") or obj.get("icon") or ""
                    ua = obj.get("user_agent", "Mozilla/5.0")
                    referer = obj.get("referer", "")

                    if url and isinstance(url, str) and url.startswith("http"):
                        # Chặn các link trang chủ gốc (ít dấu / và không có đuôi stream)
                        url_lower = url.lower()
                        is_root = (url.count('/') <= 3 and not any(kw in url_lower for kw in ['.m3u8', '.ts', 'playlist', 'live', 'play', 'stream', 'token', 'server', 'hls', 'index']))
                        
                        if not is_root and url not in seen_links:
                            seen_links.add(url)
                            display_title = title if title and title != group else "Trận đấu trực tiếp"
                            
                            # Ghi vào file m3u theo chuẩn nhóm của nhà cung cấp
                            m3u_content += f"#EXTINF:-1 tvg-logo=\"{logo}\" group-title=\"{current_group}\",{display_title}\n"
                            
                            final_link = url
                            if referer:
                                final_link = f"{url}|User-Agent={ua}&Referer={referer}"
                            elif ua != "Mozilla/5.0":
                                final_link = f"{url}|User-Agent={ua}"
                                
                            m3u_content += f"{final_link}\n"
                            count += 1

                    # Tiếp tục quét sâu vào các nhánh con trong JSON
                    for k, v in obj.items():
                        if isinstance(v, (list, dict)):
                            next_group = group if k in ["providers", "groups", "matches", "list", "items", "data", "servers", "streams"] else current_group
                            recursive_parse(v, next_group)

            recursive_parse(data)

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
                
            print(f"Đã tạo xong file playlist.m3u với {count} trận đấu thực tế!")
            
        else:
            print(f"Lỗi server: {response.status_code}")
            
    except Exception as e:
        print(f"Lỗi thực thi: {e}")

if __name__ == "__main__":
    generate_m3u_and_json()
    
