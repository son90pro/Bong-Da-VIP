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
            
            # Lưu file JSON gốc để kiểm tra cấu trúc
            with open('xoilac.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("Đã lưu file xoilac.json thành công!")
            
            valid_items = []
            seen_links = set()

            providers = data.get("providers", [])
            if not isinstance(providers, list):
                if isinstance(data, dict):
                    for k, v in data.items():
                        if isinstance(v, list):
                            providers = v
                            break
                if not isinstance(providers, list):
                    providers = [data]

            for prov in providers:
                if not isinstance(prov, dict):
                    continue
                
                prov_name = prov.get("name") or prov.get("title") or prov.get("provider_name") or "Kênh Trực Tiếp"
                prov_logo = prov.get("logo") or prov.get("icon") or ""

                # Hàm quét đệ quy đa tầng tìm thông tin trận đấu và luồng phát
                def find_matches(node, current_cat):
                    if isinstance(node, list):
                        for item in node:
                            find_matches(item, current_cat)
                    elif isinstance(node, dict):
                        cat = node.get("name") or node.get("title") or current_cat
                        
                        # Trích xuất thông tin chi tiết trận đấu
                        home = node.get("home_team") or node.get("home") or node.get("team_home") or node.get("home_name") or ""
                        away = node.get("away_team") or node.get("away") or node.get("team_away") or node.get("away_name") or ""
                        
                        match_title = ""
                        if home and away:
                            match_title = f"{home} vs {away}"
                        else:
                            t = node.get("match_name") or node.get("title") or node.get("name") or ""
                            if t and not any(kw in t.lower() for kw in ["đang phát trực tiếp", "lịch thi đấu", "tất cả", "href", "url", "logo"]):
                                match_title = t

                        league = node.get("league") or node.get("tournament") or node.get("category") or node.get("competition") or ""
                        time_str = node.get("time") or node.get("date") or node.get("start_time") or node.get("match_time") or ""
                        blv = node.get("blv") or node.get("commentator") or node.get("caster") or node.get("bình luận viên") or ""
                        logo = node.get("logo") or node.get("icon") or node.get("match_logo") or prov_logo
                        ua = node.get("user_agent", "Mozilla/5.0")
                        referer = node.get("referer", "")

                        # Thu thập toàn bộ các luồng phát (stream links)
                        streams = []
                        for k in ["stream_url", "url", "link", "m3u8", "source", "play_url", "hls"]:
                            val = node.get(k)
                            if isinstance(val, str) and val.startswith("http") and not any(ext in val.lower() for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif']):
                                streams.append((val, "Server chính"))

                        for k in ["streams", "links", "servers", "sources", "playlist"]:
                            arr = node.get(k)
                            if isinstance(arr, list):
                                for s in arr:
                                    if isinstance(s, str) and s.startswith("http"):
                                        streams.append((s, "Server"))
                                    elif isinstance(s, dict):
                                        s_url = s.get("url") or s.get("link") or s.get("stream_url") or s.get("m3u8") or ""
                                        s_name = s.get("name") or s.get("server_name") or "Server"
                                        if isinstance(s_url, str) and s_url.startswith("http"):
                                            streams.append((s_url, s_name))

                        # Nếu tìm thấy luồng phát, tiến hành đóng gói thông tin đầy đủ
                        if streams:
                            title_parts = []
                            if time_str:
                                title_parts.append(f"[{time_str}]")
                            
                            if match_title:
                                title_parts.append(match_title)
                            else:
                                title_parts.append(prov_name)

                            if league:
                                title_parts.append(f"({league})")
                            
                            if blv:
                                title_parts.append(f"- BLV: {blv}")

                            base_title = " ".join(title_parts)

                            for idx, (s_url, s_name) in enumerate(streams):
                                if s_url not in seen_links:
                                    seen_links.add(s_url)
                                    
                                    item_title = base_title
                                    if len(streams) > 1 and s_name != "Server chính":
                                        item_title += f" [{s_name}]"

                                    valid_items.append({
                                        "group": prov_name,
                                        "title": item_title,
                                        "url": s_url,
                                        "logo": logo,
                                        "ua": ua,
                                        "referer": referer
                                    })

                        # Tiếp tục quét sâu vào các nhánh con
                        for k, v in node.items():
                            if isinstance(v, (list, dict)):
                                find_matches(v, cat)

                find_matches(prov, prov_name)

            # Cơ chế quét mở rộng dự phòng nếu danh sách rỗng
            if not valid_items:
                print("Đang chạy quét mở rộng toàn bộ JSON...")
                def broad_search(node):
                    if isinstance(node, list):
                        for item in node:
                            broad_search(item)
                    elif isinstance(node, dict):
                        home = node.get("home_team") or node.get("home") or ""
                        away = node.get("away_team") or node.get("away") or ""
                        url = node.get("stream_url") or node.get("url") or node.get("m3u8") or ""
                        if home and away and isinstance(url, str) and url.startswith("http"):
                            time_str = node.get("time", "")
                            league = node.get("league", "")
                            blv = node.get("blv", "")
                            logo = node.get("logo", "")
                            title = f"[{time_str}] {home} vs {away}" if time_str else f"{home} vs {away}"
                            if league: title += f" ({league})"
                            if blv: title += f" - BLV: {blv}"
                            
                            if url not in seen_links:
                                seen_links.add(url)
                                valid_items.append({
                                    "group": "Trực Tiếp",
                                    "title": title,
                                    "url": url,
                                    "logo": logo,
                                    "ua": "Mozilla/5.0",
                                    "referer": ""
                                })
                        for k, v in node.items():
                            if isinstance(v, (list, dict)):
                                broad_search(v)
                broad_search(data)

            # Xuất file playlist.m3u hoàn chỉnh
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
                
            print(f"Đã tạo xong file playlist.m3u với {len(valid_items)} luồng đầy đủ thông tin chi tiết!")
            
        else:
            print(f"Lỗi phản hồi từ server: {response.status_code}")
            
    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")

if __name__ == "__main__":
    generate_m3u_and_json()
    
