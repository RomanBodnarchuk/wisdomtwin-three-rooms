"""Visual edition of the 21 Sep 2026 investor pitch.

Same sentences as the Adobe 12-page deck. Photography and iPhone huddle
screens replace the blank white slides. Emily closes the deck.
"""

from pathlib import Path

from PIL import Image, ImageEnhance
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import Color, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "public" / "images"
VID = ROOT / "public" / "videos"
PLATES = Path("/tmp/deck/plates")
OUT = ROOT / "public" / "WisdomTwin-Visual-Investor-Pitch-2026-09-21.pdf"

W, H = 1920, 1080

pdfmetrics.registerFont(TTFont("Display", "/tmp/fonts/Fraunces.ttf"))
pdfmetrics.registerFont(TTFont("Inter", "/usr/share/fonts/truetype/macos/Inter-Regular.ttf"))
pdfmetrics.registerFont(TTFont("InterMed", "/usr/share/fonts/truetype/macos/Inter-Medium.ttf"))
pdfmetrics.registerFont(TTFont("InterBold", "/usr/share/fonts/truetype/macos/Inter-Bold.ttf"))

CREAM = Color(243 / 255, 239 / 255, 230 / 255)
DIM = Color(184 / 255, 178 / 255, 166 / 255)
GOLD = Color(200 / 255, 164 / 255, 93 / 255)
INK = Color(10 / 255, 14 / 255, 24 / 255)
CARD = Color(16 / 255, 22 / 255, 36 / 255)
LINE = Color(200 / 255, 164 / 255, 93 / 255, alpha=0.35)

VIDEO = "https://wisdomtwin.ai/videos/emily-always-on.mp4"
DEMO = "https://wisdomtwin.ai/demo"
MAIL = "mailto:roman@wisdomtwin.ai"
CAL = "https://calendly.com/romanbodnarchuk/20min"


def build_plates():
    PLATES.mkdir(parents=True, exist_ok=True)
    src = Image.open(IMG / "scene" / "ceo-kitchen-hero.jpg").convert("RGB")
    sw, sh = src.size
    scale = max(W / sw, H / sh)
    src = src.resize((int(sw * scale) + 2, int(sh * scale) + 2), Image.Resampling.LANCZOS)
    nw, nh = src.size
    left = max(0, (nw - W) // 2)
    top = max(0, (nh - H) // 2)
    src = src.crop((left, top, left + W, top + H))
    src = ImageEnhance.Color(src).enhance(0.9)
    src = ImageEnhance.Contrast(src).enhance(1.06)
    scrim = Image.new("L", (W, 1))
    for x in range(W):
        t = x / W
        if t < 0.38:
            a = 0
        else:
            a = int(215 * ((t - 0.38) / 0.62) ** 1.05)
        scrim.putpixel((x, 0), a)
    dark = Image.new("RGB", (W, H), (8, 12, 20))
    cover = Image.composite(dark, src, scrim.resize((W, H)))
    cover.save(PLATES / "cover.jpg", quality=92)

    interior = Image.new("RGB", (W, H), (10, 14, 24))
    interior.save(PLATES / "interior.jpg", quality=90)


def wrap(c, text, font, size, width):
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else f"{cur} {word}"
        if c.stringWidth(trial, font, size) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_lines(c, lines, font, size, x, y, leading, color):
    c.setFillColor(color)
    c.setFont(font, size)
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def footer(c, label):
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.line(80, 64, W - 80, 64)
    c.setFillColor(DIM)
    c.setFont("InterMed", 13)
    c.drawString(80, 36, "WISDOMTWIN.AI")
    c.setFillColor(Color(200 / 255, 164 / 255, 93 / 255, alpha=0.7))
    c.drawString(230, 36, "|")
    c.setFillColor(DIM)
    c.drawString(252, 36, "FINAL INVESTOR PITCH")
    c.setFillColor(Color(200 / 255, 164 / 255, 93 / 255, alpha=0.7))
    c.drawString(460, 36, "|")
    c.setFillColor(DIM)
    c.drawString(482, 36, "21 SEP 2026")
    c.setFillColor(GOLD)
    c.setFont("InterBold", 13)
    c.drawRightString(W - 80, 36, label)


def interior(c):
    c.drawImage(str(PLATES / "interior.jpg"), 0, 0, W, H)
    c.setFillColor(GOLD)
    c.rect(0, H - 6, W, 6, fill=1, stroke=0)


def eyebrow(c, text, x, y):
    c.setFillColor(GOLD)
    c.setFont("InterBold", 14)
    c.drawString(x, y, text)
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.2)
    c.line(x, y - 10, x + 72, y - 10)


def phone(c, path, x, y, h):
    iw, ih = Image.open(path).size
    w = h * iw / ih
    pad = 12
    c.setFillColor(Color(0.05, 0.06, 0.08))
    c.roundRect(x - pad, y - pad, w + pad * 2, h + pad * 2, 42, fill=1, stroke=0)
    c.saveState()
    p = c.beginPath()
    p.roundRect(x, y, w, h, 32)
    c.clipPath(p, stroke=0, fill=0)
    c.drawImage(str(path), x, y, w, h, preserveAspectRatio=True, mask="auto")
    c.restoreState()
    c.setStrokeColor(Color(200 / 255, 164 / 255, 93 / 255, alpha=0.45))
    c.setLineWidth(1.4)
    c.roundRect(x - pad, y - pad, w + pad * 2, h + pad * 2, 42, fill=0, stroke=1)
    return w


def card(c, x, y, w, h):
    c.setFillColor(CARD)
    c.setStrokeColor(LINE)
    c.setLineWidth(1)
    c.roundRect(x, y, w, h, 18, fill=1, stroke=1)


def slide_cover(c):
    c.drawImage(str(PLATES / "cover.jpg"), 0, 0, W, H)
    c.setFillColor(GOLD)
    c.rect(0, H - 6, W, 6, fill=1, stroke=0)
    x = 980
    eyebrow(c, "AI JUDGMENT TWINS FOR REGULATED ENTERPRISES", x, 860)
    y = draw_lines(
        c,
        ["Your enterprise runs", "168 hours a week."],
        "Display",
        64,
        x,
        760,
        76,
        CREAM,
    )
    draw_lines(c, ["Its judgment runs 40."], "Display", 64, x, y - 8, 76, GOLD)
    c.setFillColor(DIM)
    c.setFont("Inter", 20)
    c.drawString(x, 430, "WisdomTwin.ai   ·   Investor Pitch   ·   September 21, 2026")
    c.setFillColor(CREAM)
    c.setFont("InterMed", 22)
    c.drawString(x, 388, "USD $1,000,000 pre-seed  ·  post-money SAFE")
    footer(c, "01")


def slide_problem(c):
    interior(c)
    eyebrow(c, "THE BOTTLENECK", 88, 940)
    y = draw_lines(
        c,
        ["The decision is never", "the slow part.", "The meeting is."],
        "Display",
        58,
        88,
        840,
        70,
        CREAM,
    )
    y = draw_lines(
        c,
        wrap(
            c,
            "Evidence can be ready while authorized judgment is still trapped on the calendar.",
            "Inter",
            24,
            820,
        ),
        "Inter",
        24,
        88,
        y - 28,
        34,
        DIM,
    )
    draw_lines(
        c,
        wrap(
            c,
            "The bottleneck is judgment latency, not access to information.",
            "InterMed",
            24,
            820,
        ),
        "InterMed",
        24,
        88,
        y - 18,
        34,
        CREAM,
    )
    phone(c, IMG / "buzz" / "start-mobile.png", 1288, 120, 820)
    footer(c, "02")


def slide_category(c):
    interior(c)
    eyebrow(c, "CATEGORY", 88, 940)
    draw_lines(
        c,
        ["USD $70M went into AI twins", "in eleven months."],
        "Display",
        56,
        88,
        830,
        68,
        CREAM,
    )
    c.setFillColor(GOLD)
    c.setFont("Display", 40)
    c.drawString(88, 660, "We built the one for the regulated decision.")
    names = [
        ("Hello Haven", "USD $15M"),
        ("Twin1", "USD $20M"),
        ("Viven", "USD $35M"),
    ]
    x = 88
    for name, amount in names:
        card(c, x, 360, 520, 220)
        c.setFillColor(DIM)
        c.setFont("InterMed", 18)
        c.drawString(x + 36, 500, name)
        c.setFillColor(CREAM)
        c.setFont("Display", 48)
        c.drawString(x + 36, 420, amount)
        x += 560
    c.setFillColor(DIM)
    c.setFont("Inter", 20)
    c.drawString(
        88,
        280,
        "External financing signals category interest. It is not WisdomTwin traction.",
    )
    footer(c, "03")


def slide_boundary(c):
    interior(c)
    eyebrow(c, "CUSTOMER-APPROVED BOUNDARY", 88, 940)
    y = draw_lines(
        c,
        ["The judgment never", "leaves the building."],
        "Display",
        56,
        88,
        830,
        68,
        CREAM,
    )
    c.setFillColor(DIM)
    c.setFont("Inter", 22)
    c.drawString(88, y - 16, "Designed for the customer-approved boundary.")
    steps = [
        "Approved evidence",
        "Role-specific judgment",
        "Policy controls",
        "Named human release",
    ]
    x = 88
    for i, step in enumerate(steps):
        card(c, x, 430, 250, 120)
        c.setFillColor(GOLD)
        c.setFont("InterBold", 13)
        c.drawString(x + 22, 510, f"0{i + 1}")
        c.setFillColor(CREAM)
        c.setFont("InterMed", 16)
        for j, line in enumerate(wrap(c, step, "InterMed", 16, 200)):
            c.drawString(x + 22, 470 - j * 22, line)
        if i < 3:
            c.setFillColor(GOLD)
            c.setFont("Inter", 22)
            c.drawString(x + 258, 478, "→")
        x += 292
    c.setFillColor(DIM)
    c.setFont("Inter", 20)
    note = wrap(
        c,
        "Private deployment remains to be validated configuration by configuration.",
        "Inter",
        20,
        980,
    )
    draw_lines(c, note, "Inter", 20, 88, 340, 28, DIM)
    phone(c, IMG / "buzz" / "evidence-mobile.png", 1360, 150, 700)
    footer(c, "04")


def slide_product(c):
    interior(c)
    eyebrow(c, "ONE-PRESS HUDDLE", 88, 940)
    y = draw_lines(
        c,
        ["Ask the role that is", "not in the room."],
        "Display",
        54,
        88,
        830,
        66,
        CREAM,
    )
    c.setFillColor(GOLD)
    c.setFont("Display", 32)
    c.drawString(88, y - 10, "Get the call it would make, with receipts.")
    rows = [
        ("INGEST", "Approved evidence and precedent"),
        ("TWIN", "Role-specific perspective, limits and escalation"),
        ("OPERATE", "Trust Layer + named human authority"),
    ]
    yy = 470
    for label, body in rows:
        c.setFillColor(GOLD)
        c.setFont("InterBold", 16)
        c.drawString(88, yy, label)
        c.setFillColor(CREAM)
        c.setFont("Inter", 22)
        c.drawString(250, yy - 2, body)
        yy -= 64
    c.setFillColor(DIM)
    c.setFont("Inter", 20)
    c.drawString(88, 250, "One-Press Huddle convenes the roles while the question is still live.")
    phone(c, IMG / "buzz" / "huddle-mobile.png", 1320, 130, 800)
    footer(c, "05")


def slide_wedge(c):
    interior(c)
    eyebrow(c, "FIRST WEDGE", 88, 940)
    draw_lines(
        c,
        ["We are not selling a platform.", "We are selling one decision."],
        "Display",
        48,
        88,
        840,
        60,
        CREAM,
    )
    c.setFillColor(GOLD)
    c.setFont("InterBold", 16)
    c.drawString(88, 680, "AUDIT EVIDENCE REVIEW")
    blocks = [
        ("Input", "access export + HR status + approvals + policy"),
        ("Output", "source-linked recommendation + evidence gaps + escalation"),
        ("Owner", "named human retains consequential approval"),
    ]
    y = 560
    for title, body in blocks:
        card(c, 88, y - 70, 1100, 130)
        c.setFillColor(GOLD)
        c.setFont("InterBold", 14)
        c.drawString(120, y + 20, title.upper())
        c.setFillColor(CREAM)
        c.setFont("Inter", 22)
        c.drawString(120, y - 24, body)
        y -= 160
    phone(c, IMG / "buzz" / "plan-mobile.png", 1320, 150, 760)
    footer(c, "06")


def slide_proof(c):
    interior(c)
    eyebrow(c, "WHAT CAN BE SHOWN", 88, 960)
    draw_lines(
        c,
        ["Five built demonstrations prove the product can be shown."],
        "Display",
        40,
        88,
        880,
        50,
        CREAM,
    )
    c.setFillColor(GOLD)
    c.setFont("Display", 26)
    c.drawString(88, 800, "Paid customer validation is the next proof.")
    c.setFillColor(DIM)
    c.setFont("Inter", 20)
    c.drawString(88, 750, "Five founder-built synthetic demonstrations.")
    c.drawString(88, 716, "Pre-revenue. No production deployment or paying customer is claimed.")
    lines = wrap(
        c,
        "Next proof: controlled, buyer-defined validation against time, quality, escalation and audit replay.",
        "Inter",
        20,
        1700,
    )
    draw_lines(c, lines, "Inter", 20, 88, 676, 28, CREAM)
    shots = [
        (IMG / "buzz" / "start-mobile.png", "Start"),
        (IMG / "buzz" / "huddle-mobile.png", "Huddle"),
        (IMG / "buzz" / "evidence-mobile.png", "Evidence"),
        (IMG / "buzz" / "plan-mobile.png", "Decision"),
    ]
    phone_h = 420
    phone_w = phone_h * 430 / 932
    gap = 56
    row_w = 4 * phone_w + 3 * gap
    x = (W - row_w) / 2
    for path, label in shots:
        w = phone(c, path, x, 150, phone_h)
        c.setFillColor(DIM)
        c.setFont("InterMed", 14)
        c.drawCentredString(x + w / 2, 118, label)
        x += w + gap
    footer(c, "07")


def slide_ladder(c):
    interior(c)
    eyebrow(c, "PROPOSED COMMERCIAL LADDER", 88, 940)
    draw_lines(
        c,
        ["The unit is the role,", "not the token."],
        "Display",
        56,
        88,
        830,
        68,
        CREAM,
    )
    rows = [
        ("Concept Validation", "USD $50K", "2 months", "10 roles"),
        ("Structured Pilot", "USD $250K", "6 months", "50 roles"),
        ("Commercial", "USD $500K+", "annual", "500 roles"),
    ]
    y = 560
    for name, price, term, roles in rows:
        card(c, 88, y, 1744, 120)
        c.setFillColor(GOLD)
        c.setFont("InterBold", 16)
        c.drawString(124, y + 72, name.upper())
        c.setFillColor(CREAM)
        c.setFont("Display", 32)
        c.drawString(124, y + 28, price)
        c.setFillColor(DIM)
        c.setFont("Inter", 22)
        c.drawRightString(1780, y + 48, f"{term}   ·   {roles}")
        y -= 146
    c.setFillColor(DIM)
    c.setFont("Inter", 18)
    c.drawString(88, 110, "Pricing and willingness to pay remain to be validated.")
    footer(c, "08")


def slide_moat(c):
    interior(c)
    eyebrow(c, "COMPOUNDING CONTEXT", 88, 940)
    draw_lines(
        c,
        ["Rip us out and you lose", "your own documented judgment."],
        "Display",
        52,
        88,
        820,
        64,
        CREAM,
    )
    c.setFillColor(DIM)
    c.setFont("Inter", 22)
    c.drawString(88, 640, "The compounding asset is customer-specific context:")
    assets = [
        "Approved evidence",
        "Role perspective",
        "Policy versions",
        "Precedent",
        "Reviewer actions",
    ]
    x = 88
    for asset in assets:
        tw = 300
        card(c, x, 430, tw, 140)
        c.setFillColor(CREAM)
        c.setFont("InterMed", 20)
        for i, line in enumerate(wrap(c, asset, "InterMed", 20, tw - 48)):
            c.drawString(x + 28, 500 - i * 28, line)
        x += 330
    lines = wrap(
        c,
        "Defensibility must be earned through deployment, workflow integration and accumulated governed context.",
        "Inter",
        22,
        1600,
    )
    draw_lines(c, lines, "Inter", 22, 88, 340, 32, DIM)
    footer(c, "09")


def slide_team(c):
    interior(c)
    eyebrow(c, "THE ROOM", 88, 940)
    draw_lines(
        c,
        ["Twenty-eight years inside", "the rooms where these", "decisions stall."],
        "Display",
        48,
        88,
        830,
        58,
        CREAM,
    )
    card(c, 88, 250, 900, 280)
    c.setFillColor(GOLD)
    c.setFont("InterBold", 14)
    c.drawString(120, 470, "ROMAN BODNARCHUK")
    c.setFillColor(CREAM)
    c.setFont("InterMed", 20)
    c.drawString(120, 434, "Co-Founder & CEO")
    c.setFillColor(DIM)
    c.setFont("Inter", 18)
    bio = wrap(
        c,
        "Founded N5R in 1998 · operated across 15 countries · built the five current demonstrations",
        "Inter",
        18,
        820,
    )
    draw_lines(c, bio, "Inter", 18, 120, 390, 26, DIM)

    card(c, 1020, 250, 820, 280)
    c.setFillColor(GOLD)
    c.setFont("InterBold", 14)
    c.drawString(1052, 470, "STELLA CABRERA")
    c.setFillColor(CREAM)
    c.setFont("InterMed", 20)
    c.drawString(1052, 434, "Co-Founder, Governance")
    c.setFillColor(DIM)
    c.setFont("Inter", 18)
    bio = wrap(
        c,
        "20+ years across financial-services risk, data and compliance",
        "Inter",
        18,
        740,
    )
    draw_lines(c, bio, "Inter", 18, 1052, 390, 26, DIM)
    footer(c, "10")


def slide_ask(c):
    interior(c)
    eyebrow(c, "THE ROUND", 88, 940)
    draw_lines(
        c,
        ["USD $1,000,000 to turn five", "demonstrations into the first", "paid regulated pilots."],
        "Display",
        52,
        88,
        820,
        64,
        CREAM,
    )
    c.setFillColor(GOLD)
    c.setFont("InterBold", 18)
    c.drawString(88, 560, "POST-MONEY SAFE")
    lines = wrap(
        c,
        "12-month objective: validate one repeatable regulated decision, deploy with buyers, measure the proof, then expand.",
        "Inter",
        24,
        1500,
    )
    draw_lines(c, lines, "Inter", 24, 88, 510, 34, DIM)

    c.setFillColor(CREAM)
    c.setFont("InterMed", 22)
    parts = [
        ("wisdomtwin.ai/demo", DEMO),
        ("roman@wisdomtwin.ai", MAIL),
        ("20-minute discussion", CAL),
    ]
    x = 88
    y = 300
    for i, (label, url) in enumerate(parts):
        c.setFillColor(CREAM)
        c.setFont("InterMed", 22)
        c.drawString(x, y, label)
        lw = c.stringWidth(label, "InterMed", 22)
        c.setStrokeColor(GOLD)
        c.setLineWidth(1)
        c.line(x, y - 4, x + lw, y - 4)
        c.linkURL(url, (x, y - 8, x + lw, y + 26), relative=0, thickness=0)
        x += lw + 28
        if i < 2:
            c.setFillColor(GOLD)
            c.setFont("Inter", 22)
            c.drawString(x - 18, y, "·")
    footer(c, "11")


def slide_system(c):
    interior(c)
    eyebrow(c, "CUSTOMER-APPROVED BOUNDARY  ·  NO OUTBOUND NETWORK", 80, 1000)
    draw_lines(
        c,
        ["The model proposes. Code checks. A named human releases."],
        "Display",
        32,
        80,
        940,
        40,
        CREAM,
    )
    cols = [
        ("01  INGEST", "Approved evidence and precedent"),
        ("02  TWIN", "Role-specific perspective, limits and escalation"),
        ("03  OPERATE", "Trust Layer + named human authority"),
    ]
    x = 80
    for title, body in cols:
        card(c, x, 800, 560, 100)
        c.setFillColor(GOLD)
        c.setFont("InterBold", 14)
        c.drawString(x + 22, 860, title)
        c.setFillColor(CREAM)
        c.setFont("Inter", 15)
        c.drawString(x + 22, 828, body)
        x += 586
    pairs = [
        ("Customer sources", "File share or DMS export, email export, upload"),
        ("Ingest pipeline", "Keeps permissions, sources and policy versions"),
        ("Index and retrieval", "Pilot: permission- and date-filtered, cited"),
        ("Local model server", "Customer-approved model on customer hardware"),
        ("Role-specific Wisdom Twins", "One per role: judgment log, policies, limits"),
        ("One-Press Huddle", "Convenes the roles, shows disagreement"),
        ("Trust Layer", "Policy checks, authority limits, escalation, audit log"),
        ("Named human approver", "Approve, decline or return. Identity from SSO."),
        ("Decision record", "Evidence, checks, exceptions, approver. Hash-chained."),
    ]
    y = 750
    for i, (name, detail) in enumerate(pairs):
        col = i // 5
        row = i % 5
        x = 80 + col * 900
        yy = y - row * 78
        c.setFillColor(GOLD)
        c.circle(x + 8, yy + 6, 4, fill=1, stroke=0)
        c.setFillColor(CREAM)
        c.setFont("InterMed", 16)
        c.drawString(x + 24, yy, name)
        c.setFillColor(DIM)
        c.setFont("Inter", 14)
        c.drawString(x + 24, yy - 22, detail)
    c.setFillColor(DIM)
    c.setFont("Inter", 13)
    c.drawString(80, 250, "One question in (SSO)")
    lines = wrap(
        c,
        "Runs today in prototype v0.1 on one Mac Studio. Zero non-loopback connections during a query, verified with lsof.",
        "Inter",
        14,
        1760,
    )
    y = draw_lines(c, lines, "Inter", 14, 80, 224, 20, DIM)
    lines = wrap(
        c,
        "Pilot build. Air-gapped operation is a target to validate in the pilot, not a certified claim. No certification held.",
        "Inter",
        14,
        1760,
    )
    draw_lines(c, lines, "Inter", 14, 80, y - 6, 20, DIM)
    footer(c, "A1")


def slide_emily(c):
    interior(c)
    eyebrow(c, "SYNTHETIC DEMONSTRATION", 88, 940)
    draw_lines(c, ["Emily, always on."], "Display", 60, 88, 840, 70, CREAM)
    lines = [
        "She answers on iMessage, WhatsApp, Telegram,",
        "Signal, Slack, email, and Zoom.",
    ]
    y = draw_lines(c, lines, "Inter", 24, 88, 740, 34, DIM)
    c.setFillColor(CREAM)
    c.setFont("Display", 32)
    c.drawString(88, y - 24, "24 hours. 7 days.")
    c.setFillColor(DIM)
    c.setFont("Inter", 16)
    c.drawString(88, 520, "Synthetic demonstration. Fictional names and figures.")

    c.setFillColor(CREAM)
    c.setFont("InterMed", 22)
    play = "Play the 43-second film"
    book = "Book a 20-minute demo"
    c.drawString(88, 430, play)
    c.drawString(88, 380, book)
    pw = c.stringWidth(play, "InterMed", 22)
    bw = c.stringWidth(book, "InterMed", 22)
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.2)
    c.line(88, 424, 88 + pw, 424)
    c.line(88, 374, 88 + bw, 374)
    c.linkURL(VIDEO, (88, 418, 88 + pw, 456), relative=0, thickness=0)
    c.linkURL(CAL, (88, 368, 88 + bw, 406), relative=0, thickness=0)

    tx, ty, tw, th = 980, 220, 820, 461
    c.drawImage(str(VID / "emily-always-on-thumb.jpg"), tx, ty, tw, th, preserveAspectRatio=True, anchor="c", mask="auto")
    c.setStrokeColor(LINE)
    c.setLineWidth(1.2)
    c.rect(tx, ty, tw, th, fill=0, stroke=1)
    c.linkURL(VIDEO, (tx, ty, tx + tw, ty + th), relative=0, thickness=0)
    c.setFillColor(Color(0.05, 0.05, 0.06, alpha=0.72))
    c.circle(tx + tw / 2, ty + th / 2, 36, fill=1, stroke=0)
    c.setFillColor(white)
    path = c.beginPath()
    cx, cy = tx + tw / 2 + 4, ty + th / 2
    path.moveTo(cx - 12, cy - 16)
    path.lineTo(cx - 12, cy + 16)
    path.lineTo(cx + 18, cy)
    path.close()
    c.drawPath(path, fill=1, stroke=0)
    c.setFillColor(DIM)
    c.setFont("Inter", 14)
    c.drawString(tx, ty - 28, "Click the film to play.")
    footer(c, "13")


def main():
    build_plates()
    tmp = Path("/tmp/deck/visual-pitch.pdf")
    c = canvas.Canvas(str(tmp), pagesize=(W, H))
    c.setTitle("WisdomTwin Final Investor Pitch — 21 Sep 2026")
    c.setAuthor("WisdomTwin")
    for slide in (
        slide_cover,
        slide_problem,
        slide_category,
        slide_boundary,
        slide_product,
        slide_wedge,
        slide_proof,
        slide_ladder,
        slide_moat,
        slide_team,
        slide_ask,
        slide_system,
        slide_emily,
    ):
        slide(c)
        c.showPage()
    c.save()

    reader = PdfReader(str(tmp))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.add_metadata(
        {
            "/Title": "WisdomTwin Final Investor Pitch — 21 Sep 2026",
            "/Author": "WisdomTwin",
            "/Subject": "Visual edition. Same copy as the 21 Sep 2026 pitch. Emily closes the deck.",
        }
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("wb") as f:
        writer.write(f)
    print(f"{len(reader.pages)} pages  {OUT}  {OUT.stat().st_size}")


if __name__ == "__main__":
    main()
