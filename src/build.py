from pathlib import Path
from copy import deepcopy
from lxml import etree, html

root = Path(__file__).resolve().parents[1]
dist = root / 'dist'
source = html.fragment_fromstring((root/'src/home-original.html').read_text(),create_parent='div')
for el in source.xpath('.//img[starts-with(@src,"/assets")]'):
    el.set('src','/media/original'+el.get('src'))
def by_class(node,k):
    return node.xpath('.//*[contains(concat(" ",normalize-space(@class)," ")," '+k+' ")]')[0]
def parse(raw): return html.fragment_fromstring(raw)
def render(node):return html.tostring(node,encoding='unicode',method='html')
def icon(paths,w=24):
    return f'<svg aria-hidden="true" viewBox="0 0 24 24" width="{w}" height="{w}" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{paths}</svg>'
cutlery=icon('<path d="m8 3-1 6m-2-6-1 6m7-5-1 6q-1 4-5 3L3.8 21m14-18q-4 5-4 10l3.1.3L16 21m2-18-1 10"/>',19)
def add_icon(el,s):
    x=parse(s);x.tail=el.text;el.text=None;el.insert(0,x)
brand_art = etree.parse(str(root/'src/brand-lockup.svg')).getroot()

def brand_lockup(node):
    brand = by_class(node, 'brand')
    brand.set('class', brand.get('class') + ' brand-lockup')
    for child in list(brand):
        brand.remove(child)
    brand.append(deepcopy(brand_art))

def contact_disclosure(placement):
    note_id = f'contact-note-{placement}'
    chevron = icon('<path d="m7 10 5 4 5-4"/>', 16)
    mail = icon('<rect x="3" y="5.8" width="18" height="12.7" rx="1.7"/><path d="m4.4 7.1 7.4 5.7 7.7-5.7"/>', 18)
    instagram = icon('<rect x="3.2" y="3.2" width="17.6" height="17.6" rx="4.9"/><circle cx="12" cy="12" r="4.2"/><circle cx="17.2" cy="6.9" r=".8" fill="currentColor" stroke="none"/>', 18)
    phone = icon('<path d="M6.9 3.9 5.1 5.4c-1.9 2.3.7 7.1 3.9 10.4 3.3 3.3 7.6 5.6 9.8 3.9l1.3-1.5c.5-.6.4-1.3-.2-1.8l-3.4-2.2c-.6-.4-1.2-.3-1.7.2l-1.1 1.2c-2-1.2-4-3.1-5.3-5.5l1.3-1.2c.5-.5.6-1.1.2-1.7L7.8 4c-.3-.5-.6-.5-.9-.1Z"/>', 18)
    return parse(f"""<details class="nav-contact">
      <summary class="contact-trigger" id="{note_id}-trigger" aria-controls="{note_id}">Contact {chevron}</summary>
      <div class="contact-note" id="{note_id}" role="group" aria-labelledby="{note_id}-trigger">
        <a class="contact-row" href="mailto:cookd.cafe@gmail.com">{mail}<span>cookd.cafe@gmail.com</span></a>
        <a class="contact-row" href="https://www.instagram.com/cookd.cafe/" target="_blank" rel="noopener noreferrer">{instagram}<span>@cookd.cafe</span></a>
        <span class="contact-row contact-phone">{phone}<span>(phone number here)</span></span>
      </div>
    </details>""")

def header(menu=False):
    nd=deepcopy(source.find('header'))
    desktop = by_class(nd, 'desktop-nav')
    mobile = by_class(nd, 'mobile-nav')
    mobile.set('data-lenis-prevent', '')
    cta = by_class(nd, 'header-cta')
    add_icon(cta, cutlery)
    if menu:
        cta.set('aria-current', 'page')

    for nav in (desktop, mobile):
        nav.remove(nav.xpath('./a[@href="/menu/"]')[0])
        home = nav.xpath('./a[@href="/"]')[0]
        if menu:
            home.attrib.pop('aria-current', None)
            home.attrib.pop('class', None)
        else:
            home.set('aria-current', 'page')
    redundant_link = by_class(nd, 'mobile-menu-link')
    redundant_link.getparent().remove(redundant_link)

    desktop.append(contact_disclosure('desktop'))
    tagline = by_class(mobile, 'mobile-nav-tagline')
    mobile.insert(mobile.index(tagline), contact_disclosure('mobile'))
    drawer_cta = deepcopy(cta)
    drawer_cta.set('class', 'header-cta drawer-menu-cta')
    mobile.insert(mobile.index(tagline), drawer_cta)
    brand_lockup(nd)
    return render(source.find('a'))+render(nd)
def footer():
    f=deepcopy(source.find('footer'))
    brand_lockup(f)
    directory = by_class(f, 'footer-links')
    directory.tag = 'nav'
    directory.set('aria-label', 'Footer navigation')
    address = by_class(f, 'footer-visit').find('address')
    street = address.text
    road = 'Troughton Rd'
    if street and street.endswith(road):
        address.text = street[:-len(road)]
        street_name = etree.Element('span', {'class': 'footer-street'})
        street_name.text = road
        address.insert(0, street_name)
    # The street address already identifies the neighbourhood.
    bottom = by_class(f, 'footer-bottom')
    for location in bottom.xpath('./span[normalize-space(.)="Sunnybank · Brisbane"]'):
        bottom.remove(location)
    return render(f)
shared_head = '<script>' + (root/'src/nav-entry.js').read_text() + '</script>' + """
<link rel="icon" href="/media/original/favicon-32.png"><link rel="apple-touch-icon" href="/media/original/apple-touch-icon.png">
<meta name="robots" content="noindex,follow"><meta name="theme-color" content="#fff8e9">
<link rel="preload" href="/fonts/schoolbell-normal400.woff" as="font" type="font/woff" crossorigin>
<link rel="stylesheet" href="/fonts/fonts.css"><link rel="stylesheet" href="/site.css"><link rel="stylesheet" href="/brand.css"><link rel="stylesheet" href="/contact.css"><link rel="stylesheet" href="/footer-reveal.css"><link rel="stylesheet" href="/media/mascot/sprites.css"><link rel="stylesheet" href="/vendor/lenis.css"><link rel="stylesheet" href="/motion.css">
<script defer src="/vendor/gsap.min.js"></script><script defer src="/vendor/ScrollTrigger.min.js"></script><script defer src="/vendor/lenis.min.js"></script><script defer src="/motion.js"></script><script defer src="/navigation.js"></script><script defer src="/site.js"></script><script defer src="/footer-reveal.js"></script>
"""
home_head='''<!doctype html><html lang="en-AU"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Cook'd Cafe Sunnybank | Asian-Inspired Breakfast &amp; Coffee</title><meta name="description" content="Visit Cook'd Cafe in Sunnybank for creative Asian-inspired breakfast and lunch, Five Senses coffee and small-batch fresh bakes.">
<link rel="preload" as="image" href="/media/brand/hero-wordmark.svg"><link rel="preload" as="image" type="image/webp" href="/media/original/assets/menu/chilli-crab-omurice.webp">'''+shared_head
home_styles = ['hero-scene', 'story', 'story-lettering', 'editorials', 'visit']
home_scripts = ['hero-scene', 'story', 'editorials', 'visit-hours']
home_head += ''.join(f'<link rel="stylesheet" href="/{name}.css">' for name in home_styles)
home_head += '<script src="/story-lettering.js"></script>'
home_head += ''.join(f'<script defer src="/{name}.js"></script>' for name in home_scripts)
home_head += (root/'src/original/home-metadata.html').read_text().replace('assets/customer/cookd-noren-concept.webp','assets/menu/kaya-shokupan.webp') + '</head><body class="home-page">'
sections = ['landing', 'story', 'editorials', 'visit']
content = '<main id="main">' + ''.join((root/'src'/f'{name}.html').read_text() for name in sections) + '</main>'
(dist/'index.html').write_text(home_head + header() + content + footer() + (root/'src/original/home-noscript.html').read_text() + '</body></html>')
menu_template=root/'src/menu-template.html'
menu_path=dist/'menu/index.html'
if menu_path.exists() and '<!--SITE_HEADER-->' in menu_path.read_text():
    menu_template.write_text(menu_path.read_text())
if menu_template.exists():
    menu_path.write_text(menu_template.read_text().replace('<!--SITE_HEADER-->',header(True)).replace('<!--SITE_FOOTER-->',footer()).replace('<!--SITE_HEAD-->',shared_head).replace('</body>',(root/'src/original/menu-noscript.html').read_text()+'</body>'))
