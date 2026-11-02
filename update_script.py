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
            
            valid_items = []
            seen_links = set()

            providers = data.get("providers", [])
            if not isinstance(providers, list):
                providers = []

            for prov in providers:
                if not isinstance(prov, dict):
                    continue
                
                prov_name = prov.get("name") or prov.get("title") or "Kênh Trực Tiếp"
                prov_logo = prov.get("logo") or prov.get("icon") or ""
                
                # Hàm đệ quy thông minh tìm kiếm các đối tượng chứa trận đấu
                def search_matches(obj, current_cat):
                    if isinstance(obj, list):
                        for item in obj:
                            search_matches(item, current_cat)
                    elif isinstance(obj, dict):
                        cat = obj.get("name") or obj.get("title") or current_cat
                        
                        # Kiểm tra xem object này có thông tin đội bóng hoặc trận đấu thực sự không
                        home = obj.get("home_team") or obj.get("home") or obj.get("team_home") or ""
                        away = obj.get("away_team") or obj.get("away") or obj.get("team_away") or ""
                        
                        match_title = ""
                        if home and away:
                            match_title = f"{home} vs {away}"
                        else:
                            t = obj.get("match_name") or obj.get("title") or obj.get("name") or ""
                            # Loại bỏ các tiêu đề rác hoặc tên danh mục giao diện
                            if t and not any(kw in t for kw in ["Đang Phát Trực Tiếp", "Lịch Thi Đấu", "Tất Cả", "href", "url", "logo"]):
                                match_title = t

                        league = obj.get("league") or obj.get("tournament") or obj.get("category") or ""
                        logo = obj.get("logo") or obj.get("icon") or prov_logo
                        ua = obj.get("user_agent", "Mozilla/5.0")
                        referer = obj.get("referer", "")

                        # Thu thập các link stream thực tế
                        streams = []
                        for k in ["stream_url", "url", "link", "m3u8", "source", "play_url", "hls"]:
                            val = obj.get(k)
                            # Đảm bảo đây là link phát thực sự, không phải chuỗi linh tinh hay key tên miền
                            if isinstance(val, str) and val.startswith("http") and not any(x in val for x in ['/logo/', '/teams/']):
                                streams.append((val, "Server chính"))

                        for k in ["streams", "links", "servers", "sources", "playlist"]:
                            arr = obj.get(k)
                            if isinstance(arr, list):
                                for s in arr:
                                    if isinstance(s, str) and s.startswith("http"):
                                        streams.append((s, "Server"))
                                    elif isinstance(s, dict):
                                        s_url = s.get("url") or s.get("link") or s.get("stream_url") or s.get("m3u8") or ""
                                        s_name = s.get("name") or s.get("server_name") or "Server"
                                        if isinstance(s_url, str) and s_url.startswith("http"):
                                            streams.append((s_url, s_name))

                        for s_url, s_name in streams:
                            s_url_lower = s_url.lower()
                            # Bộ lọc loại bỏ hình ảnh và trang chủ trơn
                            is_image = any(ext in s_url_lower for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif', 'badge', 'logo'])
                            is_homepage = (s_url.count('/') <= 3 and not any(kw in s_url_lower for kw in ['.m3u8', '.ts', 'playlist', 'live', 'play', 'stream', 'token', 'server', 'hls']))

                            if is_image or is_homepage:
                                continue

                            if s_url not in seen_links:
                                seen_links.add(s_url)
                                
                                display_title = match_title if match_title else "Trận đấu trực tiếp"
                                if league and league not in display_title:
                                    display_title += f" ({league})"
                                if len(streams) > 1 and s_name != "Server chính":
                                    display_title += f" [{s_name}]"

                                valid_items.append({
                                    "group": prov_name,
                                    "title": display_title,
                                    "url": s_url,
                                    "logo": logo,
                                    "ua": ua,
                                    "referer": referer
                                })

                        # Tiếp tục quét sâu vào các nhánh con
                        for k, v in obj.items():
                            if isinstance(v, (list, dict)):
                                search_matches(v, cat)

                search_matches(prov, prov_name)

            # Ghi nội dung ra file playlist.m3u chuẩn
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
                
            print(f"Đã tạo xong file playlist.m3u với {len(valid_items)} luồng trận đấu chuẩn xác!")
            
        else:
            print(f"Lỗi phản hồi từ server: {response.status_code}")
            
    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")

if __name__ == "__main__":
    generate_m3u_and_json()
    
