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

            providers = data.get("providers", [])
            if not isinstance(providers, list):
                providers = []

            for prov in providers:
                if not isinstance(prov, dict):
                    continue
                
                # Cố định group-title CHÍNH LÀ TÊN NHÀ CUNG CẤP (Sao Kê TV, Xôi Lạc TV,...)
                prov_name = prov.get("name") or prov.get("title") or "Kênh Trực Tiếp"
                
                # Lấy danh sách trận đấu bên trong provider
                matches = []
                for k in ["matches", "list", "items", "data", "match_list", "schedule"]:
                    if k in prov and isinstance(prov[k], list):
                        matches = prov[k]
                        break
                
                if not matches:
                    for val in prov.values():
                        if isinstance(val, list):
                            matches = val
                            break

                for match in matches:
                    if not isinstance(match, dict):
                        continue
                    
                    # Lấy chính xác tên cặp đấu (Home vs Away)
                    home = match.get("home_team") or match.get("home") or match.get("team_home") or ""
                    away = match.get("away_team") or match.get("away") or match.get("team_away") or ""
                    
                    match_title = ""
                    if home and away:
                        match_title = f"{home} vs {away}"
                    else:
                        match_title = match.get("title") or match.get("name") or match.get("match_name") or match.get("match") or ""
                    
                    if not match_title:
                        match_title = "Trận đấu trực tiếp"

                    league = match.get("league") or match.get("tournament") or match.get("category") or ""
                    logo = match.get("logo") or match.get("icon") or ""

                    display_title = match_title
                    if league and league not in display_title:
                        display_title += f" ({league})"

                    # Lấy danh sách server/stream phát sóng
                    streams = []
                    for sk in ["streams", "links", "servers", "sources", "playlist"]:
                        if sk in match and isinstance(match[sk], list):
                            streams = match[sk]
                            break
                    
                    direct_url = match.get("stream_url") or match.get("url") or match.get("link") or match.get("m3u8") or ""
                    if direct_url and isinstance(direct_url, str) and direct_url.startswith("http"):
                        streams.append({"name": "Server chính", "url": direct_url})

                    if not streams and direct_url and direct_url.startswith("http"):
                        streams = [{"name": "Server chính", "url": direct_url}]

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
                            # BỘ LỌC CHẶT CHẼ: Loại bỏ tuyệt đối link ảnh và link trang chủ gốc
                            s_url_lower = s_url.lower()
                            is_image = any(s_url_lower.endswith(ext) or ext in s_url_lower for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif'])
                            is_homepage = (s_url.count('/') <= 3 and not any(kw in s_url_lower for kw in ['.m3u8', '.ts', 'playlist', 'live', 'play', 'stream', 'token', 'server']))

                            if is_image or is_homepage:
                                continue

                            if s_url not in seen_links:
                                seen_links.add(s_url)
                                item_title = f"{display_title} [{s_name}]" if len(streams) > 1 else display_title
                                
                                # Ghi chuẩn định dạng: group-title là tên kênh, tiêu đề là tên trận đấu
                                m3u_content += f"#EXTINF:-1 tvg-logo=\"{logo}\" group-title=\"{prov_name}\",{item_title}\n"
                                
                                final_link = s_url
                                if referer:
                                    final_link = f"{s_url}|User-Agent={ua}&Referer={referer}"
                                elif ua != "Mozilla/5.0":
                                    final_link = f"{s_url}|User-Agent={ua}"
                                    
                                m3u_content += f"{final_link}\n"
                                count += 1

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
                
            print(f"Đã tạo xong file playlist.m3u với {count} luồng trận đấu chuẩn xác!")
            
        else:
            print(f"Lỗi phản hồi từ server: {response.status_code}")
            
    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")

if __name__ == "__main__":
    generate_m3u_and_json()
    
