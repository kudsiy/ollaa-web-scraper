"""
Hide contact details in advert text before it is stored anywhere (owner's rule, 13 Nov 2026:
never store an unmasked phone number). Phone numbers, e-mail addresses, chat handles and
chat links are replaced by "<contact>". Prices are left alone: a number written with
thousands commas (35,000,000) is never treated as a phone number.
"""
import re

MASK = "<contact>"
_SEP = r"[\s\-.()/]*"

_PATTERNS = [
    # links to chat apps and phone links
    re.compile(r"(?:https?://)?(?:www\.)?(?:wa\.me|api\.whatsapp\.com|chat\.whatsapp\.com|t\.me|viber\.click)/\S*", re.I),
    re.compile(r"\b(?:tel|callto|sms|whatsapp|viber):[^\s\"'<>]*", re.I),
    # e-mail addresses
    re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"),
    # a full number written without spaces (09xxxxxxxx, 2519xxxxxxxx), even when commas
    # separate several numbers ("0911…,0922…"): thousands groups have 3 digits, so a run of
    # 10+ digits next to a comma is never part of a price
    re.compile(r"(?<!\d)(?:\+?251|0)[1-9]\d{8}(?!\d)"),
    # Ethiopian numbers: +251 / 251 / 0 followed by 9 digits (mobile 9xx / 7xx, landline 1x ...)
    re.compile(r"(?<![\w,])(?:\+|00)?251" + _SEP + r"\(?0?\)?" + _SEP + r"[1-9](?:" + _SEP + r"\d){8}(?![\d,])"),
    re.compile(r"(?<![\w,])0" + _SEP + r"[1-9](?:" + _SEP + r"\d){8}(?![\d,])"),
    # a mobile number written without the leading 0: 9xx xxx xxx / 7xx xxx xxx
    re.compile(r"(?<![\w,])[79]\d{2}" + r"[\s\-.]?\d{3}[\s\-.]?\d{3}(?![\d,])"),
    # any other run of 9+ digits (with spaces or dashes, but no thousands commas)
    re.compile(r"(?<![\w,])\+?\d(?:[\s\-.]?\d){8,}(?![\d,])"),
    # chat handles such as @agent_name (an e-mail is already masked above); page-code words
    # such as "@context" in data blocks or "@media" in styles are not handles
    re.compile(r"(?<![\w.\"'\\])@(?!(?:context|graph|type|id|value|list|language|vocab|base|media|import|"
               r"font-face|keyframes|supports|charset|page|namespace|layer|container)\b)[A-Za-z]\w{3,}"),
]


def mask_contacts(text):
    """Return text with every phone number, e-mail, chat link and handle replaced."""
    if not text:
        return text or ""
    out = str(text)
    for rx in _PATTERNS:
        out = rx.sub(MASK, out)
    return out


def has_contact(text):
    """True if text still contains something that looks like a phone number or e-mail."""
    return mask_contacts(text) != (text or "")
