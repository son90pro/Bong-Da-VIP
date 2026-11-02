import json
import re
import requests

def parse_slug_to_title(href_str):
    if not href_str:
        return ""
    parts = [p for p in href_str.strip('/').split('/') if p]
    slug = parts[-1] if parts else ""
    if not slug or "truc-tiep" in slug:
        if len(parts) >= 2:
            slug = parts[-1]
        else:
            return ""

    time_str = ""
    match_slug = slug
    time_match = re.search(r'luc-(\d{2})(\d{2})-ngay-(\d{2})-(\d{2})-(\d{4})', slug)
    if time_match:
        h, m, d, mo, y = time_match.groups()
        time_str = f"{d}/{mo}/{y} {h}:{m}"
        match_slug = re.sub(r'-luc-\d+-ngay-[\d-]+', '', slug).strip('-')

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

            providers = []
            if isinstance(data, dict):
                providers = data.get("providers", [])
                if not providers:
                    providers = [data]
            elif isinstance(data, list):
                providers = data

            for prov in providers:
                if not isinstance(prov, dict):
                    continue
                
                prov_name = prov.get("name") or prov.get("title") or prov.get("provider_name") or "Trực Tiếp"
                prov_logo = prov.get("logo") or prov.get("icon") or ""
                
                # Hàm đệ quy thu thập tất cả các đối tượng (dictionary) chứa luồng phát bên trong provider
                all_items = []
                def collect_nodes(node):
                    if isinstance(node, list):
                        for sub in node:
                            collect_nodes(sub)
                    elif isinstance(node, dict):
                        all_items.append(node)
                        for val in node.values():
                            if isinstance(val, (list, dict)):
                                collect_nodes(val)

                collect_nodes(prov)

                for item in all_items:
                    if not isinstance(item, dict):
                        continue
                    
                    # Tìm link stream trực tiếp
                    stream_url = ""
                    for u_key in ["url", "stream_url", "m3u8", "link"]:
                        val = item.get(u_key)
                        if isinstance(val, str) and val.startswith("http"):
                            stream_url = val
                            break
                    
                    if not stream_url:
                        continue

                    # Lọc bỏ ảnh và các link trang chủ trơn
                    s_lower = stream_url.lower()
                    if any(ext in s_lower for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif']):
                        continue

                    # Bóc tách tên trận đấu từ href hoặc title
                    href = item.get("href") or item.get("url_info") or ""
                    match_title = parse_slug_to_title(href)
                    
                    if not match_title:
                        t = item.get("title") or item.get("name") or item.get("match_name") or ""
                        if t and not any(kw in t.lower() for kw in ['url', 'href', 'logo', 'referer', 'http']):
                            match_title = t
                        else:
                            match_title = f"{prov_name} Trực Tiếp"

                    logo = item.get("home_logo") or item.get("logo") or item.get("icon") or prov_logo
                    referer = item.get("Referer") or item.get("referer") or ""
                    ua = item.get("user_agent") or "Mozilla/5.0"
                    
                    # Gắn tên BLV nếu có trong item
                    blv = item.get("blv") or ""
                    if blv and blv not in match_title:
                        match_title += f" [{blv}]"

                    if stream_url not in seen_links:
                        seen_links.add(stream_url)
                        
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
                
            print(f"Đã tạo xong file playlist.m3u với {count} luồng trận đấu đầy đủ thông tin chuẩn xác!")
            
        else:
            print(f"Lỗi HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == "__main__":
    generate_m3u_and_json()
    
