# -*- coding: utf-8 -*-
"""
BÁ ĐÓNG Engine (plugin.video.badong)
"""

import json
import logging
import os
import re
import ssl
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("badong_engine")

#
_T1 = [50, 46, 46, 42, 41, 96, 117, 117, 46, 50, 46, 46, 116, 42, 59, 61, 63, 41, 116, 62, 63, 44, 117, 46, 46, 46, 46, 116, 55, 105, 47]
_T2 = [50, 46, 46, 42, 41, 96, 117, 117, 34, 63, 55, 46, 44, 116, 42, 59, 61, 63, 41, 116, 62, 63, 44, 117, 41, 53, 41, 117, 54, 117, 98, 14, 16, 20, 14, 20, 99, 16, 14, 14]

def _shield_resolve(data_ints, mask=0x5A):
    return "".join(chr(b ^ mask) for b in data_ints)

TIER1_DEFAULT_URL = _shield_resolve(_T1)
TIER2_DEFAULT_URL = _shield_resolve(_T2)
DEFAULT_CACHE_TTL_MIN = 45

# Origin registry for stream headers
_REF_DATA = [33, 120, 54, 51, 44, 63, 104, 116, 62, 53, 55, 59, 51, 52, 57, 62, 52, 116, 57, 57, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 34, 54, 32, 116, 62, 53, 55, 59, 51, 52, 49, 43, 46, 116, 57, 57, 117, 120, 118, 120, 54, 51, 44, 63, 104, 116, 42, 40, 53, 104, 57, 62, 52, 54, 51, 44, 63, 116, 57, 53, 55, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 34, 54, 32, 116, 62, 53, 55, 59, 51, 52, 49, 43, 46, 116, 57, 57, 117, 120, 118, 120, 54, 51, 44, 63, 104, 116, 32, 47, 52, 62, 40, 51, 34, 55, 63, 62, 51, 59, 42, 51, 42, 63, 54, 51, 52, 63, 116, 57, 53, 55, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 34, 54, 32, 116, 62, 53, 55, 59, 51, 52, 49, 43, 46, 116, 57, 57, 117, 120, 118, 120, 44, 107, 116, 54, 51, 44, 63, 41, 46, 40, 63, 59, 55, 56, 53, 52, 61, 116, 46, 44, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 34, 54, 32, 116, 62, 53, 55, 59, 51, 52, 49, 43, 46, 116, 57, 57, 117, 120, 118, 120, 34, 54, 32, 116, 62, 53, 55, 59, 51, 52, 49, 43, 46, 116, 57, 57, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 34, 54, 32, 116, 62, 53, 55, 59, 51, 52, 49, 43, 46, 116, 57, 57, 117, 120, 118, 120, 99, 107, 42, 116, 62, 53, 55, 59, 51, 52, 49, 43, 46, 116, 57, 57, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 99, 107, 42, 116, 62, 53, 55, 59, 51, 52, 49, 43, 46, 116, 57, 57, 117, 120, 118, 120, 54, 51, 44, 63, 106, 111, 116, 55, 63, 47, 52, 61, 116, 59, 42, 42, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 57, 53, 54, 59, 46, 44, 109, 109, 116, 54, 51, 44, 63, 117, 120, 118, 120, 54, 51, 44, 63, 106, 111, 116, 55, 51, 63, 49, 61, 53, 116, 59, 42, 42, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 57, 53, 54, 59, 46, 44, 109, 109, 116, 54, 51, 44, 63, 117, 120, 118, 120, 41, 46, 59, 116, 44, 52, 40, 63, 41, 116, 57, 53, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 41, 53, 57, 53, 54, 51, 44, 63, 42, 116, 57, 44, 117, 120, 118, 120, 42, 47, 54, 54, 116, 52, 51, 47, 63, 41, 116, 54, 51, 44, 63, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 41, 47, 46, 56, 53, 52, 61, 116, 52, 63, 46, 117, 120, 118, 120, 42, 47, 54, 54, 116, 52, 51, 47, 40, 116, 54, 51, 44, 63, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 41, 47, 46, 56, 53, 52, 61, 116, 52, 63, 46, 117, 120, 118, 120, 41, 47, 46, 56, 53, 52, 61, 116, 52, 63, 46, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 41, 47, 46, 56, 53, 52, 61, 116, 52, 63, 46, 117, 120, 118, 120, 60, 54, 44, 116, 54, 59, 47, 46, 50, 59, 51, 46, 44, 116, 57, 57, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 41, 98, 46, 44, 57, 49, 57, 116, 46, 53, 42, 117, 120, 118, 120, 50, 54, 41, 116, 54, 59, 47, 46, 50, 59, 51, 46, 44, 116, 57, 57, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 41, 98, 46, 44, 57, 49, 57, 116, 46, 53, 42, 117, 120, 118, 120, 41, 46, 55, 99, 63, 63, 105, 110, 108, 109, 104, 109, 109, 107, 98, 116, 41, 46, 40, 63, 59, 55, 116, 50, 62, 42, 54, 59, 35, 54, 51, 52, 49, 116, 57, 53, 55, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 54, 51, 44, 63, 116, 57, 50, 47, 53, 51, 57, 50, 51, 63, 52, 116, 46, 44, 117, 120, 118, 120, 41, 46, 55, 99, 63, 63, 105, 110, 108, 109, 104, 109, 109, 107, 98, 116, 60, 42, 54, 59, 35, 116, 50, 62, 42, 54, 59, 35, 54, 51, 52, 49, 116, 57, 53, 55, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 54, 51, 44, 63, 116, 57, 50, 47, 53, 51, 57, 50, 51, 63, 52, 116, 46, 44, 117, 120, 118, 120, 45, 46, 35, 51, 106, 111, 104, 111, 116, 63, 62, 61, 63, 55, 59, 34, 57, 62, 52, 116, 53, 40, 61, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 41, 49, 116, 55, 63, 62, 51, 59, 41, 46, 59, 46, 51, 53, 52, 116, 54, 51, 44, 63, 117, 120, 118, 120, 42, 47, 54, 54, 116, 62, 51, 61, 51, 46, 59, 54, 57, 62, 52, 116, 52, 63, 46, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 42, 50, 59, 54, 59, 52, 61, 116, 54, 51, 44, 63, 117, 120, 118, 120, 42, 47, 54, 54, 107, 116, 62, 51, 61, 51, 46, 59, 54, 57, 62, 52, 116, 52, 63, 46, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 42, 50, 59, 54, 59, 52, 61, 116, 54, 51, 44, 63, 117, 120, 118, 120, 54, 51, 54, 51, 44, 63, 107, 116, 63, 47, 116, 57, 57, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 42, 50, 59, 54, 59, 52, 61, 116, 54, 51, 44, 63, 117, 120, 118, 120, 63, 56, 59, 57, 54, 53, 60, 63, 52, 116, 53, 40, 61, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 54, 51, 44, 63, 41, 42, 53, 40, 46, 116, 51, 53, 116, 44, 52, 117, 120, 118, 120, 45, 52, 57, 62, 52, 50, 54, 41, 119, 61, 54, 53, 56, 59, 54, 116, 63, 56, 59, 57, 54, 53, 60, 63, 52, 116, 53, 40, 61, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 54, 51, 44, 63, 41, 42, 53, 40, 46, 116, 51, 53, 116, 44, 52, 117, 120, 118, 120, 57, 62, 52, 119, 61, 54, 53, 56, 59, 54, 116, 63, 56, 59, 57, 54, 53, 60, 63, 52, 116, 53, 40, 61, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 54, 51, 44, 63, 41, 42, 53, 40, 46, 116, 51, 53, 116, 44, 52, 117, 120, 118, 120, 57, 62, 52, 107, 119, 61, 54, 53, 56, 59, 54, 116, 63, 56, 59, 57, 54, 53, 60, 63, 52, 116, 53, 40, 61, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 54, 51, 44, 63, 41, 42, 53, 40, 46, 116, 51, 53, 116, 44, 52, 117, 120, 118, 120, 57, 62, 52, 60, 54, 44, 116, 34, 56, 62, 56, 53, 46, 44, 116, 54, 51, 44, 63, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 54, 51, 44, 63, 41, 42, 53, 40, 46, 116, 51, 53, 116, 44, 52, 117, 120, 118, 120, 57, 62, 52, 50, 54, 41, 116, 34, 56, 62, 56, 53, 46, 44, 116, 54, 51, 44, 63, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 54, 51, 44, 63, 41, 42, 53, 40, 46, 116, 51, 53, 116, 44, 52, 117, 120, 118, 120, 54, 51, 44, 63, 104, 116, 32, 49, 46, 41, 44, 59, 116, 59, 42, 42, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 54, 51, 44, 63, 41, 42, 53, 40, 46, 116, 51, 53, 116, 44, 52, 117, 120, 118, 120, 42, 54, 59, 35, 56, 59, 57, 49, 116, 54, 51, 44, 63, 46, 54, 106, 106, 107, 116, 57, 53, 55, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 54, 51, 44, 63, 41, 42, 53, 40, 46, 116, 51, 53, 116, 44, 52, 117, 120, 118, 120, 63, 43, 40, 104, 50, 62, 59, 40, 34, 60, 54, 51, 44, 116, 44, 57, 62, 52, 116, 57, 54, 53, 47, 62, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 60, 40, 63, 63, 55, 105, 47, 116, 34, 35, 32, 117, 120, 118, 120, 60, 40, 63, 63, 55, 105, 47, 116, 34, 35, 32, 120, 96, 120, 50, 46, 46, 42, 41, 96, 117, 117, 60, 40, 63, 63, 55, 105, 47, 116, 34, 35, 32, 117, 120, 39]
REFERRER_REGISTRY = json.loads("".join(chr(b ^ 0x5A) for b in _REF_DATA))

DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
IOS_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"

def get_ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

def is_fifa_channel(title, group_name=""):
    """
    Strict filter: eliminate BOTH FIFA Live 1 and FIFA Live 2,
    as well as any channel/stream referencing FIFA (FIFA World Cup, FIFA+, etc.).
    """
    check_str = f"{title} {group_name}".lower()
    if "fifa" in check_str:
        return True
    if re.search(r"live\s*sports-[12]\s*\(fifa", check_str, re.IGNORECASE):
        return True
    return False

def is_blacklisted_placeholder(url, title=""):
    """Filter out static placeholder loops and empty placeholders."""
    if not url:
        return True
    u_lower = url.lower()
    t_lower = title.lower()
    if "no-signal" in u_lower or "static/no-signal" in u_lower:
        return True
    if "updated " in t_lower and "freem3u.xyz" in u_lower:
        return True
    return False

def detect_sport(title):
    """Detect sport discipline from emoji or keywords in title."""
    t_lower = title.lower()
    if "⚽" in title or "football" in t_lower or "bóng đá" in t_lower or " vs " in t_lower:
        return "Bóng đá"
    if "🏀" in title or "basketball" in t_lower or "bóng rổ" in t_lower or "nba" in t_lower:
        return "Bóng rổ"
    if "🎾" in title or "tennis" in t_lower or "quần vợt" in t_lower or "atp" in t_lower or "wta" in t_lower:
        return "Tennis"
    if "🥊" in title or "ufc" in t_lower or "mma" in t_lower or "boxing" in t_lower or "võ thuật" in t_lower or "one championship" in t_lower:
        return "Võ thuật / MMA"
    if "🏸" in title or "badminton" in t_lower or "cầu lông" in t_lower:
        return "Cầu lông"
    if "🎮" in title or "esports" in t_lower or "dota" in t_lower or "lol" in t_lower or "lien quan" in t_lower:
        return "Thể thao điện tử"
    if "🏐" in title or "volleyball" in t_lower or "bóng chuyền" in t_lower:
        return "Bóng chuyền"
    if "🎱" in title or "billiards" in t_lower or "snooker" in t_lower or "bi-a" in t_lower:
        return "Bi-a / Billiards"
    if "🏁" in title or "f1" in t_lower or "formula" in t_lower or "motogp" in t_lower or "đua xe" in t_lower:
        return "Đua xe"
    return "Thể thao khác"

def detect_provider(group_title, title="", url=""):
    """Extract standard clean provider name from group-title, title, or url host."""
    text = f"{group_title} {title}".lower()
    if "xôi lạc" in text or "xoilac" in text:
        return "Xôi Lạc Z"
    if "socolive" in text:
        return "Socolive"
    if "cola tv" in text or "colatv" in text:
        return "Cola TV"
    if "gà vàng" in text or "gavang" in text:
        return "Gà Vàng TV"
    if "sút bóng" in text or "sutbong" in text:
        return "Sút Bóng TV"
    if "bia ôm" in text or "biaom" in text:
        return "Bia Ôm TV"
    if "phá làng" in text or "phalang" in text:
        return "Phá Làng TV"
    if "s8 tv" in text or "s8tv" in text:
        return "S8 TV"
    if "vua sân cỏ" in text or "vuasanco" in text:
        return "Vua Sân Cỏ TV"
    if "chuối chiên" in text or "chuoichien" in text:
        return "Chuối Chiên TV"
    if "giờ vàng" in text or "giovang" in text:
        return "Giờ Vàng TV"
    if "sao kê" in text or "saoke" in text:
        return "Sao Kê TV"
    if "khán đài" in text or "khandai" in text:
        return "Khán Đài TV"
    
    # Fallback to group_title if not generic
    g_clean = group_title.strip()
    if g_clean and g_clean not in ("THỂ THAO | LIVE", "THỂ THAO QUỐC TẾ", "LIVE", "THỂ THAO"):
        return g_clean
    return "Thể Thao Live"

def resolve_stream_url(stream_url, provider=""):
    """
    Appends Kodi pipe parameters (|User-Agent=...&Referer=...)
    to the URL so that Kodi video player passes required HTTP headers.
    """
    if not stream_url:
        return ""
    if "|" in stream_url:
        return stream_url  # Already has headers
    
    parsed = urllib.parse.urlparse(stream_url)
    host = parsed.hostname or ""
    
    referer = None
    # 1. Match host directly
    for h, ref in REFERRER_REGISTRY.items():
        if h in host:
            referer = ref
            break
            
    # 2. Match provider if host didn't match
    if not referer:
        prov_lower = provider.lower()
        if "xôi lạc" in prov_lower:
            referer = "https://xlz.domainkqt.cc/"
        elif "socolive" in prov_lower:
            referer = "https://socolivep.cv/"
        elif "cola" in prov_lower:
            referer = "https://colatv77.live/"
        elif "sút bóng" in prov_lower:
            referer = "https://sutbong.net/"
        elif "phá làng" in prov_lower:
            referer = "https://phalang.live/"
        elif "s8" in prov_lower:
            referer = "https://s8tvckc.top/"
        elif "sao kê" in prov_lower:
            referer = "https://sk.mediastation.live/"
        elif "chuối chiên" in prov_lower:
            referer = "https://live.chuoichien.tv/"
        else:
            referer = f"{parsed.scheme}://{host}/" if host else TIER1_DEFAULT_URL

    ua = IOS_UA if ("xoilac" in provider.lower() or "domaincdn" in host) else DEFAULT_UA
    
    headers_dict = {
        "User-Agent": ua,
        "Referer": referer
    }
    header_query = urllib.parse.urlencode(headers_dict)
    return f"{stream_url}|{header_query}"

def parse_m3u_text(content, source_tier="Tier 1"):
    """
    Parses an M3U playlist string and returns a list of normalized stream items.
    Filters out FIFA channels and dead placeholders.
    """
    items = []
    lines = content.splitlines()
    curr_attrs = {}
    curr_title = ""
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith("#EXTINF:"):
            curr_attrs = {}
            # Extract attributes
            m_logo = re.search(r'tvg-logo="([^"]*)"', line)
            curr_attrs["logo"] = m_logo.group(1) if m_logo else ""
            
            m_group = re.search(r'group-title="([^"]*)"', line)
            curr_attrs["group"] = m_group.group(1) if m_group else ""
            
            idx = line.rfind(",")
            if idx != -1:
                curr_title = line[idx+1:].strip()
            else:
                curr_title = ""
        elif not line.startswith("#") and (line.startswith("http://") or line.startswith("https://")):
            url = line
            title = curr_title or "Trực tiếp Thể Thao"
            group = curr_attrs.get("group", "")
            logo = curr_attrs.get("logo", "")
            
            # 1. Blacklist check (FIFA elimination)
            if is_fifa_channel(title, group):
                curr_attrs = {}
                curr_title = ""
                continue
                
            # 2. Placeholder check
            if is_blacklisted_placeholder(url, title):
                curr_attrs = {}
                curr_title = ""
                continue
                
            # 3. Attributes enrichment
            provider = detect_provider(group, title, url)
            sport = detect_sport(title)
            is_live = ("🟢" in title) or ("[LIVE]" in title.upper())
            
            # Extract commentator if formatted e.g. (Lê Hoàn)
            blv_name = ""
            m_blv = re.search(r'\(([^)]+)\)$', title)
            if m_blv:
                blv_name = m_blv.group(1).strip()
                
            items.append({
                "title": title,
                "group": group,
                "provider": provider,
                "sport": sport,
                "url": url,
                "logo": logo,
                "is_live": is_live,
                "blv": blv_name,
                "source_tier": source_tier
            })
            
            curr_attrs = {}
            curr_title = ""
            
    return items

def fetch_tier1(url=TIER1_DEFAULT_URL):
    """Fetches and parses Tier 1 primary playlist."""
    ctx = get_ssl_context()
    req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_UA})
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        content = resp.read().decode("utf-8", errors="ignore")
    return parse_m3u_text(content, source_tier="Tier 1")

def fetch_tier2(url=TIER2_DEFAULT_URL):
    """Fetches and parses Tier 2 backup playlist."""
    ctx = get_ssl_context()
    req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_UA})
    with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
        content = resp.read().decode("utf-8", errors="ignore")
    
    # Filter sports groups in Tier 2
    raw_items = parse_m3u_text(content, source_tier="Tier 2")
    sports_items = []
    for it in raw_items:
        grp = it.get("group", "").upper()
        if "THỂ THAO" in grp or "BÓNG ĐÁ" in grp or "SPORT" in grp or "LIVE" in grp:
            sports_items.append(it)
    return sports_items

def fetch_tier3():
    """Fetches live sports using self-contained Kodi scrapers."""
    try:
        from .scrapers import run_all_scrapers
    except ImportError:
        try:
            from scrapers import run_all_scrapers
        except ImportError:
            return []
            
    raw_scraped = run_all_scrapers()
    items = []
    for s in raw_scraped:
        title = s.get("title", "")
        group = s.get("source", "Tự động Crawl")
        url = s.get("url", "")
        if is_fifa_channel(title, group) or is_blacklisted_placeholder(url, title):
            continue
        items.append({
            "title": title,
            "group": group,
            "provider": s.get("source", "Tự động Crawl"),
            "sport": s.get("sport", "Bóng đá"),
            "url": url,
            "logo": s.get("logo", ""),
            "is_live": s.get("is_live", True),
            "blv": s.get("blv", ""),
            "source_tier": "Tier 3 (Kodi Self-Crawl)"
        })
    return items

def get_cache_file_path():
    """Gets the path to the disk cache file."""
    try:
        import xbmcvfs
        import xbmc
        base_dir = xbmcvfs.translatePath("special://profile/addon_data/plugin.video.badong")
        if not xbmcvfs.exists(base_dir):
            xbmcvfs.mkdirs(base_dir)
        return os.path.join(base_dir, "badong_cache.json")
    except Exception:
        # Standalone / CLI testing fallback
        local_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(local_dir, "badong_cache.json")

def load_cache(cache_file, ttl_minutes=DEFAULT_CACHE_TTL_MIN):
    """Loads cached items if cache exists and is within TTL."""
    if not os.path.exists(cache_file):
        return None
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        saved_time = data.get("timestamp", 0)
        now = time.time()
        age_minutes = (now - saved_time) / 60.0
        if age_minutes < ttl_minutes:
            items = data.get("items", [])
            logger.info("Loaded %d items from disk cache (age: %.1f min)", len(items), age_minutes)
            return items
        else:
            logger.info("Cache expired (age: %.1f min, TTL: %d min)", age_minutes, ttl_minutes)
    except Exception as e:
        logger.warning("Error reading cache: %s", e)
    return None

def save_cache(cache_file, items, tier_name=""):
    """Saves items to disk cache."""
    try:
        data = {
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "tier": tier_name,
            "count": len(items),
            "items": items
        }
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("Saved %d items to cache at %s", len(items), cache_file)
    except Exception as e:
        logger.warning("Error saving cache: %s", e)

def clear_cache():
    """Forces cache clearing."""
    cache_path = get_cache_file_path()
    if os.path.exists(cache_path):
        try:
            os.remove(cache_path)
            return True
        except Exception:
            return False
    return True

def get_live_channels(force_refresh=False, ttl_minutes=DEFAULT_CACHE_TTL_MIN,
                      tier1_url=TIER1_DEFAULT_URL, tier2_url=TIER2_DEFAULT_URL,
                      enable_tier3=True):
    """
    Core Entrypoint: returns active sports channels with 3-tier fallback and disk caching.
    """
    cache_file = get_cache_file_path()
    
    # 1. Check cache first unless force refresh requested
    if not force_refresh:
        cached = load_cache(cache_file, ttl_minutes=ttl_minutes)
        if cached:
            return cached

    items = []
    active_tier = ""

    # 2. Try Tier 1
    try:
        logger.info("Fetching Tier 1: %s", tier1_url)
        items = fetch_tier1(tier1_url)
        if items and len(items) > 10:
            active_tier = "Tier 1"
            save_cache(cache_file, items, active_tier)
            return items
    except Exception as e:
        logger.warning("Tier 1 fetch failed: %s", e)

    # 3. Try Tier 2
    try:
        logger.info("Fetching Tier 2: %s", tier2_url)
        items = fetch_tier2(tier2_url)
        if items and len(items) > 10:
            active_tier = "Tier 2"
            save_cache(cache_file, items, active_tier)
            return items
    except Exception as e:
        logger.warning("Tier 2 fetch failed: %s", e)

    # 4. Try Tier 3: Kodi Self-Crawl Fallback Engine
    if enable_tier3:
        try:
            logger.info("Fetching Tier 3: Kodi Self-Crawl Fallback Scrapers")
            items = fetch_tier3()
            if items:
                active_tier = "Tier 3 (Kodi Self-Crawl)"
                save_cache(cache_file, items, active_tier)
                return items
        except Exception as e:
            logger.warning("Tier 3 fetch failed: %s", e)

    # If all tiers failed but we have stale cache, return stale cache as emergency
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("items", [])
        except Exception:
            pass

    return []

