import json
import os
import time
import urllib.request
import urllib.error

def load_api_key():
    k = os.environ.get("FRED_API_KEY", "").strip()
    if k:
        return k
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "fred_api_key.txt")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return f.read().strip()
    raise SystemExit("set FRED_API_KEY env var or create config/fred_api_key.txt")


API_KEY = load_api_key()
BASE = "https://api.stlouisfed.org/fred"

CANDIDATES = {
    "money_supply": ["M2SL", "M2REAL", "WM2NS", "BOGMBASE", "AMBSL", "BASE", "TRESEGUSM052N", "WRESBAL"],
    "inflation_index": ["CPIAUCSL", "PCEPI", "PPIACO", "PPIFIS", "GDPDEF", "CPILFESL", "PCEPILFE"],
    "real_output": ["GDPC1", "GDP", "GDPPOT", "PCECC96"],
    "rate_federal": ["FEDFUNDS", "DFF", "DGS10", "DGS2", "GS10", "GS2", "DGS1", "TB3MS"],
    "rate_state_local": ["WSLB20", "MSLB20", "BAMLC0A1CAAAEY", "SLBYY", "MUNIYIELD"],
    "rate_mortgage": ["MORTGAGE30US", "MORTGAGE15US", "MORTG"],
    "rate_business": ["BAA", "AAA", "DBAA", "DAAA", "MPRIME", "DPRIME", "BAMLC0A4CBBBEY"],
    "rate_consumer": ["TERMCBCCALLNS", "TERMCBPER24NS", "TERMCBAUTO48NS", "RIFLPBCIANM60NM", "DRCCLACBS"],
    "debt_federal": ["GFDEBTN", "FYGFDPUN", "FGTBFDPUN", "FDHBPIN", "GFDEGDQ188S"],
    "debt_state_local": ["SLGSDODNS", "SLDODNS", "ASLSDODNS"],
    "debt_mortgage": ["HHMSDODNS", "MDOAH", "ASTMA", "HMLBSHNO", "RHEACBW027SBOG"],
    "debt_business": ["TBSDODNS", "BCNSDODNS", "NCBDBIQ027S", "TODNS", "BOGZ1FL144104005Q"],
    "debt_consumer": ["TOTALSL", "CMDEBT", "CCLACBW027SBOG", "HNOCDLNS", "CONSUMER"],
    "fed_balance_sheet": ["WALCL", "TREAST", "WSHOMCB", "WSHOSHO", "WSHOTSL", "RESPPMA", "QBPBSTAS", "GFDEGDQ188S"],
}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "research-fetch"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:200]
    except Exception as e:
        return "ERR", str(e)


def main():
    rows = []
    for category, ids in CANDIDATES.items():
        for sid in ids:
            url = f"{BASE}/series?series_id={sid}&api_key={API_KEY}&file_type=json"
            status, body = fetch(url)
            if status == 200 and isinstance(body, dict) and body.get("seriess"):
                s = body["seriess"][0]
                rows.append((category, sid, "OK", s.get("frequency_short"), s.get("units_short"), s.get("observation_start"), s.get("observation_end"), s.get("title")))
            else:
                rows.append((category, sid, f"FAIL:{status}", "", "", "", "", str(body)[:80]))
            time.sleep(0.12)
    for r in rows:
        print(" | ".join(str(x) for x in r))


if __name__ == "__main__":
    main()
