"""
Read off-plan sale terms out of an advert's (already masked) text, in English and Amharic,
for the thesis on off-plan apartments (owner, 13 Nov 2026). Every field is optional: an
advert that does not state a term gets None. Nothing here goes online.

Fields: developer, construction_status, construction_progress_pct, finish_level,
down_payment_pct, down_payment_amount, instalment_plan, stage_linked, bank_loan, handover,
discount_schedule, stated_price_per_m2 (and semi/full-finished prices per m2 when both are
given), plus has_payment_terms.
"""
import re

I = re.I
NUM = r"\d[\d,]*(?:\.\d+)?"

# ---------------------------------------------------------------- developer
KNOWN_DEVELOPERS = [
    "temer", "noah", "noh", "gift", "sunshine", "ayat", "flintstone", "enyi", "tsehay", "ovid", "abenezer",
    "jambo", "metropolitan", "blue sky", "afro tsion", "reportage", "nolawi", "bole pride", "habesha", "dmc",
    "zemen", "sky light", "century", "imperial", "delta", "elite", "getas", "big group", "aman", "hope",
    "mega", "sefer", "elilta", "visco", "prestigious", "royal", "sky way", "zerihun",
]
_DEV_SUFFIX = r"(?:real[\s-]?estates?|realestates?|properties|property\s+development|homes|developers?|development|plc|share\s+company|s\.c\.)"
KNOWN_DEV = re.compile(r"\b(" + "|".join(d.replace(" ", r"[\s-]?") for d in KNOWN_DEVELOPERS) + r")[\s-]+" + _DEV_SUFFIX + r"\b", I)
NAMED_DEV = re.compile(r"\b([A-Za-z]{3,}(?:[\s-][A-Za-z]{3,})?)[\s-]+" + _DEV_SUFFIX + r"\b", I)
AM_DEV = re.compile(r"([ሀ-፿]{2,})\s*(?:ሪል\s*እስቴት|ሪልእስቴት|ሪል\s*ስቴት)")
# words that come before "real estate" but are not a developer's name
NOT_A_NAME = {
    "for", "sale", "the", "addis", "ababa", "apartment", "apartments", "house", "villa", "best", "new", "luxury",
    "luxurious", "ethiopia", "ethio", "rent", "sell", "sells", "selling", "commercial", "property", "and", "with",
    "our", "your", "real", "estate", "estates", "bole", "cmc", "top", "big", "good", "from", "this", "that",
    "bedroom", "modern", "affordable", "kazanchis", "gerji", "rwanda", "sarbet", "ayat zone", "around", "near",
    "in", "at", "by", "of", "residential", "premium", "classic", "quality", "nice", "beautiful", "urgent",
}


def find_developer(text):
    m = KNOWN_DEV.search(text)
    if m:
        return re.sub(r"\s+", " ", m.group(0)).strip()
    for m in NAMED_DEV.finditer(text):
        words = m.group(1).lower().replace("-", " ").split()
        if words and words[-1] not in NOT_A_NAME and " ".join(words) not in NOT_A_NAME:
            name = words[-1] if words[0] in NOT_A_NAME else " ".join(words)
            return f"{name} {m.group(0)[len(m.group(1)):].strip()}".strip()
    m = AM_DEV.search(text)
    if m:
        return m.group(0)
    return None


# ---------------------------------------------------------------- construction
OFFPLAN = re.compile(
    r"under(?:[\s-]+\w+)?[\s-]+construction|off[\s-]?plan|pre[\s-]?sale|presale|on[\s-]?going\s+(?:project|construction)|"
    r"construction\s+(?:is\s+)?(?:in\s+progress|ongoing)|will\s+be\s+(?:completed|finished|delivered|built)|"
    r"we\s+will\s+build|hand\w*(?:\s+\w+){0,2}\s+over\s+(?:to\s+you\s+)?(?:with)?in\s+\d|"
    r"በግንባታ\s*ላይ|ግንባታ\w*\s*(?:ላይ|በመካሄድ)|እየተገነባ|የሚጠናቀ\w*|ተገንብቶ\s*የሚያልቅ|ማስረከቢያ\s*ጊዜ", I)
READY = re.compile(r"ready\s+to\s+move|move[\s-]?in\s+ready|ready\s+for\s+(?:living|occupancy)|title\s+deed|"
                   r"fully\s+(?:built|completed)|ካርታ\s*(?:ያለው|ያላቸ\w*|አለው|ተዘጋጅቷል)|ለመኖሪያ\s*ዝግጁ|ለኑሮ\s*ዝግጁ|ሰው\s*መኖር\s*የጀመረ|"
                   r"ተጠናቅቆ\s*ያለቀ|ሙሉ\s*በሙሉ\s*የተጠናቀቀ|100\s?%\s*ተገንብቶ\s*ያለቀ|ወዲያውኑ\s*የሚረከቡ", I)
NEW_PROJECT = re.compile(r"new\s+(?:block|project|building\s+for\s+sale)|አዲስ\s*(?:ብሎክ|ፕሮጀክት|ሳይት)", I)
PROGRESS = re.compile(r"(\d{1,3})\s?%\s*(?:constructed|completed|complete|built|done|finished|of\s+(?:the\s+)?construction)|"
                      r"(?:construction|ግንባታ\w*)\D{0,20}?(\d{1,3})\s?%", I)
SEMI = re.compile(r"semi[\s-]?finish\w*|ሴሚ\s*ፊኒሺ\w*|ከፊል\s*ያለቀ", I)
FULL = re.compile(r"ful+y?[\s-]?finish\w*|full[\s-]?finsh\w*|ሙሉ\s*በሙሉ\s*ያለቀ|ፉል\s*ፊኒሺ\w*", I)

# ---------------------------------------------------------------- payment
DOWN = re.compile(r"(\d{1,2}(?:\.\d)?)\s?%\s*(?:down[\s-]?payment|downpayment|down\b|up[\s-]?front|advance|initial|deposit|"
                  r"ቅድመ\s*ክፍያ)|(?:down[\s-]?payment|downpayment|ቅድመ\s*ክፍያ|advance\s+payment)\D{0,12}?(\d{1,2}(?:\.\d)?)\s?%", I)
DOWN_AMOUNT = re.compile(r"(?:down[\s-]?payment|ቅድመ\s*ክፍያ)[^.\n]{0,20}?%\s*=?\s*(" + NUM + r")", I)
INSTAL_N = re.compile(r"(\d{1,2})\s*(?:equal\s+)?(?:instal+ments?|payments|ዙር)", I)
INSTAL_PERIOD = re.compile(r"(?:pay|paid|payable|rest|remaining|balance|ይከፈላል|በመክፈል)[^.\n]{0,40}?(?:in|over|within|for)?\s*(\d{1,3})\s*(months?|years?|ወር|አመት|ዓመት)|"
                           r"(monthly|quarterly|every\s+\d+\s+months|በየወሩ|በየሶስት\s*ወሩ)\s*(?:instal+ments?|payments?)?", I)
INSTAL_AMOUNT = re.compile(r"(?:instal+ment|payment|pay|ክፍያ)[^.\n]{0,30}?(" + NUM + r")\s*(?:etb|birr|ብር)?\s*(?:per|a|/|በ)\s*(?:month|ወር)", I)
AM_REST = re.compile(r"(በ[^#\n.]{2,25}?)\s*ቀሪው\w*|ቀሪው\w*\s*(በ[^#\n.]{2,25})")
INSTAL_WORD = re.compile(r"instal+ments?|payment\s+(?:plan|schedule|terms?)|flexible\s+payment|በክፍያ|ክፍያ\s*እቅድ|በረጅም\s*ጊዜ\s*ክፍያ", I)
STAGE = re.compile(r"(?:rest|remaining|balance)[^.\n]{0,30}?(?:through|according\s+to|based\s+on|as\s+per|with)\s+(?:the\s+)?(?:construction\s+)?progress|(?:foundation|basement|slab|frame|structure|roof|finishing|floor|stage|phase|ፋውንዴሽን|ስትራክቸር|ፊኒሺንግ)"
                   r"[^.\n]{0,40}(?:pay|payment|instal|ክፍያ)|(?:pay|payment|instal|ክፍያ)[^.\n]{0,40}"
                   r"(?:foundation|basement|slab|frame|structure|roof|finishing|construction\s+(?:stage|progress)|stage|phase|"
                   r"ፋውንዴሽን|ስትራክቸር|ፊኒሺንግ)", I)
LOAN = re.compile(r"(\d{1,3})\s?%\s*(?:bank\s*loan|loan|mortgage|የባንክ\s*ብድር|ብድር)|(?:bank\s*loan|mortgage|የባንክ\s*ብድር)(?:[^.]{0,30}?(\d{1,3})\s?%)?", I)
UP_TO = re.compile(r"up\s+to|እስከ", I)
LOAN_YEARS = re.compile(r"(\d{1,2})\s*(?:years?|yrs?|አመት|ዓመት)", I)

# ---------------------------------------------------------------- handover
HANDOVER = re.compile(
    r"(?:hand\w*(?:\s+\w+){0,2}\s+over|handover|deliver\w*|complet\w*|finish\w*|ready)\s+(?:to\s+you\s+)?"
    r"(?:with)?in\s+(\d{1,2}(?:\.\d)?)\s*(months?|years?)|"
    r"ማስረከቢያ\s*ጊዜ\w*\s*:?\s*([^#\n.]{2,25}?)(?=\s{2,}|\s*\d+\s*መኝታ|$)|"
    r"(?:hand\w*(?:\s+\w+){0,2}\s+over|handover|delivery|completion|complet\w*|ready)\D{0,25}?((?:end\s+of\s+|by\s+)?20[2-3]\d|"
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+20[2-3]\d)|"
    r"(\d{1,2})\s*(ወር|አመት|ዓመት)\s*ውስጥ\s*(?:ርክክብ|የሚጠናቀቅ|ይጠናቀቃል|እናስረክባለን)|"
    r"(?:ርክክብ|ይጠናቀቃል|የሚጠናቀቅ)\D{0,20}?(20[12]\d|20[2-3]\d)\s*(?:ዓ\.?ም)?|"
    r"በ\s*(20[12]\d)\s*ዓ\.?ም\.?\s*(?:ርክክብ|የሚጠናቀቅ|ይጠናቀቃል)", I)

# ---------------------------------------------------------------- discount
DISC_CONTEXT = re.compile(r"discount|ቅናሽ|off\b", I)
DISC_PAIR = re.compile(r"(\d{2,3})\s?%\s*(?:payment|paid|pay|upfront|cash)?\s*(?:=|->|→|:|gets?|get|ለ|ላይ)\s*(\d{1,2}(?:\.\d)?)\s?%", I)
DISC_CASH = re.compile(r"(\d{1,2}(?:\.\d)?)\s?%\s*(?:discount|off|ቅናሽ)[^.\n]{0,40}?(cash|full|100\s?%|upfront|one[\s-]?time|"
                       r"early|በአንድ\s*ጊዜ|ሙሉ\s*ክፍያ)|(?:cash|full\s+payment|pay(?:ing)?\s+in\s+full|በአንድ\s*ጊዜ|ሙሉ\s*ክፍያ)"
                       r"[^.\n]{0,40}?(\d{1,2}(?:\.\d)?)\s?%\s*(?:discount|off|ቅናሽ)", I)
DISC_FLAT = re.compile(r"(\d{1,2}(?:\.\d)?)\s?%\s*(?:discount\w*|off\b|ቅናሽ)|(?:discount\w*|ቅናሽ)\s*(?:of\s+)?(\d{1,2}(?:\.\d)?)\s?%", I)
DISC_WORD = re.compile(r"discount\w*|ቅናሽ", I)

# ---------------------------------------------------------------- price per m2
PPM = re.compile(r"(" + NUM + r")\s*(?:etb|birr|br|ብር)?\s*(?:per|/|a)\s*(?:m²|m2|sqm|sq\.?\s*m|square\s*met(?:er|re)s?|ካሬ)|"
                 r"(?:በካሬ|ካሬው|per\s+(?:m²|m2|sqm|square\s*met(?:er|re)))\s*(?:ሜትር)?\s*:?\s*በ?\s*(" + NUM + r"\s*ሺ?)|"
                 r"price\s+per\s+(?:square\s*met(?:er|re)|m²|m2|sqm)\s*:?\s*(" + NUM + r")", I)
PPM_SEMI = re.compile(r"semi[\s-]?finish\w*[^\n]{0,40}?(?:per\s+(?:square\s*met(?:er|re)|m²|m2|sqm)|በካሬ)\s*:?\s*(" + NUM + r")", I)
PPM_FULL = re.compile(r"ful+y?[\s-]?finish\w*[^\n]{0,40}?(?:per\s+(?:square\s*met(?:er|re)|m²|m2|sqm)|በካሬ)\s*:?\s*(" + NUM + r")", I)


def _num(s):
    s = str(s)
    mult = 1000 if "ሺ" in s else 1
    try:
        return float(s.replace(",", "").replace("ሺ", "").strip()) * mult
    except (TypeError, ValueError):
        return None


def _plausible_ppm(v):
    return v is not None and 10_000 <= v <= 1_500_000  # birr per m2 for Addis flats


def _first_group(m):
    return next((g for g in m.groups() if g), None) if m else None


def extract_terms(text, url=""):
    """Return a dict of off-plan terms found in the (masked) advert text; the web address
    is used only as a fallback for the developer's name."""
    t = re.sub(r"[ \t]+", " ", text or "")
    out = {k: None for k in ("developer", "construction_status", "construction_progress_pct", "finish_level",
                             "down_payment_pct", "down_payment_amount", "instalment_plan", "stage_linked",
                             "bank_loan", "handover", "discount_schedule", "stated_price_per_m2",
                             "price_per_m2_semi", "price_per_m2_full")}
    out["developer"] = find_developer(t) or (find_developer(re.sub(r"[-_/]+", " ", url.rstrip("/").split("/")[-1]))
                                             if url else None)

    prog = PROGRESS.search(t)
    if prog:
        v = _num(_first_group(prog))
        if v is not None and 0 < v <= 100:
            out["construction_progress_pct"] = v
    if OFFPLAN.search(t) or (out["construction_progress_pct"] and out["construction_progress_pct"] < 100):
        out["construction_status"] = "under construction"
    elif READY.search(t):
        out["construction_status"] = "ready"

    semi, full = SEMI.search(t), FULL.search(t)
    out["finish_level"] = "semi and full finished offered" if semi and full else (
        "semi-finished" if semi else ("fully finished" if full else None))

    d = DOWN.search(t)
    if d:
        out["down_payment_pct"] = _num(_first_group(d))
        a = DOWN_AMOUNT.search(t)
        if a:
            out["down_payment_amount"] = _num(a.group(1))

    plan = []
    n = INSTAL_N.search(t)
    if n:
        plan.append(f"{n.group(1)} instalments")
    p = INSTAL_PERIOD.search(t)
    if p and (INSTAL_WORD.search(t) or d or n):
        plan.append(" ".join(g for g in p.groups() if g).strip())
    rest = AM_REST.search(t)
    if rest:
        plan.append("rest paid " + _first_group(rest).strip())
    amt = INSTAL_AMOUNT.search(t)
    if amt:
        plan.append(f"{amt.group(1)} birr per month")
    if not plan and INSTAL_WORD.search(t):
        plan.append("instalments mentioned, no details")
    out["instalment_plan"] = "; ".join(dict.fromkeys(plan)) or None
    out["stage_linked"] = True if STAGE.search(t) else None
    if out["stage_linked"] and not out["construction_status"]:
        out["construction_status"] = "under construction"

    loan = LOAN.search(t)
    if loan:
        bits = []
        pct = loan.group(1) or loan.group(2)
        if pct:
            up_to = "up to " if UP_TO.search(loan.group(0)) else ""
            bits.append(f"{up_to}{pct}% bank loan")
        else:
            bits.append("bank loan")
        y = LOAN_YEARS.search(t[max(0, loan.start() - 20):loan.end() + 40])
        if y:
            bits.append(f"over {y.group(1)} years")
        out["bank_loan"] = " ".join(bits)

    h = HANDOVER.search(t)
    if h:
        g = [x for x in h.groups() if x]
        out["handover"] = " ".join(g)

    sched = []
    if DISC_CONTEXT.search(t):
        for m in DISC_PAIR.finditer(t):
            paid, off = _num(m.group(1)), _num(m.group(2))
            if paid and off and 10 <= paid <= 100 and 0 < off < 50 and off < paid:
                sched.append(f"{m.group(1)}% paid -> {m.group(2)}% off")
    if not sched:
        c = DISC_CASH.search(t)
        if c:
            pct = c.group(1) or c.group(3)
            sched.append(f"{pct}% off for cash/full payment")
    if not sched:
        f = DISC_FLAT.search(t)
        if f:
            sched.append(f"{_first_group(f)}% discount (terms not stated)")
        elif DISC_WORD.search(t):
            sched.append("discount mentioned, no figure")
    out["discount_schedule"] = "; ".join(dict.fromkeys(sched)) or None

    for key, rx in (("price_per_m2_semi", PPM_SEMI), ("price_per_m2_full", PPM_FULL)):
        m = rx.search(t)
        if m and _plausible_ppm(_num(m.group(1))):
            out[key] = _num(m.group(1))
    for m in PPM.finditer(t):
        v = _num(_first_group(m))
        if _plausible_ppm(v):
            out["stated_price_per_m2"] = v
            break
    if out["stated_price_per_m2"] is None:
        out["stated_price_per_m2"] = out["price_per_m2_full"] or out["price_per_m2_semi"]

    # Owner, 13 Nov 2026: a developer-style down payment (or a "new block / new project")
    # without the words "under construction" or "ready" is "probably off-plan".
    if not out["construction_status"] and (out["down_payment_pct"] or out["instalment_plan"] or NEW_PROJECT.search(t)):
        out["construction_status"] = "probably off-plan"

    out["has_payment_terms"] = bool(out["down_payment_pct"] or out["instalment_plan"] or out["stage_linked"]
                                    or out["bank_loan"] or out["discount_schedule"])
    return out


OFFPLAN_STATUSES = ("under construction", "probably off-plan")
TEXT_JOIN = "\n---\n"  # separates the texts of several adverts of the same property


def is_offplan(terms):
    status = (terms or {}).get("construction_status") or ""
    return any(s in status for s in OFFPLAN_STATUSES)


def terms_for(text, url=""):
    """Terms for one advert text, or for several adverts of the same property joined by
    TEXT_JOIN: each advert is read on its own, then the results are put together. When the
    adverts disagree (e.g. one says ready, another offers a down payment) both are kept,
    as in "ready / probably off-plan"."""
    parts = [p for p in (text or "").split(TEXT_JOIN) if p.strip()]
    if len(parts) <= 1:
        return extract_terms(text, url)
    each = [extract_terms(p, url) for p in parts]
    out = {}
    for k in each[0]:
        vals = [e[k] for e in each if e[k] not in (None, "")]
        if k == "has_payment_terms" or k == "stage_linked":
            out[k] = any(vals) if vals else (False if k == "has_payment_terms" else None)
        elif not vals:
            out[k] = None
        elif isinstance(vals[0], (int, float)) and not isinstance(vals[0], bool):
            out[k] = vals[0]
        else:
            out[k] = " / ".join(dict.fromkeys(str(v) for v in vals))
    return out


# ---------------------------------------------------------------- web address signal
URL_SIGNAL = re.compile(OFFPLAN.pattern + r"|" + KNOWN_DEV.pattern + r"|real[\s-]?estate|realestate|developer|"
                        r"down[\s-]?payment|instal+ment|payment[\s-]?plan|discount|project", I)


def offplan_url_signal(url):
    """True when a listing's web address suggests an off-plan or developer advert
    (used to scrape those first)."""
    slug = re.sub(r"[-_/]+", " ", url.rstrip("/").split("/")[-1])
    return bool(URL_SIGNAL.search(slug))
