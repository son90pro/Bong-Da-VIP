import json
import re
import requests

def parse_slug_to_info(href_str):
    if not href_str:
        return "", ""
    parts = [p for p in href_str.strip('/').split('/') if p]
    slug = parts[-1] if parts else ""
    if not slug or "truc-tiep" in slug:
        if len(parts) >= 2:
            slug = parts[-1]
        else:
            return "", ""

    time_str = ""
    match_slug = slug
    time_match = re.search(r'luc-(\d{2})(\d{2})-ngay-(\d{2})-(\d{2})-(\d{4})', slug)
    if time_match:
        h, m, d, mo, y = time_match.groups()
        time_str = f"{d}/{mo} {h}:{m}"
        match_slug = re.sub(r'-luc-\d+-ngay-[\d-]+', '', slug).strip('-')

    team_name = match_slug.replace('-', ' ').title()
    team_name = re.sub(r'\bVs\b', 'vs', team_name)

    return time_str, team_name

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
                if "providers" in data and isinstance(data["providers"], list):
                    providers = data["providers"]
                else:
                    found_lists = [v for v in data.values() if isinstance(v, list)]
                    if found_lists:
                        providers = [{"name": k, "matches": v} for k, v in data.items() if isinstance(v, list)]
                    else:
                        providers = [data]
            elif isinstance(data, list):
                providers = data

            for prov in providers:
                if not isinstance(prov, dict):
                    continue
                
                prov_name = prov.get("name") or prov.get("title") or prov.get("provider_name") or "Trực Tiếp"
                prov_logo = prov.get("logo") or prov.get("icon") or ""
                
                matches = []
                for k in ["matches", "list", "items", "data", "match_list", "schedule", "channels", "matchs", "match", "content"]:
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

                def process_node(node, cur_time="", cur_title="", cur_logo=prov_logo):
                    nonlocal count, m3u_content, seen_links
                    if isinstance(node, list):
                        for item in node:
                            process_node(item, cur_time, cur_title, cur_logo)
                    elif isinstance(node, dict):
                        # 1. Cập nhật ngữ cảnh thời gian và tên trận đấu
                        href = node.get("href") or node.get("url_info") or ""
                        t_str, m_title = parse_slug_to_info(href)
                        if t_str:
                            cur_time = t_str
                        if m_title:
                            cur_title = m_title

                        home = node.get("home_team") or node.get("home") or ""
                        away = node.get("away_team") or node.get("away") or ""
                        if home and away:
                            cur_title = f"{home} vs {away}"
                        else:
                            raw_t = node.get("title") or node.get("name") or node.get("match_name") or ""
                            if raw_t and not any(kw in raw_t.lower() for kw in ['url', 'href', 'logo', 'http', 'referer', 'server', 'blv', 'hd', 'full', 'truc-tiep']):
                                if " vs " in raw_t.lower() or len(raw_t.split()) >= 3:
                                    cur_title = raw_t

                        lg = node.get("home_logo") or node.get("logo") or node.get("icon") or ""
                        if lg and isinstance(lg, str) and lg.startswith("http") and not any(ext in lg.lower() for ext in ['.m3u8', '.ts', 'playlist']):
                            cur_logo = lg

                        # 2. Quét tìm các luồng phát stream thực thụ (.m3u8 hoặc live stream)
                        streams = []
                        for u_key in ["url", "stream_url", "m3u8", "link"]:
                            val = node.get(u_key)
                            if isinstance(val, str) and val.startswith("http"):
                                # Bỏ qua nếu bản thân giá trị url lại là một đường dẫn ảnh logo
                                if not any(ext in val.lower() for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif', 'image/small']):
                                    streams.append((val, node.get("title") or node.get("name") or node.get("blv") or ""))

                        for sk in ["streams", "links", "servers", "sources"]:
                            arr = node.get(sk)
                            if isinstance(arr, list):
                                for s in arr:
                                    if isinstance(s, str) and s.startswith("http"):
                                        if not any(ext in s.lower() for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif', 'image/small']):
                                            streams.append((s, ""))
                                    elif isinstance(s, dict):
                                        s_url = s.get("url") or s.get("link") or s.get("m3u8") or ""
                                        s_name = s.get("name") or s.get("title") or ""
                                        if s_url.startswith("http") and not any(ext in s_url.lower() for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif', 'image/small']):
                                            streams.append((s_url, s_name))

                        if not streams:
                            for sub_k, sub_v in node.items():
                                if isinstance(sub_v, str) and sub_v.startswith("http") and (".m3u8" in sub_v or ".ts" in sub_v or "live" in sub_v):
                                    if not any(ext in sub_v.lower() for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif', 'image/small']):
                                        streams.append((sub_v, node.get("title") or node.get("name") or ""))

                        # 3. Ghi ra playlist M3U chuẩn xác cho từng luồng stream
                        for s_url, s_name in streams:
                            if s_url not in seen_links:
                                seen_links.add(s_url)

                                parts = []
                                if cur_time:
                                    parts.append(cur_time)
                                if cur_title:
                                    parts.append(cur_title)
                                else:
                                    parts.append(f"{prov_name} Trực Tiếp")

                                display_base = " ".join(parts)

                                # Lấy tên BLV hoặc Server phát sạch sẽ
                                blv_tag = s_name or node.get("blv") or ""
                                if blv_tag and not any(kw in blv_tag.lower() for kw in ['url', 'href', 'logo', 'http', 'truc-tiep']):
                                    if blv_tag.lower() not in display_base.lower():
                                        display_base += f" ({blv_tag})"

                                final_logo = cur_logo if cur_logo else prov_logo
                                m3u_content += f"#EXTINF:-1 tvg-logo=\"{final_logo}\" group-title=\"{prov_name}\",{display_base}\n"

                                referer = node.get("Referer") or node.get("referer") or ""
                                ua = node.get("user_agent") or "Mozilla/5.0"
                                final_link = s_url
                                if referer:
                                    final_link = f"{s_url}|User-Agent={ua}&Referer={referer}"
                                elif ua != "Mozilla/5.0":
                                    final_link = f"{s_url}|User-Agent={ua}"
                                m3u_content += f"{final_link}\n"
                                count += 1

                        # Tiếp tục đệ quy xuống các nhánh con
                        for k, v in node.items():
                            if isinstance(v, (list, dict)):
                                process_node(v, cur_time, cur_title, cur_logo)

                for m in matches:
                    process_node(m, "", "", prov_logo)

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
                
            print(f"Đã tạo xong file playlist.m3u với {count} luồng trận đấu chuẩn xác tuyệt đối!")
            
        else:
            print(f"Lỗi HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == "__main__":
    generate_m3u_and_json()
    
