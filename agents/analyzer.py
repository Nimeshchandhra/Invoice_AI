import re
import json
from utils.llm import generate_response


# -------------------------
# RULE-BASED EXTRACTION
# -------------------------

def extract_total(context):
    m = re.search(r'Balance Due:\s*\$?\s*(\d+\.\d+)', context, re.I)
    if m:
        return f"${m.group(1)}"

    amounts = re.findall(r'\$\s?\d+\.\d+', context)
    return amounts[-1] if amounts else None


def extract_date(context):
    m = re.search(r'\b[A-Za-z]{3}\s+\d{1,2}\s+\d{4}\b', context)
    return m.group() if m else None


def extract_vendor_rule(context):
    lines = context.split("\n")

    for l in lines[:10]:
        l = l.strip()

        if not l:
            continue

        # skip junk
        if any(x in l.lower() for x in ["invoice", "bill to", "ship to", "#", "date"]):
            continue

        if len(l) < 40:
            return l

    return None


def extract_items_rule(context):
    items = []

    for l in context.split("\n"):
        l = l.strip()

        if not l:
            continue

        if "$" in l and any(c.isalpha() for c in l):
            if not any(x in l.lower() for x in ["subtotal", "total", "discount", "shipping", "balance"]):
                items.append(l)

    return items if len(items) > 0 else None


# -------------------------
# LLM FALLBACKS
# -------------------------

def llm_extract_items(context):
    print("🔥 LLM CALLED FOR ITEMS")

    prompt = f"""
Extract the item names from this invoice.

Rules:
- Return ONLY item names
- No explanation
- If multiple → comma separated

Context:
{context}
"""

    try:
        res = generate_response(prompt)
        print("RAW LLM RESPONSE:", res)

        # 🔥 fallback parsing (NO JSON dependency)
        items = [i.strip() for i in res.split(",") if i.strip()]

        return items if items else None

    except Exception as e:
        print("LLM ERROR:", e)
        return None

def llm_extract_vendor(context):
    print("🔥 LLM CALLED FOR VENDOR")

    prompt = f"""
Extract the vendor/company name from this invoice.

Rules:
- Return ONLY the name
- No explanation

Context:
{context}
"""

    try:
        res = generate_response(prompt)
        print("RAW VENDOR RESPONSE:", res)

        return res.strip()
    except:
        return None
# -------------------------
# MAIN ANALYZER
# -------------------------

def analyze(query, docs):
    context = "\n".join([d.page_content for d in docs])

    # ---- RULES ----
    total = extract_total(context)
    date = extract_date(context)
    vendor = extract_vendor_rule(context)
    items = extract_items_rule(context)

    # ---- LLM FALLBACK ----

    # vendor fallback
    if not vendor:
        vendor = llm_extract_vendor(context)

    # items fallback (IMPORTANT FIX)
    if not items or len(items) == 0:
        items = llm_extract_items(context)

    return {
        "vendor": vendor,
        "total_amount": total,
        "item_name": items,
        "date": date
    }