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

            # 2. Xử lý phần providers (Nhóm theo tên kênh: Xôi Lạc TV, Sao Kê TV,...)
            providers = data.get("providers", [])
            if isinstance(providers, list):
                for prov in providers:
                    if not isinstance(prov, dict):
                        continue
                    prov_name = prov.get("name") or prov.get("title") or "Kênh Trực Tiếp"
                    prov_logo = prov.get("logo") or prov.get("icon") or ""
                    
                    # Lấy danh sách trận đấu bên trong provider
                    matches = (prov.get("matches") or prov.get("list") or 
                               prov.get("items") or prov.get("data") or [])
                    
                    if not matches and isinstance(prov, dict):
                        matches = [prov]

                    for match in matches:
                        if not isinstance(match, dict):
                            continue
                        
                        # Lấy tên đội nhà và đội khách
                        home = match.get("home_team") or match.get("home") or match.get("team_home") or ""
                        away = match.get("away_team") or match.get("away") or match.get("team_away") or ""
                        
                        match_title = ""
                        if home and away:
                            match_title = f"{home} vs {away}"
                        else:
                            match_title = match.get("title") or match.get("name") or match.get("match_name") or ""
                        
                        if not match_title:
                            match_title = "Trận đấu trực tiếp"
                            
                        league = match.get("league") or match.get("tournament") or match.get("category") or ""
                        time_str = match.get("time") or match.get("date") or match.get("start_time") or ""
                        
                        # Định dạng tiêu đề hiển thị giống mẫu: Tên trận + Giải đấu + Thời gian
                        display_title = match_title
                        extra_info = []
                        if league:
                            extra_info.append(league)
                        if time_str:
                            extra_info.append(time_str)
                        
                        if extra_info:
                            display_title += f" ({' • '.join(extra_info)})"

                        logo = match.get("logo") or match.get("icon") or prov_logo

                        # Lấy danh sách các server / luồng phát
                        streams = (match.get("streams") or match.get("links") or 
                                   match.get("servers") or match.get("sources") or [])
                        
                        direct_url = match.get("stream_url") or match.get("url") or match.get("link") or match.get("m3u8") or ""
                        if direct_url and isinstance(direct_url, str) and direct_url.startswith("http"):
                            streams.append({"name": "Server chính", "url": direct_url})

                        if streams:
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

                                if s_url and s_url.startswith("http") and s_url not in seen_links:
                                    seen_links.add(s_url)
                                    
                                    # Nếu có nhiều server, thêm tên server vào sau để phân biệt
                                    item_title = f"{display_title} [{s_name}]" if len(streams) > 1 else display_title
                                    
                                    # group-title chính là tên Provider (Sao Kê TV, Xôi Lạc TV...) giúp app chia danh mục hoàn hảo
                                    m3u_content += f"#EXTINF:-1 tvg-logo=\"{logo}\" group-title=\"{prov_name}\",{item_title}\n"
                                    
                                    final_link = s_url
                                    if referer:
                                        final_link = f"{s_url}|User-Agent={ua}&Referer={referer}"
                                    elif ua != "Mozilla/5.0":
                                        final_link = f"{s_url}|User-Agent={ua}"
                                        
                                    m3u_content += f"{final_link}\n"
                                    count += 1

            # 3. Xử lý thêm phần groups (nếu có cấu trúc bổ sung)
            groups = data.get("groups", [])
            if isinstance(groups, list):
                for g in groups:
                    if not isinstance(g, dict):
                        continue
                    g_name = g.get("name") or g.get("title") or "Bóng Đá"
                    g_matches = g.get("matches", []) or g.get("items", []) or g.get("list", [])
                    for match in g_matches:
                        if not isinstance(match, dict):
                            continue
                        home = match.get("home_team") or match.get("home") or ""
                        away = match.get("away_team") or match.get("away") or ""
                        match_title = f"{home} vs {away}" if (home and away) else (match.get("title") or match.get("name") or "Trận đấu trực tiếp")
                        league = match.get("league") or match.get("tournament") or ""
                        logo = match.get("logo") or ""
                        
                        direct_url = match.get("stream_url") or match.get("url") or match.get("link") or match.get("m3u8") or ""
                        if direct_url and direct_url.startswith("http") and direct_url not in seen_links:
                            seen_links.add(direct_url)
                            display_title = f"{match_title} [{league}]" if league else match_title
                            m3u_content += f"#EXTINF:-1 tvg-logo=\"{logo}\" group-title=\"{g_name}\",{display_title}\n"
                            m3u_content += f"{direct_url}\n"
                            count += 1

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
                
            print(f"Đã tạo xong file playlist.m3u với {count} trận đấu chuẩn giao diện mẫu!")
            
        else:
            print(f"Lỗi server: {response.status_code}")
            
    except Exception as e:
        print(f"Lỗi thực thi: {e}")

if __name__ == "__main__":
    generate_m3u_and_json()
    
