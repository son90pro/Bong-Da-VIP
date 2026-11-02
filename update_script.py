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

            def is_root_homepage(url):
                """Hàm phụ trợ kiểm tra xem link có phải là trang chủ gốc hay không"""
                if not url or not isinstance(url, str):
                    return True
                url_lower = url.lower()
                # Nếu link chỉ có dạng https://domain.com/ (ít dấu slash và không có từ khóa stream)
                has_stream_keyword = any(kw in url_lower for kw in ['.m3u8', '.ts', 'playlist', 'live', 'play', 'stream', 'token', 'server', 'hls'])
                if url.count('/') <= 3 and not has_stream_keyword:
                    return True
                return False

            def process_match(match, group_name):
                nonlocal count
                if not isinstance(match, dict):
                    return
                
                # Lấy tên cặp đấu
                home = match.get("home_team") or match.get("home") or match.get("team_home") or ""
                away = match.get("away_team") or match.get("away") or match.get("team_away") or ""
                
                match_title = ""
                if home and away:
                    match_title = f"{home} vs {away}"
                else:
                    match_title = match.get("title") or match.get("name") or match.get("match_name") or ""
                
                if not match_title:
                    return # Bỏ qua nếu không có tên trận
                    
                league = match.get("league") or match.get("tournament") or match.get("category") or ""
                time_str = match.get("time") or match.get("date") or match.get("start_time") or ""
                logo = match.get("logo") or match.get("icon") or ""

                display_title = match_title
                extra = []
                if league: extra.append(league)
                if time_str: extra.append(time_str)
                if extra:
                    display_title += f" ({' • '.join(extra)})"

                # Thu thập danh sách các server / nguồn phát
                streams = match.get("streams") or match.get("links") or match.get("servers") or match.get("sources") or []
                
                direct_url = match.get("stream_url") or match.get("url") or match.get("link") or match.get("m3u8") or ""
                if direct_url and isinstance(direct_url, str) and direct_url.startswith("http"):
                    if not is_root_homepage(direct_url):
                        streams.append({"name": "Server chính", "url": direct_url})

                for idx, stream in enumerate(streams, 1):
                    s_url = ""
                    s_name = f"Server {idx}"
                    ua = match.get("user_agent", "Mozilla/5.0")
                    referer = match.get("referer", "")

                    if isinstance(stream, str):
                        s_url = stream
                    elif isinstance(stream, dict):
                        s_url = stream.get("url") or stream.get("link") or stream.get("stream_url") or ""
                        s_name = stream.get("name") or stream.get("server_name") or f"Server {idx}"
                        ua = stream.get("user_agent", ua)
                        referer = stream.get("referer", referer)

                    if s_url and isinstance(s_url, str) and s_url.startswith("http"):
                        # Bỏ qua nếu là link trang chủ gốc
                        if is_root_homepage(s_url):
                            continue

                        if s_url not in seen_links:
                            seen_links.add(s_url)
                            item_title = f"{display_title} [{s_name}]" if len(streams) > 1 else display_title
                            
                            m3u_content += f"#EXTINF:-1 tvg-logo=\"{logo}\" group-title=\"{group_name}\",{item_title}\n"
                            
                            final_link = s_url
                            if referer:
                                final_link = f"{s_url}|User-Agent={ua}&Referer={referer}"
                            elif ua != "Mozilla/5.0":
                                final_link = f"{s_url}|User-Agent={ua}"
                                
                            m3u_content += f"{final_link}\n"
                            count += 1

            def recursive_find_matches(obj, current_group):
                if isinstance(obj, list):
                    for item in obj:
                        recursive_find_matches(item, current_group)
                elif isinstance(obj, dict):
                    has_teams = (obj.get("home_team") or obj.get("home")) and (obj.get("away_team") or obj.get("away"))
                    has_title_and_link = (obj.get("title") or obj.get("name")) and (obj.get("url") or obj.get("streams") or obj.get("links") or obj.get("stream_url"))
                    
                    if has_teams or has_title_and_link:
                        process_match(obj, current_group)
                    
                    for k, v in obj.items():
                        if k not in ["streams", "links", "servers", "sources"]:
                            if isinstance(v, (list, dict)):
                                recursive_find_matches(v, current_group)

            # Quét qua danh sách providers
            providers = data.get("providers", [])
            if isinstance(providers, list):
                for prov in providers:
                    if not isinstance(prov, dict): continue
                    prov_name = prov.get("name") or prov.get("title") or "Kênh Trực Tiếp"
                    recursive_find_matches(prov, prov_name)

            # Quét qua groups nếu có
            groups = data.get("groups", [])
            if isinstance(groups, list):
                for g in groups:
                    if not isinstance(g, dict): continue
                    g_name = g.get("name") or g.get("title") or "Bóng Đá"
                    recursive_find_matches(g, g_name)

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
                
            print(f"Đã lọc và tạo xong file playlist.m3u với {count} trận đấu thực tế (đã loại bỏ trang chủ)!")
            
        else:
            print(f"Lỗi server: {response.status_code}")
            
    except Exception as e:
        print(f"Lỗi thực thi: {e}")

if __name__ == "__main__":
    generate_m3u_and_json()
    
