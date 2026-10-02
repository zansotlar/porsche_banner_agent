"""
Porsche Banner Agent - jedro logike
Zamenja veljavnost akcije v small print besedilu na Porsche Meta bannerjih.
Avtomatsko zazna vrstico z datumi (OCR), jo teksturno "izbriše" (inpainting)
in na novo izriše s posodobljenim datumom, centrirano med sosednjima
vrsticama, v ujemajoči velikosti pisave.
"""
import sys
import re
import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

OLD_DATE = "30.9.2026"
NEW_DATE = "31.12.2026"


def _scan_for_date_token(data, old_digits):
    n = len(data['text'])
    best = None
    for i in range(n):
        txt = data['text'][i].strip()
        if not txt:
            continue
        digits = re.sub(r"[^0-9]", "", txt)
        if len(digits) >= 4 and "2026" in digits:
            score = 2 if digits == old_digits else 1
            if best is None or score > best[0]:
                best = (score, data['top'][i], data['height'][i], data['left'][i], data['width'][i])
    return best


def _scan_for_word(data, candidates):
    n = len(data['text'])
    for i in range(n):
        txt = data['text'][i].strip().lower()
        txt_clean = re.sub(r"[^\w]", "", txt, flags=re.UNICODE)
        for cand in candidates:
            if len(txt_clean) >= 4 and (cand in txt_clean or txt_clean in cand):
                return data['top'][i], data['height'][i], data['left'][i], data['width'][i]
    return None


def _run_ocr_stages(img_bgr):
    H, W = img_bgr.shape[:2]
    stages = []

    data1 = pytesseract.image_to_data(img_bgr, lang='slv+eng', output_type=pytesseract.Output.DICT)
    stages.append((data1, 0))

    crop_y0 = int(H * 0.70)
    crop = img_bgr[crop_y0:H, 0:W]
    data2 = pytesseract.image_to_data(crop, lang='slv+eng', output_type=pytesseract.Output.DICT, config='--psm 6')
    stages.append((data2, crop_y0))

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    data3 = pytesseract.image_to_data(th, lang='slv+eng', output_type=pytesseract.Output.DICT, config='--psm 6')
    stages.append((data3, crop_y0))

    return stages


def find_layout(img_bgr, old_date_str):
    old_digits = re.sub(r"[^0-9]", "", old_date_str)
    best = None

    for data, offset in _run_ocr_stages(img_bgr):
        date_tok = _scan_for_date_token(data, old_digits)
        line1_tok = _scan_for_word(data, ["popuste", "ugodnosti"])
        line3_tok = _scan_for_word(data, ["vozil", "omejennabor", "omejen"])

        def offset_tok(tok, is_date):
            if tok is None:
                return None
            if is_date:
                _, top, height, left, width = tok
            else:
                top, height, left, width = tok
            return (top + offset, height, left, width)

        date_o = offset_tok(date_tok, True)
        line1_o = offset_tok(line1_tok, False)
        line3_o = offset_tok(line3_tok, False)

        score = sum(x is not None for x in [date_o, line1_o, line3_o])
        if date_o is not None and (best is None or score > best[0]):
            best = (score, date_o, line1_o, line3_o)

    if best is None:
        return None
    _, date_o, line1_o, line3_o = best
    return date_o, line1_o, line3_o


def fix_image(in_path, out_path, old_date=OLD_DATE, new_date=NEW_DATE, debug=False):
    img_bgr = cv2.imread(in_path)
    if img_bgr is None:
        raise RuntimeError(f"Ne morem odpreti slike: {in_path}")
    H, W = img_bgr.shape[:2]

    layout = find_layout(img_bgr, old_date)
    if layout is None:
        return False, "Datum ni bil najden (banner morda nima small printa)."
    date_tok, line1_tok, line3_tok = layout
    d_top, d_height, d_left, d_width = date_tok

    margin_x = int(W * 0.06)
    rx0 = margin_x
    rx1 = W - margin_x

    if line1_tok is not None and line3_tok is not None:
        l1_top, l1_height, _, _ = line1_tok
        l3_top, _, _, _ = line3_tok
        line1_bottom = l1_top + l1_height
        line3_top = l3_top
        safety_margin = max(3, int(l1_height * 0.15))
        ry0 = min(line1_bottom + safety_margin, d_top)
        ry1 = max(line3_top - safety_margin, d_top + d_height)
        ry0 = min(ry0, d_top - 4)
        ry1 = max(ry1, d_top + d_height + 4)
        center_y = (line1_bottom + line3_top) / 2.0
    else:
        pad_y_top = int(d_height * 0.6)
        pad_y_bot = int(d_height * 0.8)
        ry0 = max(0, d_top - pad_y_top)
        ry1 = min(H, d_top + d_height + pad_y_bot)
        center_y = (d_top + d_top + d_height) / 2.0

    ry0 = max(0, int(ry0))
    ry1 = min(H, int(ry1))

    roi = img_bgr[ry0:ry1, rx0:rx1]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 165, 255, cv2.THRESH_BINARY)
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)

    inpainted = cv2.inpaint(roi, mask, 5, cv2.INPAINT_TELEA)
    img_bgr2 = img_bgr.copy()
    img_bgr2[ry0:ry1, rx0:rx1] = inpainted

    template_line = f"Ponudba velja za pogodbe podpisane od 1.8.2026 do {old_date}."
    new_line = template_line.replace(old_date, new_date)

    img_pil = Image.fromarray(cv2.cvtColor(img_bgr2, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)

    FONT_SIZE_BY_WIDTH = {1200: 28, 1080: 26}
    best_size = FONT_SIZE_BY_WIDTH.get(W, max(10, round(W * 28 / 1200)))
    try:
        font = ImageFont.truetype(FONT_PATH, best_size)
    except IOError:
        font = ImageFont.load_default()

    draw.text((center_x, center_y), new_line, font=font, fill=(255, 255, 255), anchor="mm")

    img_pil.save(out_path)
    if debug:
        print(f"date_tok top={d_top} h={d_height}, font size used: {best_size}, center_y={center_y}")
    return True, "OK"


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uporaba: python3 fix_smallprint.py <vhodna_slika> <izhodna_slika> [stari_datum] [novi_datum]")
        sys.exit(1)
    in_path = sys.argv[1]
    out_path = sys.argv[2]
    old_d = sys.argv[3] if len(sys.argv) > 3 else OLD_DATE
    new_d = sys.argv[4] if len(sys.argv) > 4 else NEW_DATE
    ok, msg = fix_image(in_path, out_path, old_d, new_d, debug=True)
    print(msg)
