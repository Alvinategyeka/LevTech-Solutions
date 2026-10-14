from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import shutil, zipfile, os, textwrap, re, json

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'source_artwork'
PAGES = ROOT / 'pages'
ROOT.mkdir(parents=True, exist_ok=True)
SRC.mkdir(exist_ok=True)
PAGES.mkdir(exist_ok=True)

# Copy the selected original/generated artwork into a self-contained source bundle.
# Rebuilds use only files packaged alongside this script.
REQUIRED_ASSETS = [
    'page-01-cover.png', 'page-02-company-profile.png', 'page-03-our-solutions.png',
    'page-04-product-categories.png', 'page-05-smart-home-automation.png',
    'page-06-smart-home-control-systems.png', 'page-07-smart-locks.png',
    'page-08-smart-switches.png', 'page-09-video-intercom.png',
    'page-10-cctv-surveillance.png', 'page-11-solar-4g-surveillance.png',
    'page-12-recording-solutions.png', 'page-13-access-control-attendance.png',
    'page-14-gate-automation.png', 'page-15-fire-alarms.png',
    'page-16-intruder-alarms.png', 'page-17-electric-fencing.png',
    'page-18-smart-doorbells.png', 'page-19-smart-sensors.png',
    'page-21-smart-lighting.png', 'page-25-smart-climate-control.png',
    'page-27-backup-power.png', 'page-28-solar-street-lights.png',
    'page-33-smart-home-devices.png', 'page-34-smart-speakers.png',
    'page-36-smart-plugs.png', 'page-37-smart-home-hubs-gateways.png',
    'page-37-smart-curtains-reference.jpg', 'page-39-smart-film-reference.jpg',
    'page-40-intrusion-alarms-smart-security.png', 'page-44-complete-solutions.png',
    'gps-page-source.png'
]
missing = [name for name in REQUIRED_ASSETS if not (SRC / name).is_file() or (SRC / name).stat().st_size == 0]
if missing:
    raise FileNotFoundError('Missing catalogue source artwork: ' + ', '.join(missing))

# Fonts available on the build machine. Package includes standard dependencies in README.
FONT_DIR = Path('/usr/share/fonts/truetype/lato')
FONT_REG = FONT_DIR/'Lato-Regular.ttf'
FONT_MED = FONT_DIR/'Lato-Medium.ttf'
FONT_SEMI = FONT_DIR/'Lato-Semibold.ttf'
FONT_BOLD = FONT_DIR/'Lato-Bold.ttf'
FONT_HEAVY = FONT_DIR/'Lato-Heavy.ttf'
if not FONT_BOLD.exists():
    FONT_DIR = Path('/usr/share/fonts/truetype/dejavu')
    FONT_REG = FONT_DIR/'DejaVuSans.ttf'; FONT_MED = FONT_REG; FONT_SEMI = FONT_DIR/'DejaVuSans-Bold.ttf'; FONT_BOLD = FONT_SEMI; FONT_HEAVY = FONT_SEMI

def font(path, size):
    try: return ImageFont.truetype(str(path), size=size)
    except Exception: return ImageFont.load_default()

BLUE = (20, 121, 248)
NAVY = (8, 30, 58)
INK = (31, 58, 91)
MID = (102, 122, 146)
WHITE = (255,255,255)

# Use CV inpaint on the cover year's cyan characters when available, to avoid a visible box.
def refresh_cover_year(im):
    im = im.convert('RGB')
    try:
        import cv2, numpy as np
        arr = np.array(im)
        # Locate only cyan-blue pixels inside the year line; don't affect the Product Catalogue label above.
        roi = arr[892:932, 60:330]
        mask = ((roi[:,:,2] > 150) & (roi[:,:,1] > 75) & (roi[:,:,0] < 120)).astype('uint8') * 255
        if mask.any():
            kernel = np.ones((3,3), np.uint8)
            mask = cv2.dilate(mask, kernel, iterations=1)
            full = np.zeros(arr.shape[:2], dtype='uint8')
            full[892:932, 60:330] = mask
            arr = cv2.inpaint(arr, full, 4, cv2.INPAINT_TELEA)
            im = Image.fromarray(arr)
    except Exception:
        # Fallback uses a sampled dark tone from the same cover area if OpenCV is unavailable.
        draw = ImageDraw.Draw(im)
        draw.rectangle((70, 892, 330, 930), fill=(7, 28, 54))
    draw = ImageDraw.Draw(im)
    draw.text((72, 891), '2026 EDITION', font=font(FONT_HEAVY, 29), fill=(35, 176, 255), stroke_width=0)
    return im

def add_standard_footer_and_number(im, number, update_number=True):
    im = im.convert('RGB')
    w,h = im.size
    # Replace the complete legacy footer (some source pages still carried 2024/2025
    # and a source-page number) instead of drawing over only its bottom few pixels.
    fy = max(0, h-62)
    d = ImageDraw.Draw(im)
    d.rectangle((0, fy, w, h), fill=WHITE)
    d.line((42, fy+2, w-42, fy+2), fill=(221,231,242), width=2)
    brand_f = font(FONT_BOLD, 15); tagline_f = font(FONT_REG, 14)
    brand_label = 'LEVTECH INTEGRATED SYSTEMS'
    d.text((45, fy+19), brand_label, font=brand_f, fill=(20,47,84))
    tagline_x = int(45 + d.textlength(brand_label, font=brand_f) + 20)
    d.text((tagline_x, fy+20), 'SMART. SECURE. RELIABLE.', font=tagline_f, fill=(97,119,145))
    # A cyan tick anchors the page number.
    d.line((w-105, fy+10, w-105, h-7), fill=(39,163,247), width=3)
    d.text((w-89, fy+15), f'{number:02d}', font=font(FONT_BOLD, 19), fill=(17,46,82))
    # Cover a little beyond the original page-number label: otherwise single-digit
    # remnants such as the old '4' can remain beside the new folio.
    d.rectangle((25, 0, 116, 78), fill=WHITE)
    d.text((39, 5), f'{number:02d}', font=font(FONT_HEAVY, 37), fill=(23,77,234))
    d.rectangle((39, 51, 82, 56), fill=(42,174,251))
    return im

def process_new_style_page(im, number, section=''):
    # Pages 33 and 34 use a more panoramic hero/product-grid format. Keep the
    # full artwork visible, but clean the old source folio before adding the
    # curated catalogue number.
    im = im.convert('RGB')
    w,h=im.size
    d=ImageDraw.Draw(im)
    # Clear the original long section label and rebuild a concise, legible header.
    d.rectangle((w-740, 0, w, 44), fill=WHITE)
    d.line((w-88, 10, w-88, 33), fill=(39,163,247), width=2)
    short_label = section.upper().replace(' & ', ' + ')
    d.text((w-104, 15), short_label, font=font(FONT_BOLD, 12), fill=(46,68,93), anchor='ra')
    d.text((w-73, 7), f'{number:02d}', font=font(FONT_BOLD, 25), fill=(12,34,61))
    # Fully replace legacy lower folio/2024-25 footer.
    fy=h-36
    d.rectangle((0, fy, w, h), fill=WHITE)
    d.line((34, fy+1, w-34, fy+1), fill=(219,230,241), width=2)
    d.text((38, fy+10), 'LEVTECH INTEGRATED SYSTEMS', font=font(FONT_BOLD, 13), fill=(20,47,84))
    d.text((260, fy+10), 'SMART. SECURE. RELIABLE.', font=font(FONT_REG, 12), fill=(99,119,145))
    d.line((w-92, fy+6, w-92, h-4), fill=(39,163,247), width=3)
    d.text((w-77, fy+6), f'{number:02d}', font=font(FONT_BOLD, 16), fill=(17,46,82))
    return im

def process_gps_page(im):
    im=im.convert('RGB'); w,h=im.size; d=ImageDraw.Draw(im)
    # Re-label the numbered section to match the curated catalogue sequence (page 8).
    d.rectangle((58, 199, 540, 233), fill=WHITE)
    d.text((60, 205), '08  |  GPS TRACKING & FLEET', font=font(FONT_BOLD, 18), fill=(28,116,247))
    d.rectangle((1690, 44, w-55, 90), fill=(247,249,252))
    d.text((1710, 60), 'GPS TRACKING & FLEET', font=font(FONT_BOLD, 13), fill=(106,126,150))
    # Replace previous draft pagination.
    d.rectangle((1960, h-54, w-12, h-4), fill=(247,249,252))
    d.text((1972, h-35), '08 / 27', font=font(FONT_BOLD, 15), fill=(19,48,81))
    return im

def process_closing(im, number):
    im=im.convert('RGB'); w,h=im.size; d=ImageDraw.Draw(im)
    # The artwork previously contained generic WhatsApp/Phone and Email labels without actual details.
    # Replace them with only confirmed contact information and a clear online enquiry CTA.
    x0,y0,x1,y1 = 1230, 720, 1740, 823
    d.rounded_rectangle((x0,y0,x1,y1), radius=14, fill=(5,24,48), outline=(48,190,245), width=2)
    d.text((x0+22,y0+10), 'CONTACT LEVTECH', font=font(FONT_BOLD, 18), fill=(86,210,255))
    d.text((x0+22,y0+38), 'www.levtechs.com', font=font(FONT_BOLD, 22), fill=WHITE)
    d.text((x0+22,y0+70), 'Kampala, Uganda  |  Request a site assessment or quotation online', font=font(FONT_REG, 13), fill=(219,235,249))
    # Rebuild the bottom brand/page strip; omit unknown phone/email details.
    fy=831
    d.rectangle((0, fy, w, h), fill=WHITE)
    d.line((42, fy+2, w-42, fy+2), fill=(218,229,241), width=2)
    d.text((48, fy+21), 'LEVTECH INTEGRATED SYSTEMS', font=font(FONT_BOLD, 16), fill=(20,47,84))
    d.text((300, fy+22), 'SMART. SECURE. RELIABLE.', font=font(FONT_REG, 15), fill=(97,119,145))
    d.line((w-100, fy+10, w-100, h-7), fill=(39,163,247), width=3)
    d.text((w-82, fy+18), f'{number:02d}', font=font(FONT_BOLD, 21), fill=(17,46,82))
    return im

def draw_brand_header(draw, number, section):
    # Recreate the wordmark without duplicating the shared 'Tech' segment.
    brand_font = font(FONT_HEAVY, 37)
    draw.text((68, 34), 'Lev', font=brand_font, fill=(7, 34, 73))
    lev_width = draw.textlength('Lev', font=brand_font)
    draw.text((68 + lev_width - 1, 34), 'Tech', font=brand_font, fill=(20, 121, 248))
    draw.text((71, 78), 'INTEGRATED SYSTEMS', font=font(FONT_BOLD, 13), fill=(103, 124, 151))
    draw.text((1482, 52), 'SMART. SECURE. RELIABLE.', font=font(FONT_BOLD, 17), fill=(40, 67, 101))
    draw.line((65, 118, 1837, 118), fill=(219, 229, 241), width=2)
    draw.text((67, 1290), 'LEVTECH INTEGRATED SYSTEMS', font=font(FONT_BOLD, 15), fill=(21, 49, 85))
    draw.text((303, 1291), 'SMART. SECURE. RELIABLE.', font=font(FONT_REG, 14), fill=(100, 120, 146))
    draw.line((1780, 1283, 1780, 1325), fill=(39, 163, 247), width=3)
    draw.text((1796, 1284), f'{number:02d}', font=font(FONT_BOLD, 20), fill=(17, 46, 82))

def round_paste(base, image, xy, size, radius=20, fit=True):
    image = image.convert('RGB')
    if fit:
        image = ImageOps.fit(image, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    else:
        image = ImageOps.contain(image, size, method=Image.Resampling.LANCZOS)
    if image.size != size:
        backing = Image.new('RGB', size, (244,248,252))
        backing.paste(image, ((size[0]-image.width)//2,(size[1]-image.height)//2))
        image = backing
    mask = Image.new('L', size, 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((0,0,size[0]-1,size[1]-1), radius=radius, fill=255)
    base.paste(image, xy, mask)

def create_gps_page():
    W,H=1902,1345
    im=Image.new('RGB',(W,H),(248,251,255)); d=ImageDraw.Draw(im)
    draw_brand_header(d,8,'GPS TRACKING')
    d.text((68,177),'08  |  GPS TRACKING & FLEET',font=font(FONT_BOLD,19),fill=(25,117,246))
    d.text((65,223),'GPS VEHICLE TRACKING',font=font(FONT_HEAVY,56),fill=(5,25,52))
    d.text((65,290),'& FLEET MANAGEMENT',font=font(FONT_HEAVY,56),fill=(20,121,248))
    d.text((69,374),'Know where vehicles are, understand trips and support better',font=font(FONT_REG,21),fill=(74,96,124))
    d.text((69,408),'fleet control across the working day.',font=font(FONT_REG,21),fill=(74,96,124))
    # Small editorial pills under the title.
    pills=[('CARS & MOTORCYCLES',69,455,282),('TRIP HISTORY',294,455,170),('FLEET VISIBILITY',477,455,192)]
    for label,x,y,w in pills:
        d.rounded_rectangle((x,y,x+w,y+42),radius=20,fill=(232,244,255),outline=(198,226,255),width=2)
        d.text((x+16,y+12),label,font=font(FONT_BOLD,13),fill=(21,91,157))
    # The dashboard visual is cropped from the earlier generated GPS page so the final graphic remains authentic to the series.
    gps=Image.open(SRC/'gps-page-source.png').convert('RGB').crop((1080,140,2005,745))
    round_paste(im,gps,(925,160),(890,584),radius=24,fit=True)
    # Four substantial, readable capabilities.
    cards=[
        ('01','LIVE LOCATION & PLAYBACK','View supported vehicle positions, review trip history and understand route activity.'),
        ('02','GEOFENCING & ALERTS','Set zone rules and receive over-speeding, parking or offline alerts where supported.'),
        ('03','FLEET OVERSIGHT','Use trip and vehicle data to support dispatch, utilisation and operational follow-up.'),
        ('04','REMOTE IMMOBILISATION','Available only with compatible trackers and correct installation; motorcycle cut-off is model/EFI dependent.'),
    ]
    card_y=790; card_h=208; card_w=423; gap=18; x0=67
    for i,(n,title,body) in enumerate(cards):
        x=x0+i*(card_w+gap)
        d.rounded_rectangle((x,card_y,x+card_w,card_y+card_h),radius=18,fill=(255,255,255),outline=(218,230,244),width=2)
        d.rounded_rectangle((x+18,card_y+18,x+67,card_y+67),radius=15,fill=(231,244,255))
        d.text((x+29,card_y+31),n,font=font(FONT_HEAVY,19),fill=(20,121,248))
        d.text((x+82,card_y+25),title,font=font(FONT_BOLD,18),fill=(9,34,67))
        lines=textwrap.wrap(body,width=43)
        for j,line in enumerate(lines[:4]):
            d.text((x+22,card_y+91+j*25),line,font=font(FONT_REG,16),fill=(80,103,130))
    # Applications/compatibility banner.
    d.rounded_rectangle((67,1033,1837,1250),radius=22,fill=(5,25,52))
    d.text((96,1064),'DESIGNED FOR REAL-WORLD FLEETS',font=font(FONT_BOLD,23),fill=(255,255,255))
    d.text((96,1111),'Company and delivery vehicles  •  Motorcycle fleets  •  Field teams  •  NGO and logistics operations',font=font(FONT_REG,18),fill=(203,223,245))
    d.text((96,1162),'Final capability depends on tracker model, vehicle type, installation and selected service plan.',font=font(FONT_REG,15),fill=(128,207,245))
    return im

def create_window_page(number=24):
    W,H=1902,1345
    im=Image.new('RGB',(W,H),(248,251,255)); d=ImageDraw.Draw(im)
    draw_brand_header(d,number,'SMART WINDOW TREATMENTS')
    d.text((68,157),'SMART WINDOW TREATMENTS',font=font(FONT_BOLD,19),fill=(25,117,246))
    d.text((65,194),'Curtains, blinds & switchable smart film',font=font(FONT_HEAVY,45),fill=(5,25,52))
    d.text((68,251),'Automate light, comfort and privacy with compatible window-treatment systems.',font=font(FONT_REG,21),fill=(74,96,124))
    # Two high quality reference crops are re-composed, rather than reproducing the older near-duplicate technical pages.
    curtain_src=Image.open(SRC/'page-37-smart-curtains-reference.jpg').convert('RGB')
    curtain=curtain_src.crop((65,175,570,405))
    film_src=Image.open(SRC/'page-39-smart-film-reference.jpg').convert('RGB')
    film_on=film_src.crop((48,169,329,282))
    film_off=film_src.crop((331,169,636,282))
    card_y=310; card_h=815; card_w=825; left_x=70; right_x=1007
    for x in (left_x,right_x):
        d.rounded_rectangle((x,card_y,x+card_w,card_y+card_h),radius=22,fill=(255,255,255),outline=(218,230,244),width=2)
    round_paste(im,curtain,(left_x+18,card_y+18),(card_w-36,360),radius=16,fit=False)
    # Smart film: two state crops shown side-by-side to explain the clear/private transition.
    state_w=365; state_h=183; sx=right_x+22; sy=card_y+21
    for st_x,st_img,lab in [(sx,film_on,'CLEAR'),(sx+state_w+28,film_off,'PRIVACY')]:
        d.rounded_rectangle((st_x,sy,st_x+state_w,sy+state_h),radius=12,fill=(241,246,251),outline=(218,230,241),width=2)
        round_paste(im,st_img,(st_x+4,sy+4),(state_w-8,state_h-8),radius=8,fit=True)
        d.rounded_rectangle((st_x+12,sy+138,st_x+115,sy+169),radius=12,fill=(5,32,66))
        d.text((st_x+25,sy+145),lab,font=font(FONT_BOLD,14),fill=(255,255,255))
    # Left card copy.
    d.text((left_x+25,card_y+399),'MOTORISED CURTAINS & BLINDS',font=font(FONT_HEAVY,25),fill=(5,25,52))
    d.text((left_x+25,card_y+440),'Bring curtains and blinds into everyday routines with',font=font(FONT_REG,17),fill=(74,96,124))
    d.text((left_x+25,card_y+464),'compatible track motors and connected control systems.',font=font(FONT_REG,17),fill=(74,96,124))
    left_bullets=[('APP OR REMOTE CONTROL','Operate curtains with supported controls.'),('TIMED SCHEDULES & SCENES','Link opening and closing to daily routines.'),('CONNECTED INTEGRATION','Voice/app control depends on the motor and ecosystem.')]
    by=card_y+522
    for title,body in left_bullets:
        d.ellipse((left_x+28,by+1,left_x+42,by+15),fill=(30,166,245))
        d.text((left_x+55,by-1),title,font=font(FONT_BOLD,15),fill=(20,72,131))
        d.text((left_x+55,by+23),body,font=font(FONT_REG,15),fill=(83,104,128))
        by+=70
    # Right card copy.
    d.text((right_x+25,card_y+230),'SWITCHABLE SMART FILM',font=font(FONT_HEAVY,25),fill=(5,25,52))
    d.text((right_x+25,card_y+270),'Change compatible glass from transparent to private/frosted',font=font(FONT_REG,17),fill=(74,96,124))
    d.text((right_x+25,card_y+294),'using an appropriate switching and control solution.',font=font(FONT_REG,17),fill=(74,96,124))
    film_bullets=[('MEETING ROOMS & PARTITIONS','Support privacy in glass meeting rooms and offices.'),('HOMES & GLASS DOORS','A privacy option for suitable windows and glass panels.'),('CONTROL OPTIONS','Switch, remote or smart control based on installation.')]
    by=card_y+354
    for title,body in film_bullets:
        d.ellipse((right_x+28,by+1,right_x+42,by+15),fill=(30,166,245))
        d.text((right_x+55,by-1),title,font=font(FONT_BOLD,15),fill=(20,72,131))
        d.text((right_x+55,by+23),body,font=font(FONT_REG,15),fill=(83,104,128))
        by+=70
    # Small use-case chips make the bottom of each card deliberate rather than leaving dead space.
    def chip(x,y,label):
        f=font(FONT_BOLD,13); tw=d.textlength(label,font=f); ww=int(tw+28)
        d.rounded_rectangle((x,y,x+ww,y+31),radius=15,fill=(236,246,255),outline=(211,231,249),width=1)
        d.text((x+14,y+8),label,font=f,fill=(37,100,159))
        return ww
    xx=left_x+25
    for label in ['LIVING ROOMS','HOTELS','OFFICES','BEDROOMS']:
        xx += chip(xx,1056,label)+9
    xx=right_x+25
    for label in ['MEETING ROOMS','GLASS PARTITIONS','WINDOWS','BATHROOMS']:
        xx += chip(xx,1056,label)+8
    d.rounded_rectangle((70,1150,1832,1253),radius=16,fill=(232,244,255),outline=(207,229,251),width=2)
    d.text((93,1174),'SPECIFICATION NOTE',font=font(FONT_BOLD,15),fill=(18,94,167))
    d.text((93,1205),'Final selection depends on curtain track geometry, motor load, glass type, power requirements and control compatibility.',font=font(FONT_REG,17),fill=(62,89,121))
    return im

def create_network_page(number=30):
    """Editorial spread for LAN, Wi-Fi, structured cabling and IP telephony.
    Product imagery is cropped from the original LevTech solutions artwork."""
    W,H=1902,1345
    im=Image.new('RGB',(W,H),(248,251,255)); d=ImageDraw.Draw(im)
    draw_brand_header(d,number,'NETWORKING & IP TELEPHONY')

    # Dark lead panel with a connected-systems motif.
    d.rounded_rectangle((66,155,914,622),radius=24,fill=(5,25,52))
    d.text((104,190),f'{number:02d}  |  NETWORKING & COMMUNICATION',font=font(FONT_BOLD,17),fill=(64,191,255))
    d.text((100,238),'CONNECTED',font=font(FONT_HEAVY,53),fill=WHITE)
    d.text((100,298),'INFRASTRUCTURE.',font=font(FONT_HEAVY,49),fill=(55,189,255))
    d.text((104,373),'Keep people, devices and sites connected.',font=font(FONT_REG,22),fill=(217,232,247))
    d.text((104,417),'LevTech plans networking and business voice solutions',font=font(FONT_REG,18),fill=(217,232,247))
    d.text((104,445),'around coverage, capacity, reliability and daily use.',font=font(FONT_REG,18),fill=(217,232,247))

    # Network-node illustration links the main solution families.
    center=(485,548)
    nodes=[(210,535,'Wi-Fi'),(355,500,'CCTV'),(615,500,'IP PHONES'),(760,535,'SMART HOME')]
    for x,y,label in nodes:
        d.line((center[0],center[1],x,y),fill=(49,165,235),width=3)
        d.ellipse((x-33,y-33,x+33,y+33),fill=(14,55,98),outline=(72,198,255),width=2)
        # simple, readable pictograms rather than fake logos
        if label=='Wi-Fi':
            d.arc((x-16,y-15,x+16,y+13),200,340,fill=WHITE,width=3); d.arc((x-10,y-7,x+10,y+11),200,340,fill=WHITE,width=3); d.ellipse((x-2,y+9,x+2,y+13),fill=WHITE)
        elif label=='CCTV':
            d.rounded_rectangle((x-15,y-8,x+11,y+8),radius=4,outline=WHITE,width=3); d.line((x+11,y-4,x+20,y-10),fill=WHITE,width=3); d.line((x-5,y+8,x-9,y+17),fill=WHITE,width=3)
        elif label=='IP PHONES':
            d.rounded_rectangle((x-14,y-19,x+14,y+19),radius=5,outline=WHITE,width=3); d.rectangle((x-7,y-12,x+7,y-4),fill=WHITE); d.ellipse((x-3,y+5,x+3,y+11),fill=WHITE)
        else:
            d.rectangle((x-16,y-11,x+16,y+11),outline=WHITE,width=3); d.line((x-5,y+16,x+5,y+16),fill=WHITE,width=3); d.line((x,y+11,x,y+16),fill=WHITE,width=3)
        d.text((x-48,y+43),label,font=font(FONT_BOLD,11),fill=(215,234,251))
    d.ellipse((center[0]-42,center[1]-31,center[0]+42,center[1]+31),fill=(15,116,203),outline=(95,214,255),width=3)
    d.text((center[0]-27,center[1]-9),'LAN',font=font(FONT_HEAVY,20),fill=WHITE)

    # Two original-generated product illustrations: business IP phones and network rack/cabling.
    src=Image.open(SRC/'page-03-our-solutions.png').convert('RGB')
    phone_crop=src.crop((1027,760,1272,849))
    network_crop=src.crop((1281,760,1519,849))
    d.rounded_rectangle((950,155,1835,622),radius=24,fill=WHITE,outline=(215,228,244),width=2)
    d.text((990,183),'BUSINESS VOICE & NETWORK EQUIPMENT',font=font(FONT_BOLD,19),fill=(15,58,103))
    # Crop images remain secondary illustrations, with generous space and clear captions.
    round_paste(im,phone_crop,(990,225),(375,200),radius=15,fit=True)
    round_paste(im,network_crop,(1415,225),(375,200),radius=15,fit=True)
    d.text((1000,445),'IP TELEPHONY',font=font(FONT_HEAVY,21),fill=(10,38,75))
    d.text((1000,477),'Desk phones, extensions and business voice.',font=font(FONT_REG,16),fill=(77,99,127))
    d.text((1425,445),'NETWORKING',font=font(FONT_HEAVY,21),fill=(10,38,75))
    d.text((1425,477),'Switches, cabling and wireless connectivity.',font=font(FONT_REG,16),fill=(77,99,127))
    d.rounded_rectangle((990,530,1792,586),radius=14,fill=(232,244,255),outline=(207,229,250),width=1)
    d.text((1015,549),'One dependable network for people, devices and connected systems.',font=font(FONT_BOLD,16),fill=(28,85,140))

    # Four service cards.
    cards=[
      ('01','STRUCTURED CABLING','Data cabling, fibre or other suitable links planned for the site and required capacity.'),
      ('02','WI-FI & LAN','Router, switch and access-point selection based on coverage, connected devices and user demand.'),
      ('03','IP TELEPHONY','Business phone endpoints, extensions and voice connectivity for suitable offices and teams.'),
      ('04','SYSTEM INTEGRATION','Support connectivity needs for compatible CCTV, intercom, access and smart-home devices.'),
    ]
    y=685; card_w=420; card_h=245; gap=25; x0=67
    for i,(n,title,body) in enumerate(cards):
        x=x0+i*(card_w+gap)
        d.rounded_rectangle((x,y,x+card_w,y+card_h),radius=18,fill=WHITE,outline=(218,230,244),width=2)
        d.rounded_rectangle((x+20,y+18,x+70,y+68),radius=14,fill=(231,244,255))
        d.text((x+31,y+31),n,font=font(FONT_HEAVY,20),fill=(20,121,248))
        d.text((x+88,y+28),title,font=font(FONT_BOLD,17),fill=(9,34,67))
        for j,line in enumerate(textwrap.wrap(body,width=42)):
            d.text((x+22,y+93+j*26),line,font=font(FONT_REG,16),fill=(80,103,130))
    d.rounded_rectangle((67,968,1835,1247),radius=22,fill=(5,25,52))
    d.text((100,1001),'DESIGNED AROUND YOUR SITE',font=font(FONT_HEAVY,25),fill=WHITE)
    d.text((101,1046),'Typical environments',font=font(FONT_BOLD,17),fill=(70,204,255))
    envs=['Offices & call centres','Retail & hospitality','Schools & institutions','Warehouses & multi-site teams']
    x=101
    for label in envs:
        ww=int(d.textlength(label,font=font(FONT_REG,15))+34)
        d.rounded_rectangle((x,1084,x+ww,1128),radius=22,fill=(14,51,91),outline=(52,127,184),width=1)
        d.text((x+17,1098),label,font=font(FONT_REG,15),fill=(234,244,252))
        x+=ww+15
    d.text((101,1170),'Planning note',font=font(FONT_BOLD,15),fill=(80,211,255))
    d.text((230,1170),'Coverage, internet service, PoE needs, voice platform and endpoint count are confirmed at survey.',font=font(FONT_REG,15),fill=(210,228,246))
    return im

def create_closing_page(number=31):
    W,H=1902,1345
    im=Image.new('RGB',(W,H),(255,255,255)); d=ImageDraw.Draw(im)
    source=Image.open(SRC/'page-44-complete-solutions.png').convert('RGB')
    # Premium dark hero band, using the original generated building and installation photography.
    d.rectangle((0,0,W,688),fill=(4,20,43))
    d.rectangle((0,0,W,118),fill=(255,255,255))
    # Use the actual LevTech lockup cropped from the approved closing artwork.
    logo_crop=source.crop((42,0,600,74))
    logo_crop=ImageOps.contain(logo_crop,(530,80),method=Image.Resampling.LANCZOS)
    im.paste(logo_crop,(62,18))
    d.text((1440,48),'PRODUCT & SOLUTIONS CATALOGUE • 2026',font=font(FONT_BOLD,16),fill=(40,70,111))
    d.line((65,118,1837,118),fill=(210,226,242),width=2)
    d.text((67,165),'ONE PARTNER.',font=font(FONT_HEAVY,61),fill=(255,255,255))
    d.text((67,233),'CONNECTED',font=font(FONT_HEAVY,61),fill=(42,186,250))
    d.text((67,301),'SOLUTIONS.',font=font(FONT_HEAVY,61),fill=(255,255,255))
    body=[
      'From consultation and system design to professional',
      'installation, commissioning and ongoing support,',
      'LevTech brings security, smart living, fleet visibility',
      'and power solutions together.'
    ]
    for i,line in enumerate(body): d.text((72,397+i*32),line,font=font(FONT_REG,20),fill=(216,231,247))
    # Use the generated commercial property photo as the main hero visual.
    hero=source.crop((420,50,1505,472))
    round_paste(im,hero,(845,153),(965,500),radius=20,fit=True)
    # Small value statements at the foot of the hero.
    vals=[('01','CONSULT & ASSESS'),('02','DESIGN & SPECIFY'),('03','INSTALL & CONFIGURE'),('04','TEST & HANDOVER'),('05','SUPPORT & MAINTAIN')]
    x=70
    for n,label in vals:
        d.ellipse((x,585,x+42,627),fill=(12,53,97),outline=(55,203,255),width=2)
        d.text((x+10,596),n,font=font(FONT_BOLD,14),fill=(100,224,255))
        d.text((x+52,596),label,font=font(FONT_BOLD,13),fill=(232,243,255))
        x+=350
    # Portfolio band: high-value services are listed explicitly, not generic placeholder labels.
    d.text((69,728),'BUILT AROUND YOUR SITE. CONNECTED AROUND YOUR NEEDS.',font=font(FONT_HEAVY,28),fill=(5,25,52))
    d.text((71,771),'Security, automation, fleet operations, communications and power - planned as one coordinated solution.',font=font(FONT_REG,18),fill=(82,103,127))
    services=[
      ('SECURITY','CCTV • Intrusion & fire alarms • Electric fencing'),
      ('ACCESS','Digital locks • Access control • Gate automation'),
      ('SMART LIVING','Control panels • Lighting • Curtains • Smart devices'),
      ('FLEET','GPS vehicle tracking • Trip history • Fleet alerts'),
      ('POWER','Backup systems • Inverters & batteries • Solar street lights'),
      ('CONNECTIVITY','Wi-Fi • Networking • IP telephony')
    ]
    start_x=70; start_y=827; cw=565; ch=110; gap_x=24; gap_y=18
    for i,(head,bodytxt) in enumerate(services):
        row=i//3; col=i%3; x=start_x+col*(cw+gap_x); y=start_y+row*(ch+gap_y)
        d.rounded_rectangle((x,y,x+cw,y+ch),radius=14,fill=(246,249,253),outline=(220,230,242),width=2)
        d.rectangle((x,y+12,x+5,y+ch-12),fill=(34,160,247))
        d.text((x+24,y+17),head,font=font(FONT_BOLD,16),fill=(20,102,188))
        for j,line in enumerate(textwrap.wrap(bodytxt,width=51)):
            d.text((x+24,y+49+j*24),line,font=font(FONT_REG,16),fill=(69,90,117))
    # Final enquiry banner with only verified website/location details.
    d.rounded_rectangle((70,1088,1832,1242),radius=18,fill=(5,25,52))
    d.text((100,1110),'LET’S BUILD A SAFER, SMARTER TOMORROW TOGETHER.',font=font(FONT_HEAVY,25),fill=(255,255,255))
    d.text((102,1155),'Request a site assessment or quotation online.',font=font(FONT_REG,17),fill=(202,222,243))
    d.text((1220,1114),'www.levtechs.com',font=font(FONT_BOLD,24),fill=(77,213,255))
    d.text((1222,1156),'Kampala, Uganda',font=font(FONT_REG,18),fill=(233,243,251))
    d.text((1222,1190),'Smart. Secure. Reliable.',font=font(FONT_BOLD,16),fill=(140,209,246))
    # White footer band.
    d.line((44,1270,W-44,1270),fill=(219,229,241),width=2)
    brand_f=font(FONT_BOLD,15); tagline_f=font(FONT_REG,14); brand_label='LEVTECH INTEGRATED SYSTEMS'
    d.text((48,1291),brand_label,font=brand_f,fill=(21,49,85))
    d.text((int(48+d.textlength(brand_label,font=brand_f)+20),1292),'SMART. SECURE. RELIABLE.',font=tagline_f,fill=(100,120,146))
    d.line((1780,1283,1780,1325),fill=(39,163,247),width=3)
    d.text((1796,1284),f'{number:02d}',font=font(FONT_BOLD,20),fill=(17,46,82))
    return im

# Curated sequence: service families have their own spread where useful; near-identical variants are removed.
plan = [
 (1, 'Cover', 'Smart solutions for a safer, smarter tomorrow.', 'cover', 'page-01-cover.png'),
 (2, 'Company Profile', 'Who LevTech is, what we stand for, and how we approach integrated technology.', 'standard', 'page-02-company-profile.png'),
 (3, 'Our Solutions', 'One integrated portfolio spanning security, smart living, fleet visibility, power and communications.', 'standard', 'page-03-our-solutions.png'),
 (4, 'Smart Home Product Categories', 'A visual directory of smart control panels, locks, switches, cameras, modules, gateways, sensors, curtains, thermostats and smart film.', 'standard', 'page-04-product-categories.png'),
 (5, 'CCTV & Video Surveillance', 'Cameras and coverage for homes, businesses, institutions and public-facing sites.', 'standard', 'page-10-cctv-surveillance.png'),
 (6, 'Solar & 4G Surveillance Cameras', 'Remote monitoring options for locations where wired power or network access is difficult.', 'standard', 'page-11-solar-4g-surveillance.png'),
 (7, 'Recording, Storage & NVR/DVR Solutions', 'Recording systems and storage infrastructure that support dependable camera deployments.', 'standard', 'page-12-recording-solutions.png'),
 (8, 'GPS Vehicle Tracking & Fleet Management', 'Live location, trip history, geofencing, alerts and compatible remote immobilisation.', 'gps', 'gps-page-source.png'),
 (9, 'Access Control & Attendance', 'Manage entry, credentials and attendance for offices, sites and institutions.', 'standard', 'page-13-access-control-attendance.png'),
 (10, 'Digital Door Locks & Keyless Entry', 'Smart access options across door types, form factors and supported unlocking methods.', 'standard', 'page-07-smart-locks.png'),
 (11, 'Video Intercom Systems', 'See, speak to and manage visitors at doors, gates and building entrances.', 'standard', 'page-09-video-intercom.png'),
 (12, 'Smart Doorbells & Visitor Management', 'Connected doorbells, visitor notifications and remote access from compatible devices.', 'standard', 'page-18-smart-doorbells.png'),
 (13, 'Intrusion Alarms, Motion Sensors & Smart Security', 'Alarm hubs, motion and contact sensors, sirens, remotes, panic buttons and connected alerting.', 'newstyle', 'page-40-intrusion-alarms-smart-security.png'),
 (14, 'Fire Detection & Life Safety', 'Fire alarm and detection components for earlier warning and safer spaces.', 'standard', 'page-15-fire-alarms.png'),
 (15, 'Electric Fencing & Perimeter Protection', 'Perimeter deterrence as part of a coordinated site security plan.', 'standard', 'page-17-electric-fencing.png'),
 (16, 'Automated Gates & Gate Motors', 'Controlled vehicle access and automated entry for residential and commercial sites.', 'standard', 'page-14-gate-automation.png'),
 (17, 'Smart Home Automation', 'Create connected routines for comfort, convenience, control and energy management.', 'standard', 'page-05-smart-home-automation.png'),
 (18, 'Smart Home Control Systems', 'Centralized touch panels and compatible control interfaces for connected spaces.', 'standard', 'page-06-smart-home-control-systems.png'),
 (19, 'Smart Switches, Sockets & Modules', 'Connected switches, outlets, relays, lighting modules and compatible circuit controls.', 'standard', 'page-08-smart-switches.png'),
 (20, 'Smart Plugs & Connected Appliance Control', 'Wi-Fi and Zigbee plugs, supported energy monitoring, wall sockets, in-wall relay modules, timers and appliance scenes.', 'newstyle', 'page-36-smart-plugs.png'),
 (21, 'Smart Lighting & Scenes', 'Lighting control that supports useful scenes, schedules and connected routines.', 'standard', 'page-21-smart-lighting.png'),
 (22, 'Smart Sensors & Environmental Monitoring', 'Sensors for motion, doors and windows, temperature, humidity and other automation or alerting needs.', 'standard', 'page-19-smart-sensors.png'),
 (23, 'Smart Climate Control & HVAC', 'Thermostats, AC controllers, climate modules and supported automation for residential and commercial spaces.', 'standard', 'page-25-smart-climate-control.png'),
 (24, 'Smart Window Treatments & Switchable Film', 'Motorised curtains and blinds, plus switchable privacy film for suitable glass applications.', 'window', 'page-37-smart-curtains-reference.jpg'),
 (25, 'Smart Home Hubs, Gateways & Ecosystems', 'SONOFF Bridge Max/Bridge-M, Tuya gateways, Zigbee devices, Matter interoperability and app/voice ecosystems.', 'newstyle', 'page-37-smart-home-hubs-gateways.png'),
 (26, 'Smart Home Devices & Intelligent Living', 'Smart furniture and cabinet locks, curtain motors and tracks, connected devices and everyday smart-living applications.', 'newstyle', 'page-33-smart-home-devices.png'),
 (27, 'Smart Speakers, Voice Assistants & Whole-Home Audio', 'Echo Show 15, Echo Show 5, Echo Spot, Echo Dot and compatible voice-led audio and connected-home control.', 'newstyle', 'page-34-smart-speakers.png'),
 (28, 'Backup Power, Inverters & Battery Systems', 'Power continuity options for essential equipment and connected installations.', 'standard', 'page-27-backup-power.png'),
 (29, 'Solar Street Lights & Outdoor Energy', 'Autonomous outdoor lighting for compounds, roadsides and suitable public or commercial spaces.', 'standard', 'page-28-solar-street-lights.png'),
 (30, 'Networking & IP Telephony', 'Structured cabling, LAN/Wi-Fi, network equipment and business voice connectivity.', 'network', 'page-03-our-solutions.png'),
 (31, 'One Partner. Connected Solutions.', 'Consultation, design, installation, commissioning and after-sales support across the LevTech portfolio.', 'closing', 'page-44-complete-solutions.png'),
]

# Curated from the strongest of the original 44-page sequence and generated supplemental pages. Near-duplicate lock, switch,
# sensor and thermostat spreads are consolidated. Dedicated smart-plug and hub/gateway pages are retained because they add specific products, not duplicate scenes. The dedicated network/voice page below expands IP
# telephony and connected infrastructure rather than leaving them in summary copy only. The smart-living
# spread retains furniture locks, curtain motors/tracks, SONOFF Bridge Max/Bridge-M and the Echo family.

PAGE_W, PAGE_H = 1902, 1345  # composition canvas; source raster exported with enhanced edge clarity
FINAL_SCALE = 1.0

def enhance_page_for_readability(im):
    """Strengthen fine text/line contrast and export a larger, high-quality page raster.

    The source artwork is raster-based, so enhancement is deliberately modest: no aggressive
    sharpening halos or colour shifts, just improved edge definition and print/display sampling.
    """
    im = im.convert('RGB')
    im = ImageEnhance.Contrast(im).enhance(1.16)
    im = ImageEnhance.Sharpness(im).enhance(1.25)
    im = im.filter(ImageFilter.UnsharpMask(radius=1.15, percent=115, threshold=3))
    size = (round(PAGE_W * FINAL_SCALE), round(PAGE_H * FINAL_SCALE))
    return im.resize(size, Image.Resampling.LANCZOS)

def create_source_page(plan_entry):
    num, title, desc, kind, filename = plan_entry
    p = SRC / filename
    im = Image.open(p).convert('RGB')
    if kind == 'cover':
        im = refresh_cover_year(im)
    elif kind == 'standard':
        im = add_standard_footer_and_number(im, num)
    elif kind == 'newstyle':
        im = process_new_style_page(im, num, title)
    elif kind == 'gps':
        im = create_gps_page()
    elif kind == 'window':
        im = create_window_page(num)
    elif kind == 'network':
        im = create_network_page(num)
    elif kind == 'closing':
        im = create_closing_page(num)
    elif kind == 'overview':
        # Use the full solutions overview on this index-like page: its card clearly names networking and IP telephony.
        im = add_standard_footer_and_number(im, num)
    # Place, rather than crop, the artwork on a uniform A4 landscape canvas.
    contained = ImageOps.contain(im, (PAGE_W, PAGE_H), method=Image.Resampling.LANCZOS)
    canvas = Image.new('RGB', (PAGE_W, PAGE_H), WHITE)
    x=(PAGE_W-contained.width)//2; y=(PAGE_H-contained.height)//2
    canvas.paste(contained, (x,y))
    return canvas

def build():
    page_records=[]
    # Clear stale generated page previews from previous runs so the package matches the curated count.
    for old in PAGES.glob('page-*.jpg'):
        old.unlink()
    for num, title, desc, kind, filename in plan:
        img = create_source_page((num,title,desc,kind,filename))
        img = enhance_page_for_readability(img)
        outname = f'page-{num:02d}-{re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:45]}.jpg'
        path = PAGES/outname
        img.save(path, 'JPEG', quality=96, optimize=True, progressive=True, subsampling=0)
        page_records.append({'num':num,'title':title,'description':desc,'kind':kind,'filename':outname})
    # Build high quality, uniform-size A4 landscape PDF from final page images.
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4, landscape
    pdf_path = ROOT/'LevTech_Integrated_Systems_Catalogue_2026.pdf'
    page_size = landscape(A4)
    c = canvas.Canvas(str(pdf_path), pagesize=page_size, pageCompression=1)
    c.setTitle('LevTech Integrated Systems | Product & Solutions Catalogue 2026')
    c.setAuthor('LevTech Integrated Systems')
    c.setSubject('Curated catalogue of security, smart home, fleet, networking and power solutions')
    pw,ph=page_size
    for rec in page_records:
        bookmark = f"page{rec['num']:02d}"
        c.bookmarkPage(bookmark)
        c.addOutlineEntry(f"{rec['num']:02d} - {rec['title']}", bookmark, level=0, closed=False)
        c.drawImage(str(PAGES/rec['filename']),0,0,width=pw,height=ph, preserveAspectRatio=False, mask='auto')
        c.showPage()
    c.save()
    manifest = [dict(num=r['num'], title=r['title'], description=r['description'], filename=r['filename']) for r in page_records]
    (ROOT / 'catalogue_manifest.js').write_text('window.LEVTECH_CATALOGUE_PAGES = ' + json.dumps(manifest, ensure_ascii=False, indent=2) + ';\n', encoding='utf-8')
    (ROOT / 'catalogue_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return page_records, pdf_path

if __name__=='__main__':
    records,pdf=build()
    print(f'Built {len(records)} catalogue pages: {pdf}')
