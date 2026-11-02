import json
import re
import requests

def parse_slug_to_title(href_str):
    if not href_str:
        return "Trận đấu trực tiếp"
    parts = [p for p in href_str.strip('/').split('/') if p]
    slug = parts[-1] if parts else ""
    if not slug or "truc-tiep" in slug:
        if len(parts) >= 2:
            slug = parts[-1]
        else:
            return "Trận đấu trực tiếp"

    # Trích xuất thời gian và ngày tháng từ slug (ví dụ: luc-1930-ngay-02-11-2026)
    time_str = ""
    match_slug = slug
    time_match = re.search(r'luc-(\d{2})(\d{2})-ngay-(\d{2})-(\d{2})-(\d{4})', slug)
    if time_match:
        h, m, d, mo, y = time_match.groups()
        time_str = f"{d}/{mo}/{y} {h}:{m}"
        match_slug = re.sub(r'-luc-\d+-ngay-[\d-]+', '', slug).strip('-')

    # Làm sạch tên đội bóng
    team_name = match_slug.replace('-', ' ').title()
    team_name = re.sub(r'\bVs\b', 'vs', team_name)

    if time_str:
        return f"[{time_str}] {team_name}"
    return team_name

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
            
            m3u_content = "#EXTM3U x-tvg-url=\"\"\n"
            count = 0
            seen_links = set()

            providers = data.get("providers", [])
            if not isinstance(providers, list):
                providers = [providers] if isinstance(providers, dict) else []

            for prov in providers:
                if not isinstance(prov, dict):
                    continue
                
                # Tên nhà cung cấp chuẩn làm danh mục sidebar bên trái TV
                prov_name = prov.get("name") or prov.get("title") or prov.get("provider_name") or "Kênh Trực Tiếp"
                prov_logo = prov.get("logo") or prov.get("icon") or ""
                
                # Lấy danh sách trận đấu bên trong provider
                matches = []
                for k in ["matches", "list", "items", "data", "match_list", "schedule", "channels", "matchs"]:
                    if k in prov and isinstance(prov[k], list):
                        matches = prov[k]
                        break
                
                if not matches:
                    for val in prov.values():
                        if isinstance(val, list):
                            matches = val
                            break

                if not matches:
                    matches = [prov]

                for match in matches:
                    if not isinstance(match, dict):
                        continue
                    
                    # 1. Lấy thông tin tiêu đề, thời gian, tên đội từ slug href
                    href = match.get("href") or match.get("url_info") or ""
                    match_title = parse_slug_to_title(href)

                    # 2. Lấy logo đội bóng
                    logo = match.get("home_logo") or match.get("logo") or match.get("icon") or prov_logo
                    
                    # 3. Lấy link stream (.m3u8) và Referer
                    stream_url = match.get("url") or match.get("stream_url") or match.get("m3u8") or ""
                    referer = match.get("Referer") or match.get("referer") or ""
                    ua = match.get("user_agent") or "Mozilla/5.0"

                    if stream_url and isinstance(stream_url, str) and stream_url.startswith("http"):
                        s_lower = stream_url.lower()
                        # Loại bỏ tuyệt đối các file ảnh
                        is_image = any(ext in s_lower for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif'])
                        
                        if not is_image:
                            if stream_url not in seen_links:
                                seen_links.add(stream_url)
                                
                                # Ghi EXTINF chuẩn với logo và tên nhóm danh mục
                                m3u_content += f"#EXTINF:-1 tvg-logo=\"{logo}\" group-title=\"{prov_name}\",{match_title}\n"
                                
                                final_link = stream_url
                                if referer:
                                    final_link = f"{stream_url}|User-Agent={ua}&Referer={referer}"
                                elif ua != "Mozilla/5.0":
                                    final_link = f"{stream_url}|User-Agent={ua}"
                                    
                                m3u_content += f"{final_link}\n"
                                count += 1

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
                
            print(f"Đã tạo xong file playlist.m3u với {count} luồng trận đấu chuẩn xác tuyệt đối!")
            
        else:
            print(f"Lỗi HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")

if __name__ == "__main__":
    generate_m3u_and_json()
    
