import json
import requests

def extract_all_links(data):
    results = []
    
    def recursive_search(obj, current_group="Bóng Đá"):
        if isinstance(obj, list):
            for item in obj:
                recursive_search(item, current_group)
        elif isinstance(obj, dict):
            # Lấy nhóm giải đấu
            group = (obj.get("category") or obj.get("group") or obj.get("league") or 
                     obj.get("tournament") or current_group)
            
            # Cố gắng lấy tên đội nhà và đội khách nếu có
            home = obj.get("home_team") or obj.get("home") or obj.get("team_home") or ""
            away = obj.get("away_team") or obj.get("away") or obj.get("team_away") or ""
            
            match_title = ""
            if home and away:
                match_title = f"{home} vs {away}"
            else:
                match_title = (obj.get("title") or obj.get("name") or obj.get("match_name") or 
                               obj.get("channel_name") or obj.get("match") or "")
            
            logo = obj.get("logo") or obj.get("icon") or obj.get("team_logo") or ""
            
            # Quét các trường chứa link stream
            for k, v in obj.items():
                if isinstance(v, str) and v.startswith("http"):
                    if any(kw in k.lower() for kw in ["url", "link", "stream", "m3u8", "source", "play"]):
                        final_title = match_title if match_title else "Trận đấu trực tiếp"
                        results.append({
                            "title": final_title,
                            "group": group,
                            "url": v,
                            "logo": logo,
                            "ua": obj.get("user_agent", "Mozilla/5.0"),
                            "referer": obj.get("referer", "")
                        })
                elif isinstance(v, (list, dict)):
                    recursive_search(v, group)

    recursive_search(data)
    return results

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
            
            all_links = extract_all_links(data)
            print(f"Tổng số link luồng stream tìm thấy: {len(all_links)}")
            
            m3u_content = "#EXTM3U x-tvg-url=\"\"\n"
            count = 0
            seen_urls = set()

            for item in all_links:
                url = item["url"]
                if url not in seen_urls:
                    seen_urls.add(url)
                    
                    m3u_content += f"#EXTINF:-1 tvg-logo=\"{item['logo']}\" group-title=\"{item['group']}\",{item['title']}\n"
                    
                    final_link = url
                    if item["referer"]:
                        final_link = f"{url}|User-Agent={item['ua']}&Referer={item['referer']}"
                    elif item["ua"] != "Mozilla/5.0":
                        final_link = f"{url}|User-Agent={item['ua']}"
                        
                    m3u_content += f"{final_link}\n"
                    count += 1

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
                
            print(f"Đã tạo xong file playlist.m3u với {count} kênh chuẩn!")
            
        else:
            print(f"Lỗi server: {response.status_code}")
            
    except Exception as e:
        print(f"Lỗi thực thi: {e}")

if __name__ == "__main__":
    generate_m3u_and_json()
    
