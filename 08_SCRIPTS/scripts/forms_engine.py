import os, re, json, datetime, requests
from bs4 import BeautifulSoup

SCAO_INDEX = "https://www.courts.michigan.gov/SCAO-forms/"
SCAO_FORMS_BASE = "https://www.courts.michigan.gov"

class FormsCatalog:
    """
    Crawls the SCAO forms site to build a catalog:
    - Category pages (e.g., General Use, FOC, Circuit, District, Probate)
    - Individual form PDFs (e.g., MC 01, FOC 65) and instruction PDFs (inst*)
    Produces: data/forms_catalog.json
    """
    def __init__(self, data_dir):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.out_path = os.path.join(self.data_dir, "forms_catalog.json")

    def _get(self, url, timeout=20):
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.text

    def _abs(self, href: str) -> str:
        if href.startswith("http"):
            return href
        return SCAO_FORMS_BASE + href

    def build(self):
        html = self._get(SCAO_INDEX)
        soup = BeautifulSoup(html, "lxml")
        # category links under the main forms page
        cats = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = (a.get_text() or "").strip()
            # only SCAO-forms subpages
            if "/SCAO-forms/" in href and href != "/SCAO-forms/":
                cats.append({"name": text, "url": self._abs(href)})
        catalog = {"built_at": datetime.datetime.now().isoformat(), "categories": []}

        # visit each category and extract form links (pdfs)
        for c in cats:
            try:
                ch = self._get(c["url"])
                cs = BeautifulSoup(ch, "lxml")
                forms = []
                for link in cs.find_all("a", href=True):
                    href = link["href"]
                    if href.lower().endswith(".pdf") and "/siteassets/forms" in href.lower():
                        title = (link.get_text() or "").strip()
                        num = None
                        # form number pattern like MC 01, FOC 65, etc.
                        m = re.search(r"\b([A-Z]{2,4}\s*\d+[a-z]?)\b", title, re.I)
                        if m:
                            num = m.group(1).upper().replace("  ", " ")
                        else:
                            # try from filename
                            base = os.path.basename(href)
                            fm = re.search(r"\b([A-Z]{2,4}\s*\d+[a-z]?)\b", base, re.I)
                            if fm:
                                num = fm.group(1).upper().replace("  ", " ")
                        forms.append({
                            "number": num,
                            "title": title,
                            "pdf": self._abs(href)
                        })
                catalog["categories"].append({"category": c["name"], "url": c["url"], "forms": forms})
            except Exception as e:
                catalog["categories"].append({"category": c["name"], "url": c["url"], "error": str(e), "forms": []})

        with open(self.out_path, "w", encoding="utf-8") as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)
        return {"count_categories": len(catalog["categories"]), "out": self.out_path}

class FormsForge:
    """
    Resolves ODB actions to SCAO form sets and returns the best match(es) with URLs.
    Uses forms_catalog.json if present; otherwise, offers static fallbacks for common actions.
    """
    STATIC_MAP = {
        "parenting_time_enforcement": ["FOC 65", "FOC 88", "MC 416"],
        "injunction_tro": ["MC 230"],
        "complaint_civil": ["MC 01", "MC 12"],
        "relief_from_judgment": ["MC 97"],
        "disqualification": ["MC 327"],
        "show_cause": ["MC 230", "FOC 65"],
        "appeal_leave": [],  # appellate forms vary by court
        "foia": [],
        "jtc": [],
    }

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.catalog_path = os.path.join(self.data_dir, "forms_catalog.json")
        self.catalog = None
        if os.path.exists(self.catalog_path):
            try:
                self.catalog = json.load(open(self.catalog_path, "r", encoding="utf-8"))
            except Exception:
                self.catalog = None

    def _lookup(self, form_number: str):
        if not self.catalog:
            return None
        target = form_number.upper().strip()
        hits = []
        for cat in self.catalog.get("categories", []):
            for f in cat.get("forms", []):
                if f.get("number") == target or (f.get("title") and target in f.get("title", "").upper()):
                    hits.append({"category": cat.get("category"), **f})
        return hits

    def resolve_for_action(self, action: str):
        a = action.lower()
        key = None
        if "parenting" in a:
            key = "parenting_time_enforcement"
        elif "injunction" in a or "tro" in a:
            key = "injunction_tro"
        elif "complaint" in a:
            key = "complaint_civil"
        elif "relief from judgment" in a:
            key = "relief_from_judgment"
        elif "disqualify" in a:
            key = "disqualification"
        elif "show cause" in a or "contempt" in a:
            key = "show_cause"
        elif "appeal" in a:
            key = "appeal_leave"
        elif "foia" in a:
            key = "foia"
        elif "jtc" in a or "canon" in a:
            key = "jtc"

        results = []
        if key and key in self.STATIC_MAP:
            for num in self.STATIC_MAP[key]:
                hit = self._lookup(num) if self.catalog else None
                if hit:
                    results.extend(hit)
                else:
                    results.append({"number": num, "title": "SCAO Form", "pdf": None, "category": None})
        return {"action": action, "forms": results}
