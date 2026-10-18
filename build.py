#!/usr/bin/env python3
"""South Jersey Seller's Guide: static site generator.
Reads data/*.json and writes the site into docs/.

Env vars:
  BASE         absolute origin for canonical URLs + sitemap (e.g. https://jgonthego.github.io)
  PATH_PREFIX  sub-path the site is served from (e.g. /sj-seller-guide); '' for local/root
  FORM_ID      Formspree form id; when unset the email signup renders disabled
"""
import json, os, html, shutil, re
from datetime import date

BASE = os.environ.get("BASE", "http://localhost:8000").rstrip("/")
PREFIX = os.environ.get("PATH_PREFIX", "").rstrip("/")
FORM_ID = os.environ.get("FORM_ID", "").strip()
SHOW_FORM = bool(FORM_ID) and FORM_ID != "YOUR_FORM_ID"
SITE = "South Jersey Seller's Guide"
TAG = "Selling a home in South Jersey: NJ rules, closing costs and town-by-town resale requirements"
OUT = "docs"
e = html.escape

M = json.load(open("data/municipalities.json"))
V = json.load(open("data/towns_verified.json")); V.pop("_note", None)
S = json.load(open("data/statewide.json")); SRC = S["sources"]; CHECKED = S["checked"]
COUNTIES = ["Atlantic", "Cape May", "Cumberland", "Salem", "Gloucester", "Camden", "Burlington", "Ocean"]
EQFILE = {"Cape May": "CapeMay"}
CSS = open("site/style.css").read()
JS = open("site/app.js").read()

def L(p): return PREFIX + p
def canon(p): return BASE + PREFIX + p
def cslug(c): return c.lower().replace(" ", "-")
def src(key, text=None):
    t, u = SRC[key]
    return f'<a class="src" href="{u}" rel="noopener">{e(text or t)}</a>'
def srclist(keys):
    return '<ul class="sources">' + "".join(f"<li>{src(k)}</li>" for k in keys) + "</ul>"
def money(x): return "${:,.0f}".format(x)

for m in M:
    m["v"] = V.get(m["slug"])
    m["status"] = m["v"]["status"] if m["v"] else "unverified"

STATUS_LABEL = {"verified": "Verified", "partial": "Partly verified", "unverified": "Not yet verified"}

LOGO = '<svg viewBox="0 0 32 32" width="30" height="30" aria-hidden="true"><defs><linearGradient id="lg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f5c76b"/><stop offset="1" stop-color="#e08a3c"/></linearGradient></defs><rect width="32" height="32" rx="9" fill="#0f2a44"/><path d="M7 17 16 9l9 8v7a1 1 0 0 1-1 1h-5v-5h-6v5H8a1 1 0 0 1-1-1z" fill="url(#lg)"/><path d="M5 26c4-2 7-2 11 0s7 2 11 0" stroke="#5ed0c4" stroke-width="1.8" fill="none" stroke-linecap="round"/></svg>'

NAV = [("/closing-costs/", "Closing costs"), ("/disclosures/", "Disclosures"), ("/smoke-co-certificate/", "Smoke/CO cert"), ("/timeline/", "Timeline"), ("/checklist/", "Checklist"), ("/towns/", "Towns")]

def signup():
    if SHOW_FORM:
        return f'''<form class="signup" action="https://formspree.io/f/{e(FORM_ID)}" method="POST"><label for="em">Get rule-change alerts for South Jersey sellers</label><div class="row"><input id="em" type="email" name="email" placeholder="you@example.com" required><input type="hidden" name="list" value="sj-seller-alerts"><button>Subscribe</button></div></form>'''
    return '''<!-- NEWSLETTER HOOK: set FORM_ID (Formspree id) at build time to enable this form -->
<form class="signup is-disabled" aria-disabled="true" onsubmit="return false"><label for="em">Rule-change alerts for South Jersey sellers <span class="pill">coming soon</span></label><div class="row"><input id="em" type="email" placeholder="you@example.com" disabled><button disabled>Subscribe</button></div><small>Sign-up is not active yet. This form collects nothing.</small></form>'''

def sponsor():
    return '''<aside class="sponsor" aria-label="Featured local pros (placeholder)"><div class="sponsor-h"><span class="pill pill-muted">Placeholder</span> Featured local pros</div><div class="sponsor-grid"><div class="slot">Sponsor slot<br><small>Real estate attorney</small></div><div class="slot">Sponsor slot<br><small>Home inspector / fire-cert prep</small></div><div class="slot">Sponsor slot<br><small>Title &amp; settlement</small></div></div><p class="muted small">This space is reserved for future local sponsors and lists no businesses today. Sponsorship will never change what this guide says.<!-- SPONSOR HOOK: add a sponsorship contact link here --></p></aside>'''

DISCLAIMER = f'<p><b>Not legal or tax advice.</b> This guide summarizes public sources for general information. Rules and fees change and vary by town. Confirm everything with your NJ real estate attorney, your tax advisor and the municipality before you rely on it. Statewide facts last checked {CHECKED}; each town page shows its own source links and check date.</p>'

PAGES = []
def page(path, title, desc, body, crumbs=None, ld=None, active=None):
    nav = "".join(f'<a href="{L(p)}"{" aria-current=page" if p==active else ""}>{t}</a>' for p, t in NAV)
    bc = ""
    if crumbs:
        bc = '<nav class="crumbs" aria-label="Breadcrumb"><a href="' + L("/") + '">Home</a>' + "".join(f' <span>/</span> <a href="{L(p)}">{e(t)}</a>' if p else f' <span>/</span> <b>{e(t)}</b>' for t, p in crumbs) + "</nav>"
    lds = "" if not ld else f'<script type="application/ld+json">{json.dumps(ld)}</script>'
    full = f"{title} | {SITE}" if path != "/" else f"{SITE}: {TAG}"
    doc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(full)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{canon(path)}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:type" content="website"><meta property="og:url" content="{canon(path)}"><meta property="og:site_name" content="{e(SITE)}"><meta name="twitter:card" content="summary">
<meta name="theme-color" content="#0f2a44"><link rel="icon" href="{L('/favicon.svg')}" type="image/svg+xml"><link rel="stylesheet" href="{L('/assets/style.css')}">{lds}</head>
<body><a class="skip" href="#main">Skip to content</a>
<header class="top"><div class="wrap top-in"><a class="brand" href="{L('/')}">{LOGO}<span>South Jersey<b> Seller's Guide</b></span></a><button class="menu" aria-label="Menu" onclick="document.body.classList.toggle('nav-open')">☰</button><nav class="nav">{nav}</nav></div></header>
<main id="main" class="wrap">{bc}{body}
<section class="band">{signup()}</section>{sponsor()}</main>
<footer class="foot"><div class="wrap"><div class="disc">{DISCLAIMER}</div><div class="foot-cols"><div><b>{SITE}</b><br>An independent guide for homeowners selling in Atlantic, Cape May, Cumberland, Salem, Gloucester, Camden, Burlington and Ocean counties.</div><div><a href="{L('/about/')}">About, method &amp; sources</a><br><a href="{L('/checklist/')}">Printable checklist</a><!-- CONTACT HOOK: add a corrections email/link here --></div></div><p class="muted small">Anonymous visit counts via GoatCounter (no cookies).</p></div></footer>
<script src="{L('/assets/app.js')}" defer></script><script>window.goatcounter={{path:function(){{return location.pathname||'/'}}}}</script><script data-goatcounter="https://jgonthego.goatcounter.com/count" async src="{L('/assets/gc.js')}"></script></body></html>'''
    d = OUT + path
    os.makedirs(d, exist_ok=True)
    open(d + ("index.html" if path.endswith("/") else ""), "w").write(doc)
    PAGES.append(path)

# ---------------- RTF helpers (mirrored in site/app.js) ----------------
R = S["rtf"]
def tier_calc(price, tiers):
    fee = 0.0
    for lo, hi, rate in tiers:
        if price > lo:
            top = price if hi is None else min(price, hi)
            fee += (top - lo) / 500.0 * rate
    return round(fee, 2)
def rtf(price, kind="standard"):
    k = ("standard" if kind == "standard" else "reduced") + ("_le350" if price <= 350000 else "_gt350")
    return tier_calc(price, R[k])
def gpf(price):
    for lo, hi, pct in R["gpf"]:
        if price > lo and (hi is None or price <= hi): return round(price * pct / 100, 2)
    return 0.0
for p, k, want in R["tests"]:
    got = rtf(p, k); assert abs(got - want) < 0.01, (p, k, got, want)
assert gpf(2750000) == 68750  # example from Division of Taxation memo (July 2, 2025)

def rate_table(rows):
    out = '<table class="t"><thead><tr><th>Portion of price over</th><th>…but not over</th><th>Rate per $500</th></tr></thead><tbody>'
    for lo, hi, r in rows:
        out += f"<tr><td>{money(lo)}</td><td>{money(hi) if hi else 'no limit'}</td><td>${r:.2f}</td></tr>"
    return out + "</tbody></table>"

# ---------------- statewide pages ----------------
def closing_costs():
    ex = [300000, 450000, 750000, 1500000, 2750000]
    ex_rows = "".join(f"<tr><td>{money(p)}</td><td>{money(rtf(p))}</td><td>{money(gpf(p)) if gpf(p) else '—'}</td><td><b>{money(rtf(p)+gpf(p))}</b></td></tr>" for p in ex)
    gp = "".join(f"<tr><td>{money(lo)}</td><td>{money(hi) if hi else 'no limit'}</td><td>{pct:g}% of the <b>entire</b> price</td></tr>" for lo, hi, pct in R["gpf"])
    b = f'''<div class="hero hero-sm"><p class="eyebrow">Statewide · NJ law</p><h1>NJ seller closing costs</h1><p class="lead">In New Jersey the <b>seller</b> pays the state Realty Transfer Fee. Since July 10, 2025 the seller also pays the Graduated Percent Fee (the old "mansion tax") on sales over $1 million. Nonresident sellers usually make an estimated income-tax payment at closing.</p><p class="checked">Last checked {CHECKED}</p></div>
<div class="grid2">
<section class="card"><h2>Estimate your transfer fees</h2><div class="calc" id="calc"><label>Sale price (deed consideration)<input id="cprice" inputmode="numeric" value="450,000"></label><label class="chk"><input type="checkbox" id="cred"> Seller qualifies for the reduced rate (senior 62+, blind, disabled, or low/moderate-income housing; Form RTF-1 required)</label><label>Property class<select id="cclass"><option value="res">Class 2 residential (1–4 units), farm with residence (3A), 4A commercial, 4C co-op</option><option value="other">Other class (Graduated Percent Fee does not apply)</option></select></label><div class="calc-out" aria-live="polite"><div><span>Realty Transfer Fee</span><b id="o-rtf">—</b></div><div><span>Graduated Percent Fee</span><b id="o-gpf">—</b></div><div class="tot"><span>Total state transfer fees</span><b id="o-tot">—</b></div></div><p class="small muted">Uses the official rate tables below. It is an estimate only: exemptions, Director's-ratio valuations and mixed-class properties change the result. Your settlement agent calculates the actual fee, which is paid to the county when the deed is recorded.</p></div></section>
<section class="card"><h2>Quick examples (standard rate, residential)</h2><table class="t"><thead><tr><th>Price</th><th>RTF</th><th>Graduated %</th><th>Total</th></tr></thead><tbody>{ex_rows}</tbody></table><p class="small muted">Checked against the Division of Taxation's own examples: $325,000 gives an RTF of $1,910; $280,000 at the senior partial-exemption rate gives $475 ({src("rtf_faq","RTF FAQ")}); $2.75M gives a Graduated Percent Fee of $68,750 ({src("gpf_notice","July 2025 memo")}).</p></section>
</div>
<section class="card" id="rtf"><h2>1. Realty Transfer Fee (RTF): official rate table</h2><p>The fee is charged on the consideration recited in the deed and paid to the county recording officer when the deed is recorded. Which schedule applies depends on whether the <b>total</b> consideration is above or below $350,000. Each band's rate applies only to the part of the price inside that band.</p>
<div class="grid2"><div><h3>Standard: total price $350,000 or less</h3>{rate_table(R["standard_le350"])}</div><div><h3>Standard: total price over $350,000</h3>{rate_table(R["standard_gt350"])}</div>
<div><h3>Reduced rate: total price $350,000 or less</h3>{rate_table(R["reduced_le350"])}</div><div><h3>Reduced rate: total price over $350,000</h3>{rate_table(R["reduced_gt350"])}</div></div>
<h3>Who gets the reduced rate</h3><p>Partial exemptions apply to qualifying <b>senior citizens 62 or older</b>, qualifying <b>blind</b> persons, qualifying <b>disabled</b> persons, and <b>low- and moderate-income housing</b>. The seller claims it on a notarized <b>Form RTF-1</b> (Affidavit of Consideration for Use by Seller), recorded with the deed.</p>
<h3>Full exemptions (deeds the RTF does not apply to)</h3><ul class="cols">
<li>Consideration under $100</li><li>To/from the US, the State or its agencies/subdivisions</li><li>Only to provide or release security for a debt</li><li>Confirming or correcting a prior recorded deed</li><li>Sale for delinquent taxes or assessments</li><li>On partition</li><li>By a receiver, bankruptcy trustee or assignee for creditors</li><li>Between husband and wife, or parent and child</li><li>Cemetery lot or plot</li><li>Executor/administrator to a devisee or heir under a will or intestacy</li><li>Within 90 days after a divorce decree, between the former spouses</li><li>Specific performance of a final judgment; release of a right of reversion; and others listed by the Division</li></ul>
<p class="small">Sources: {src("rtf_page")} · {src("rtf_faq")}</p></section>
<section class="card accent" id="mansion"><h2>2. The "mansion tax" is now the Graduated Percent Fee, and the <u>seller</u> pays it</h2>
<p><b>What changed in 2025:</b> P.L.2025, c.69 (approved June 30, 2025; effective <b>July 10, 2025</b>) replaced the flat 1% buyer-paid fee on sales over $1 million with a <b>graduated fee paid by the seller (grantor)</b>. The rate applies to the <b>entire</b> price, not just the amount over a threshold.</p>
<table class="t"><thead><tr><th>Price over</th><th>…not over</th><th>Graduated Percent Fee</th></tr></thead><tbody>{gp}</tbody></table>
<p>It applies to deeds for property classed as <b>Class 2 residential (1–4 units)</b>, <b>Class 3A farm</b> (only if it has a building suited for residential use), <b>Class 4A commercial</b> and <b>Class 4C co-op units</b>. Form RTF-1EE must accompany every deed over $1,000,000. The parties can negotiate who bears the cost in the contract, but the law puts it on the seller.</p>
<p><b>Transition rule:</b> for contracts signed before July 10, 2025 with deeds recorded by November 15, 2025, the seller could claim a refund of the amount above 1% on Form RTF-3. The Division also notes that refund claims generally must be filed within 90 days of payment (N.J.S.A. 46:15-7.2(c)), so check timing with your attorney.</p>
<p class="small">Sources: {src("pl2025c69")} · {src("gpf_notice")} · {src("gpf_exempt")} · {src("rtf_page")}. Note: an older answer in the Division's RTF FAQ still describes the pre-2025 "buyers must remit the 1% fee" rule. The 2025 statute and memo control.</p></section>
<section class="card" id="gitrep"><h2>3. Nonresident sellers: GIT/REP forms</h2>
<p>Every seller files one GIT/REP form with the deed. NJ residents certify residency or an exemption on <b>GIT/REP-3</b>. A <b>nonresident</b> individual, estate or trust generally completes <b>GIT/REP-1</b> and makes an estimated Gross Income Tax payment at or before closing, whether or not there is a gain.</p>
<ul><li><b>Amount:</b> the gain × the top NJ rate (<b>10.75%</b>), but <b>never less than 2% of the consideration</b> (the seller's share). 2% is a floor, not a cap.</li><li><b>Alternatives:</b> an exemption claimed on GIT/REP-3, a waiver on GIT/REP-4, or a prepayment receipt (GIT/REP-2). The forms list the qualifying situations.</li><li>If GIT/REP-1 is incomplete, the county clerk will not record the deed. Any overpayment is reconciled when the seller files an NJ nonresident return.</li></ul>
<p class="small">Sources: {src("gitrep_faq")} · {src("gitrep1")} · {src("tb57")} · {src("gitrep_forms")}</p></section>
<section class="card"><h2>4. Other common seller costs (not set by state law)</h2><ul><li>Mortgage payoff and lien releases; prorated property taxes and water/sewer through closing.</li><li>Real estate commission (negotiable), attorney fees, municipal certificate fees (see your <a href="{L('/towns/')}">town page</a>) and smoke/CO certificate fees.</li><li>Federal capital-gains exclusion on a main home: up to $250,000 ($500,000 for most joint filers) if ownership/use tests are met. See {src("irs_701")}.</li></ul></section>'''
    page("/closing-costs/", "NJ Seller Closing Costs 2026: Realty Transfer Fee, Mansion Tax, GIT/REP", "Official NJ Realty Transfer Fee rate tables, exemptions and reduced rates, the 2025 seller-paid Graduated Percent Fee (mansion tax), and GIT/REP rules for nonresident sellers, with a calculator.", b, crumbs=[("Closing costs", None)], active="/closing-costs/")

def attorney():
    b = f'''<div class="hero hero-sm"><p class="eyebrow">Statewide · NJ law</p><h1>The 3-day attorney review period</h1><p class="lead">When a licensed agent prepares the contract to sell a 1–4 family home in NJ, either side's attorney can review it and cancel it within <b>three business days</b>.</p><p class="checked">Last checked {CHECKED}</p></div>
<div class="grid2"><section class="card"><h2>How it works</h2><ul class="steps"><li><b>Counting:</b> the 3 days start when the <b>signed contract is delivered</b> to both buyer and seller. Saturdays, Sundays and legal holidays don't count.</li><li><b>Disapproval:</b> if an attorney disapproves, notice must reach the broker(s) and the other party within the 3 days. Otherwise the contract becomes binding as written.</li><li><b>Notice method:</b> the regulation's text lists certified mail, telegram or personal delivery. In <i>Conley v. Guerrero</i> (2017) the NJ Supreme Court held that fax, email, personal delivery or overnight mail with proof of delivery also work.</li><li><b>Extension:</b> buyer and seller may agree in writing to extend the period.</li><li><b>Where it applies:</b> contracts prepared by real estate licensees for 1–4 unit residential property (and vacant one-family lots) where the licensee earns a commission. The contract must carry the warning in large print at the top of page 1.</li></ul></section>
<section class="card"><h2>What sellers typically do during review</h2><ul><li>Have your attorney check price, deposit timing, inspection and mortgage contingencies, closing date and who pays which certificate fees.</li><li>Order your town's resale certificate and the smoke/CO certificate early. Many fee schedules jump when you apply with fewer than 10 business days to go.</li><li>Gather the Seller's Property Condition Disclosure Statement (with the mandatory flood questions), survey, elevation certificate if you have one, and solar lease/PPA documents if any.</li></ul><p class="small muted">Practical tips, not legal requirements. Ask your attorney.</p></section></div>
<section class="card"><h2>Sources</h2>{srclist(["njac_11_5_6_2", "conley"])}</section>'''
    page("/attorney-review/", "NJ Attorney Review Period (3 Business Days) for Home Sellers", "How New Jersey's three-business-day attorney review period works for home sale contracts: counting days, notice of disapproval and Conley v. Guerrero.", b, crumbs=[("Attorney review", None)])

def disclosures():
    b = f'''<div class="hero hero-sm"><p class="eyebrow">Statewide · NJ law</p><h1>NJ seller disclosure requirements</h1><p class="lead">New Jersey sellers fill out the Division of Consumer Affairs' <b>Seller's Property Condition Disclosure Statement</b>. Since <b>March 20, 2024</b> its <b>Flood Risk</b> questions are mandatory under P.L.2023, c.93.</p><p class="checked">Last checked {CHECKED}</p></div>
<div class="grid2"><section class="card accent"><h2>Flood risk disclosure (P.L.2023, c.93)</h2><ul><li>Applies to <b>all sellers of real property</b>, residential and non-residential. Questions 109–117 (the Flood Risk addendum) are mandatory for everyone; questions 1–108 are mandatory for residential sales.</li><li>Must be given <b>before the buyer becomes obligated</b> under the contract.</li><li>Asks whether the property is in FEMA's Special Flood Hazard Area ("100-year") or Moderate Risk area ("500-year"); whether federal law requires flood insurance; past flood damage, claims and FEMA/other assistance; and whether a FEMA <b>elevation certificate</b> exists (if so, it must be shared with the buyer).</li><li>Questions about flood history are answered from the seller's actual knowledge. Check zones with NJDEP's {src("flood_tool","address look-up tool")} or FEMA's {src("fema_msc","Flood Map Service Center")}.</li></ul><p class="small">Sources: {src("pl2023c93")} · {src("dca_flood_news")} · {src("dep_flood_faq")} · {src("dep_flood")}</p></section>
<section class="card"><h2>Other disclosure rules sellers hit</h2><ul><li><b>Solar panels (P.L.2023, c.312):</b> for a single-family home with solar panels, the disclosure statement, contract or a rider must name the installer and the panel owner/PPA company. If panels are leased or under a PPA, it must state clearly whether the lease/PPA transfers and attach the surviving contract documents. Applies to panels installed on or after Jan 16, 2024, once the Real Estate Commission posted its guidance.</li><li><b>Lead paint (federal):</b> for homes built before 1978, sellers must disclose known lead-based paint and hazards, hand over records, give the EPA pamphlet, include the lead warning statement and give buyers a 10-day chance to test. See the <a href="{L('/lead-paint/')}">lead paint page</a>.</li><li><b>Secondary power sources:</b> homes with a generator, solar or battery need a warning label at the panel and meter before a change of occupancy. See the <a href="{L('/smoke-co-certificate/')}">smoke/CO certificate page</a>.</li></ul><p class="small">Sources: {src("pl2023c312")} · {src("pcds")} · {src("epa_lead")}</p></section></div>
<section class="card"><h2>Get the official form</h2><p>Download the current {src("pcds","Seller's Property Condition Disclosure Statement")} from the Division of Consumer Affairs and answer from your actual knowledge. Ask your attorney about anything you're unsure of.</p></section>'''
    page("/disclosures/", "NJ Seller Disclosure Requirements (2024 Flood Risk Law, Solar, Lead)", "What New Jersey home sellers must disclose: the Seller's Property Condition Disclosure Statement, mandatory flood-risk questions since March 2024, solar panel and lead paint disclosures.", b, crumbs=[("Disclosures", None)], active="/disclosures/")

def smoke():
    b = f'''<div class="hero hero-sm"><p class="eyebrow">Statewide · NJ Uniform Fire Code</p><h1>The smoke alarm / CO alarm certificate</h1><p class="lead">Before any 1- or 2-family home changes occupancy (a sale or a new tenant), New Jersey requires a certificate showing working <b>smoke alarms</b> and <b>carbon monoxide alarms</b>. Since February 3, 2025 the inspection also covers a <b>secondary power source label</b>.</p><p class="checked">Last checked {CHECKED}</p></div>
<section class="card accent"><h2>Big 2025 change: fire extinguishers are no longer part of it</h2><p><b>P.L.2025, c.19</b> (approved and effective February 3, 2025) amended N.J.S.A. 52:27D-198.1. It dropped the portable fire extinguisher from the resale certificate and added a check for a <b>secondary power source identification label</b> (for homes with a generator, solar PV, battery storage, etc.) located within 18 inches of the electrical panel and meter. The certificate formerly known as the "CSDCMAFEC" (Certificate of Smoke Detector, Carbon Monoxide Alarm and Fire Extinguisher Compliance) is now the <b>CSACMASPSIL</b> (Certificate of Smoke Alarm, Carbon Monoxide Alarm, and Secondary Power Source Identification Label Compliance).</p><p>The Division of Fire Safety told local enforcing agencies to stop enforcing the extinguisher requirement for these certificates. Some older town web pages and the codified regulation text (N.J.A.C. 5:70) still mention extinguishers until they are updated. The law also requires inspections to be done by <b>certified fire inspectors</b>; housing inspectors may keep doing them until Feb 3, 2027.</p><p class="small">Sources: {src("pl2025c19")} · {src("dfs_sps_memo")} · {src("dfs_bulletin_2026")} · {src("fsc_minutes")}</p></section>
<div class="grid2"><section class="card"><h2>What gets checked</h2><ul><li><b>Smoke alarms</b> on each level, outside each separate sleeping area, and as required by the rule for the home's age. Some homes need 10-year sealed-battery alarms when battery-only units are replaced.</li><li><b>Carbon monoxide alarms</b> in the vicinity of sleeping areas if the home has a fuel-burning appliance, fireplace or attached garage.</li><li><b>Secondary power source label</b> at the panel and meter, if the home has one.</li></ul><p class="small">Rule text: {src("njac_5_70_4_19")} · {src("njac_5_70_2_3")}</p></section>
<section class="card"><h2>Who issues it and what it costs</h2><ul><li>Issued by the town's <b>local fire enforcing agency</b> (fire bureau or fire marshal). Where the town has no local agency, the state Division of Fire Safety issues it. Where the town runs its own resale/CO inspection, the town may check alarms as part of that.</li><li><b>Fees in the state rule</b> (where the state or a town without its own fee schedule issues it): <b>$45</b> if requested more than 10 business days before the change of occupancy, <b>$90</b> for 4–10 business days, <b>$161</b> for fewer than 4. Towns that enforce locally can set their own fees by ordinance. See your <a href="{L('/towns/')}">town page</a>.</li><li>Typically valid for <b>6 months</b>. Selling without one can bring a penalty of up to $500 under the rule.</li></ul><p class="small">Sources: {src("njac_5_70_2_9")} · {src("dfs_portal")}</p></section></div>'''
    page("/smoke-co-certificate/", "NJ Smoke & CO Alarm Certificate for Home Sales (2025 Update)", "New Jersey's resale smoke alarm and carbon monoxide certificate: the 2025 law that removed the fire extinguisher requirement, the secondary power source label, fees and who issues it.", b, crumbs=[("Smoke/CO certificate", None)], active="/smoke-co-certificate/")

def lead():
    b = f'''<div class="hero hero-sm"><p class="eyebrow">Federal + NJ</p><h1>Lead paint rules when selling</h1><p class="lead">For a sale, the main lead rule is <b>federal</b>: disclosure for homes built before 1978. New Jersey's 2021 lead inspection law targets <b>rentals</b>, which matters if you rent out a property or are selling a rental.</p><p class="checked">Last checked {CHECKED}</p></div>
<div class="grid2"><section class="card"><h2>Federal disclosure (homes built before 1978)</h2><ul><li>Disclose any <b>known</b> lead-based paint or hazards and give the buyer available records and reports.</li><li>Give the buyer the EPA pamphlet <i>Protect Your Family From Lead in Your Home</i>.</li><li>Include the Lead Warning Statement and signed disclosure in the contract.</li><li>Give the buyer a <b>10-day</b> opportunity to test for lead (they can waive it or agree to a different period).</li><li>Keep the signed acknowledgment for 3 years. Sellers aren't required to test or remove lead.</li></ul><p class="small">Source: {src("epa_lead")}</p></section>
<section class="card"><h2>NJ lead-safe certification (rentals): P.L.2021, c.182</h2><ul><li>Applies to most pre-1978 <b>rental</b> dwellings. It does not apply to owner-occupied homes being sold.</li><li>Municipalities must inspect for lead paint hazards at tenant turnover or within 2 years of the law's effective date (by July 22, 2024), then every 3 years or at turnover, whichever is first.</li><li>Exempt: units built in 1978 or later, units certified lead-free, seasonal rentals under 6 months, and some others listed by DCA.</li><li>If you're selling a rental, confirm its lead-safe certificate status with the town and your attorney.</li></ul><p class="small">Source: {src("dca_lead")}</p></section></div>'''
    page("/lead-paint/", "Lead Paint Rules for NJ Home Sellers (Federal & NJ 2021 Law)", "Federal lead-based paint disclosure rules for selling a pre-1978 home in New Jersey, and how NJ's 2021 rental lead inspection law (P.L.2021, c.182) fits in.", b, crumbs=[("Lead paint", None)])

def timeline():
    steps = [("Before listing (2–6 weeks out)", "Pull your deed, survey, mortgage payoff estimate and any elevation certificate. Look up your <a href=\"" + L("/towns/") + "\">town's resale certificate rules</a> and the fee. Fix obvious smoke/CO alarm issues. Start the Seller's Property Condition Disclosure (flood questions are mandatory)."),
             ("Listing & offers", "Give the buyer the disclosure statement before they're bound by a contract. Add the federal lead disclosure for pre-1978 homes."),
             ("Contract signed → attorney review (3 business days)", "Attorneys review the contract. Either side can cancel during this window. See <a href=\"" + L("/attorney-review/") + "\">attorney review</a>."),
             ("Inspections & mortgage (about 2–6 weeks)", "The buyer's home inspection, any repair negotiation, appraisal and mortgage commitment. Typical NJ contracts set deadlines for each."),
             ("Apply for town certificates (as early as allowed)", "File your town's resale CO/inspection application and the smoke/CO certificate request. Apply more than 10 business days ahead to avoid rush fees. Allow time for re-inspection."),
             ("Title, payoff & final readings (1–2 weeks out)", "The title company clears liens and orders the municipal lien search. Schedule final water/sewer readings if your town requires them. Nonresidents prepare GIT/REP-1."),
             ("Closing", "Sign the deed and the RTF-1 or RTF-1EE if applicable. The transfer fee and GIT/REP payment are collected and the deed is recorded with the county clerk.")]
    lis = "".join(f'<li><div class="dot">{i+1}</div><div><h3>{t}</h3><p>{d}</p></div></li>' for i, (t, d) in enumerate(steps))
    b = f'''<div class="hero hero-sm"><p class="eyebrow">Planning</p><h1>Typical NJ home-sale timeline</h1><p class="lead">Most financed sales in South Jersey close about <b>30–60 days</b> after the contract is signed. Here's the usual order of events from the seller's side. Your contract's dates control.</p></div>
<section class="card"><ol class="timeline">{lis}</ol><p class="small muted">General planning outline, not a legal requirement. Deadlines come from your contract and your town.</p></section>'''
    page("/timeline/", "Typical Timeline for Selling a House in New Jersey", "Step-by-step timeline for selling a home in South Jersey: disclosures, attorney review, inspections, town resale certificates, smoke/CO certificate and closing.", b, crumbs=[("Timeline", None)], active="/timeline/")

def checklist():
    groups = [("Paperwork", ["Deed and survey located", "Mortgage payoff statement requested", "Seller's Property Condition Disclosure Statement completed, including flood questions 109–117", "Elevation certificate (if you have one) ready to give the buyer", "Lead-based paint disclosure + EPA pamphlet (pre-1978 homes)", "Solar lease/PPA documents and installer info (if panels)", "HOA/condo documents and resale certificate (if applicable)"]),
              ("Town & fire certificates", ["Checked my town's page: resale CO / inspection required?", "Applied for the town's resale certificate (fee: ______)", "Requested the smoke/CO alarm certificate from the fire official (apply 10+ business days ahead)", "Smoke alarms tested; CO alarms near sleeping areas", "Secondary power source label at panel and meter (generator/solar/battery homes)", "Re-inspection scheduled if needed", "Final water/sewer reading requested (if required)"]),
              ("Money & closing", ["Estimated Realty Transfer Fee (and Graduated Percent Fee if over $1M)", "RTF-1 if claiming senior/blind/disabled reduced rate", "GIT/REP form chosen (GIT/REP-3 resident, GIT/REP-1 nonresident)", "Property taxes and utilities prorated", "Attorney review completed", "Keys, garage remotes, manuals and warranties gathered"])]
    body = "".join(f'<section class="card ck"><h2>{g}</h2><ul class="checks">' + "".join(f'<li><label><input type="checkbox"> {i}</label></li>' for i in items) + "</ul></section>" for g, items in groups)
    b = f'''<div class="hero hero-sm"><p class="eyebrow">Printable</p><h1>NJ home seller checklist</h1><p class="lead">Print it or tick boxes on screen (saved in this browser only).</p><button class="btn noprint" onclick="window.print()">Print checklist</button></div><div class="grid3">{body}</div>'''
    page("/checklist/", "Printable NJ Home Seller Checklist", "A printable checklist for selling a house in South Jersey: disclosures, town resale certificate, smoke/CO certificate, transfer fees and closing.", b, crumbs=[("Checklist", None)], active="/checklist/")

# ---------------- towns ----------------
def badge(st): return f'<span class="badge b-{st}">{STATUS_LABEL[st]}</span>'
NOTV = "Not yet verified — check with the municipal clerk"

def clerk_link(m):
    if m.get("website"):
        return f'<a href="{e(m["website"]["url"])}" rel="noopener">{e(m["name"])} official website (find the clerk / construction office)</a>'
    return f'No official website is listed for {e(m["name"])} in the state directory. Find the clerk through the {src("njgov_dir","NJ.gov local government directory")} or call the {e(m["county"])} County Clerk.'

def town_page(m):
    v = m["v"]; st = m["status"]; slug = m["slug"]; c = m["county"]
    if v:
        rows = f'''<tr><th>Resale requirement</th><td>{e(v["requirement"])}</td></tr><tr><th>Who issues it</th><td>{e(v["issuer"])}</td></tr><tr><th>Fee</th><td>{e(v["fee"])}</td></tr>'''
        det = "".join(f"<li>{e(d)}</li>" for d in v.get("details", []))
        srcs = "".join(f'<li><a class="src" href="{e(s["url"])}" rel="noopener">{e(s["label"])}</a></li>' for s in v["sources"])
        pnote = f'<p class="warn">Parts of this entry are still <b>{NOTV}</b>: {clerk_link(m)}.</p>' if st == "partial" else ""
        req = f'''<section class="card"><div class="card-h"><h2>Resale certificate / CO requirement</h2>{badge(st)}</div><table class="kv">{rows}</table>{"<ul>"+det+"</ul>" if det else ""}{pnote}<div class="srcbox"><b>Sources</b> <span class="checked">last checked {e(v["checked"])}</span><ul class="sources">{srcs}</ul></div><p class="small muted">Fees and procedures change. Confirm with the town before you schedule your closing.</p></section>'''
    else:
        req = f'''<section class="card"><div class="card-h"><h2>Resale certificate / CO requirement</h2>{badge(st)}</div><div class="notv"><b>{NOTV}.</b><p>We haven't yet confirmed from an official source whether {e(m["name"])} requires a municipal resale certificate of occupancy / resale inspection, or only the state smoke/CO alarm certificate. We won't guess.</p><p>Contact: {clerk_link(m)}</p><p class="small">Every NJ sale of a 1–2 family home still needs the <a href="{L('/smoke-co-certificate/')}">smoke alarm / CO alarm certificate</a> from the local fire official.</p></div></section>'''
    t, q = m.get("tax"), m.get("eq")
    taxrows = ""
    if t:
        taxrows += f'<tr><th>2025 general tax rate</th><td>{t["general_rate"]:.3f} per $100 of assessed value</td></tr><tr><th>2025 effective tax rate</th><td>{t["effective_rate"]:.3f} per $100 of estimated market value</td></tr><tr><th>Example</th><td>A home assessed at $300,000 × {t["general_rate"]:.3f}% ≈ <b>{money(300000*t["general_rate"]/100)}</b>/yr (before any deductions)</td></tr>'
    if q:
        taxrows += f'<tr><th>2026 equalization ratio</th><td>{q["ratio"]:.2f}% (assessments average about {q["ratio"]:.0f}% of market value)</td></tr>'
    eqf = EQFILE.get(c, c)
    taxsec = f'''<section class="card"><div class="card-h"><h2>Property tax &amp; equalization</h2><span class="badge b-verified">Official data</span></div>{'<table class="kv">'+taxrows+'</table>' if taxrows else '<p>'+NOTV+'.</p>'}<div class="srcbox"><b>Sources</b> <span class="checked">last checked {CHECKED}</span><ul class="sources"><li>{src("taxrates","NJ Division of Taxation: 2025 General & Effective Tax Rates (PDF)")}</li><li><a class="src" href="https://www.nj.gov/treasury/taxation/lpt/2026CountyEqualizationTables/2026{eqf.replace(' ','')}.xlsx" rel="noopener">NJ Division of Taxation: 2026 {e(c)} County Equalization Table (XLSX)</a></li></ul></div></section>'''
    fq = f'https://msc.fema.gov/portal/search?AddressQuery={m["name"].replace(" ","%20")}%2C%20NJ'
    flood = f'''<section class="card"><h2>Flood zone</h2><p>Flood zones are set property by property, not town-wide, so look up your exact address. Since March 2024 every NJ seller must answer the flood-risk questions on the disclosure form. See <a href="{L('/disclosures/')}">disclosures</a>.</p><p><a class="btn btn-sm" href="{fq}" rel="noopener">FEMA Flood Map Service Center: {e(m["name"])}</a> <a class="btn btn-sm btn-ghost" href="{SRC["flood_tool"][1]}" rel="noopener">NJ flood risk look-up</a></p></section>'''
    ofl = v.get("official_url") if v else None
    links = []
    if m.get("website"): links.append(f'<li><a href="{e(m["website"]["url"])}" rel="noopener">Official municipal website</a> <span class="small muted">(via NJ.gov directory)</span></li>')
    if ofl: links.append(f'<li><a href="{e(ofl)}" rel="noopener">Official resale / CO page</a></li>')
    links.append(f'<li><a href="{L("/counties/"+cslug(c)+"/")}">All {e(c)} County towns</a></li>')
    lea = m.get("lea"); hist = ""
    if lea:
        hist = f'''<details class="card hist"><summary>Historical reference: 2021 DCA fire-enforcement directory (not used for verification)</summary><p>The NJ Division of Fire Safety's local enforcing agency directory (dated June 2021) listed: enforcement <b>{e(lea.get("enf") or "—")}</b>; smoke/CO certificates issued by <b>{e(lea.get("smoke_name") or "—")}</b> {e(lea.get("smoke_addr") or "")} {e(lea.get("smoke_phone") or "")}. This is several years old and may be out of date, so confirm with the town. {src("lea_dir","Directory PDF")}</p></details>'''
    b = f'''<div class="hero hero-sm"><p class="eyebrow">{e(c)} County · Municipality</p><h1>Selling a house in {e(m["name"])}, NJ</h1><p class="lead">Town-specific resale certificate rules, property tax data and flood look-up for {e(m["name"])}. For statewide rules (transfer fee, disclosures, attorney review) see the guides linked below.</p><div class="hero-meta">{badge(st)}<span class="pill pill-muted">Census GEOID {e(m["geoid"])}</span></div></div>
<div class="grid2 town">{req}{taxsec}{flood}<section class="card"><h2>Links</h2><ul>{"".join(links)}</ul><h3>Statewide rules that also apply</h3><ul class="cols2"><li><a href="{L('/closing-costs/')}">Transfer fee &amp; mansion tax</a></li><li><a href="{L('/smoke-co-certificate/')}">Smoke/CO certificate</a></li><li><a href="{L('/disclosures/')}">Disclosures &amp; flood law</a></li><li><a href="{L('/attorney-review/')}">Attorney review</a></li><li><a href="{L('/lead-paint/')}">Lead paint</a></li><li><a href="{L('/checklist/')}">Checklist</a></li></ul></section></div>{hist}'''
    ld = {"@context": "https://schema.org", "@type": "WebPage", "name": f"Selling a house in {m['name']}, NJ", "about": {"@type": "City", "name": m["name"], "containedInPlace": {"@type": "AdministrativeArea", "name": f"{c} County, New Jersey"}}}
    page(f"/towns/{slug}/", f"Selling a House in {m['name']}, NJ: Resale CO, Fees, Taxes", f"{m['name']} ({c} County, NJ) home seller guide: resale certificate of occupancy / smoke-CO certificate requirements, fees, 2025 tax rate, equalization ratio and flood zone lookup.", b, crumbs=[(c + " County", f"/counties/{cslug(c)}/"), (m["name"], None)], ld=ld)

def card(m):
    return f'<a class="tcard" href="{L("/towns/"+m["slug"]+"/")}" data-name="{e(m["name"].lower())}" data-county="{e(m["county"])}" data-status="{m["status"]}"><b>{e(m["name"])}</b><span>{e(m["county"])} Co.</span>{badge(m["status"])}</a>'

def finder(ms, chips=True):
    cc = "".join(f'<button class="chip" data-f="county" data-v="{e(c)}">{e(c)}</button>' for c in COUNTIES) if chips else ""
    return f'''<div class="finder"><div class="search"><svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2"/><path d="m20 20-4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg><input id="q" type="search" placeholder="Search {len(ms)} towns… e.g. Linwood, Ocean City, Cherry Hill" aria-label="Search towns" autocomplete="off"></div><div class="chips"><button class="chip on" data-f="all" data-v="">All</button>{cc}<button class="chip" data-f="status" data-v="verified">Verified</button><button class="chip" data-f="status" data-v="partial">Partly verified</button></div><p class="small muted" id="count"></p><div class="tgrid" id="tgrid">{"".join(card(m) for m in sorted(ms, key=lambda x: x["name"]))}</div></div>'''

def counts(ms):
    return {s: sum(1 for m in ms if m["status"] == s) for s in ("verified", "partial", "unverified")}

def coverage_table():
    rows = ""
    for c in COUNTIES:
        ms = [m for m in M if m["county"] == c]; k = counts(ms)
        pct = round(100 * (k["verified"] + k["partial"]) / len(ms))
        rows += f'<tr><td><a href="{L("/counties/"+cslug(c)+"/")}">{c}</a></td><td>{len(ms)}</td><td>{k["verified"]}</td><td>{k["partial"]}</td><td>{k["unverified"]}</td><td><div class="bar"><i style="width:{pct}%"></i></div></td></tr>'
    k = counts(M)
    rows += f'<tr class="tot"><td>Total</td><td>{len(M)}</td><td>{k["verified"]}</td><td>{k["partial"]}</td><td>{k["unverified"]}</td><td></td></tr>'
    return f'<table class="t cov"><thead><tr><th>County</th><th>Towns</th><th>Verified</th><th>Partly</th><th>Not yet</th><th>Progress</th></tr></thead><tbody>{rows}</tbody></table>'

def county_pages():
    for c in COUNTIES:
        ms = [m for m in M if m["county"] == c]; k = counts(ms)
        b = f'''<div class="hero hero-sm"><p class="eyebrow">County</p><h1>Selling a house in {c} County, NJ</h1><p class="lead">{len(ms)} municipalities · {k["verified"]} verified · {k["partial"]} partly verified · {k["unverified"]} not yet verified. Pick your town for resale certificate rules, tax data and flood links.</p></div>{finder(ms, chips=False)}'''
        page(f"/counties/{cslug(c)}/", f"Selling a House in {c} County, NJ: Town-by-Town Resale Rules", f"Resale certificate of occupancy, smoke/CO certificate, tax rate and flood info for all {len(ms)} municipalities in {c} County, New Jersey.", b, crumbs=[(c + " County", None)])

def towns_index():
    b = f'''<div class="hero hero-sm"><p class="eyebrow">All 8 counties</p><h1>Find your town</h1><p class="lead">All {len(M)} municipalities in Atlantic, Cape May, Cumberland, Salem, Gloucester, Camden, Burlington and Ocean counties (official Census 2020 list, updated for the 2022 Pine Valley–Pine Hill merger).</p></div>{finder(M)}'''
    page("/towns/", "All South Jersey Towns: Resale CO & Smoke Certificate Rules", "Searchable list of all 201 South Jersey municipalities with resale certificate of occupancy requirements, verification status and sources.", b, crumbs=[("Towns", None)], active="/towns/")

# ---------------- home / about / misc ----------------
# Stylised tile map: rough geographic arrangement of the 8 counties (north at top)
TILES = {"Burlington": "bur", "Camden": "cam", "Gloucester": "glo", "Salem": "sal", "Ocean": "oce", "Atlantic": "atl", "Cumberland": "cum", "Cape May": "cpm"}
def home():
    k = counts(M)
    tiles = ""
    for c in COUNTIES:
        ms = [m for m in M if m["county"] == c]; kk = counts(ms)
        tiles += f'<a class="tile t-{TILES[c]}" href="{L("/counties/"+cslug(c)+"/")}"><b>{c}</b><span>{len(ms)} towns</span><em>{kk["verified"]+kk["partial"]} checked</em></a>'
    feats = [("/closing-costs/", "Closing costs &amp; calculator", "Official Realty Transfer Fee tables, the 2025 seller-paid mansion tax, GIT/REP for nonresidents.", "💲"),
             ("/smoke-co-certificate/", "Smoke/CO certificate", "The 2025 law dropped fire extinguishers and added a secondary-power label. Fees: $45/$90/$161.", "🔥"),
             ("/disclosures/", "Disclosures &amp; flood law", "Mandatory flood-risk questions since March 2024, solar and lead disclosures.", "🌊"),
             ("/attorney-review/", "Attorney review", "Three business days. How they're counted and how to cancel.", "⚖️"),
             ("/lead-paint/", "Lead paint", "Federal pre-1978 disclosure and NJ's rental lead law.", "🎨"),
             ("/timeline/", "Timeline", "From listing to closing: what happens when.", "🗓️"),
             ("/checklist/", "Printable checklist", "Every form and certificate on one page.", "✅")]
    fc = "".join(f'<a class="fcard" href="{L(p)}"><span class="ic" aria-hidden="true">{i}</span><h3>{t}</h3><p>{d}</p></a>' for p, t, d, i in feats)
    b = f'''<section class="hero hero-home"><div class="hero-txt"><p class="eyebrow">Atlantic · Cape May · Cumberland · Salem · Gloucester · Camden · Burlington · Ocean</p><h1>Selling your South Jersey home? <span class="hl">Know every fee, form and inspection</span> before you list.</h1><p class="lead">Free, source-linked guide to New Jersey's seller rules plus town-by-town resale certificate requirements for all {len(M)} municipalities in South Jersey. Every town-specific fact links to an official source with a "last checked" date. If we haven't verified something, we say so.</p><div class="stats"><div><b>{len(M)}</b><span>municipalities</span></div><div><b>{k["verified"]}</b><span>fully verified</span></div><div><b>{k["partial"]}</b><span>partly verified</span></div><div><b>2025</b><span>law changes covered</span></div></div><a class="btn" href="#find">Find your town</a> <a class="btn btn-ghost" href="{L('/closing-costs/')}">Estimate transfer fees</a></div>
<div class="tilemap" aria-label="County map (stylised)">{tiles}<div class="tm-sea" aria-hidden="true">Atlantic Ocean</div><div class="tm-bay" aria-hidden="true">Delaware Bay</div></div></section>
<section class="alert"><b>New in 2025:</b> sellers now pay the graduated "mansion tax" on sales over $1M (effective July 10, 2025), and the resale fire certificate no longer requires a fire extinguisher (effective Feb 3, 2025). <a href="{L('/closing-costs/#mansion')}">Details</a></section>
<h2 class="sec">The statewide rules</h2><div class="fgrid">{fc}</div>
<h2 class="sec" id="find">Find your town</h2>{finder(M)}
<h2 class="sec">Verification coverage</h2><section class="card">{coverage_table()}<p class="small muted">"Verified" means the resale requirement and issuer were confirmed from an official municipal page, the municipal code or an official form. "Partly" means something (often the fee) is still unconfirmed. Atlantic and Cape May were checked first; the other counties are queued. <a href="{L('/about/')}">Method</a>.</p></section>'''
    ld = {"@context": "https://schema.org", "@type": "WebSite", "name": SITE, "url": canon("/"), "description": TAG}
    page("/", SITE, "Free South Jersey house-selling guide: NJ transfer fee and 2025 mansion tax, seller disclosures and flood law, smoke/CO certificate, and resale CO rules for all 201 towns in 8 counties.", b, ld=ld)

def about():
    k = counts(M)
    b = f'''<div class="hero hero-sm"><p class="eyebrow">About</p><h1>Method, coverage &amp; sources</h1><p class="lead">This guide is built to be checked. Nothing town-specific is published without an official source link and a check date.</p></div>
<div class="grid2"><section class="card"><h2>How towns are verified</h2><ul><li><b>Verified</b>: the resale CO/inspection requirement and the issuing office confirmed from the town's own website, its code (eCode360/General Code) or an official application form.</li><li><b>Partly verified</b>: the requirement is sourced, but the fee or another detail isn't published or conflicts between sources.</li><li><b>Not yet verified</b>: no official confirmation yet. The page says "{NOTV}" and links to the town.</li><li>Search-engine summaries, real-estate blogs and third-party lists are never used as sources.</li></ul></section>
<section class="card"><h2>Coverage</h2>{coverage_table()}</section></div>
<section class="card"><h2>Data sources</h2><ul class="sources"><li>{src("census","US Census Bureau 2020 county subdivision list (NJ)")}: the municipality list (Pine Valley merged into Pine Hill in 2022, giving {len(M)} towns).</li><li>{src("taxrates")} and {src("eqtables")}: tax rates and equalization ratios.</li><li>{src("njgov_dir")}: official municipal website links.</li><li>{src("lea_dir")}: historical reference only (2021).</li><li>{src("fema_msc")}: flood maps.</li></ul><h3>Statewide law sources</h3>{srclist(["pl2025c69","gpf_notice","rtf_page","gitrep_faq","njac_11_5_6_2","conley","pl2023c93","pl2023c312","pl2025c19","dfs_sps_memo","njac_5_70_2_3","njac_5_70_2_9","njac_5_70_4_19","dca_lead","epa_lead"])}</section>
<section class="card"><h2>Who made this</h2><p>An independent project. Not affiliated with any government agency, brokerage or law firm. Spot an error or a rule change? Please tell us. Corrections are dated.</p></section>'''
    page("/about/", "About: Method, Coverage & Sources", "How the South Jersey Seller's Guide verifies town resale rules, current coverage, and every official source used.", b, crumbs=[("About", None)])

def notfound():
    page("/404/", "Page not found", "Page not found.", f'<div class="hero hero-sm"><h1>Page not found</h1><p class="lead">Try the <a href="{L("/towns/")}">town list</a> or the <a href="{L("/")}">home page</a>.</p></div>')
    shutil.move(OUT + "/404/index.html", OUT + "/404.html"); os.rmdir(OUT + "/404"); PAGES.remove("/404/")

def main():
    if os.path.exists(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT + "/assets")
    open(OUT + "/assets/style.css", "w").write(CSS)
    tj = json.dumps([[m["slug"], m["name"], m["county"], m["status"]] for m in M])
    open(OUT + "/assets/app.js", "w").write("window.RTF=" + json.dumps(R) + ";\n" + JS)
    shutil.copy("site/gc.js", OUT + "/assets/gc.js")  # self-hosted GoatCounter count.js (ISC)
    open(OUT + "/favicon.svg", "w").write(LOGO.replace('width="30" height="30" aria-hidden="true"', 'xmlns="http://www.w3.org/2000/svg"'))
    open(OUT + "/.nojekyll", "w").write("")
    home(); closing_costs(); attorney(); disclosures(); smoke(); lead(); timeline(); checklist(); towns_index(); about(); county_pages()
    for m in M: town_page(m)
    notfound()
    today = date.today().isoformat()
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"<url><loc>{canon(p)}</loc><lastmod>{today}</lastmod></url>\n" for p in PAGES) + "</urlset>\n"
    open(OUT + "/sitemap.xml", "w").write(sm)
    open(OUT + "/robots.txt", "w").write(f"User-agent: *\nAllow: /\nSitemap: {canon('/sitemap.xml')}\n")
    k = counts(M)
    print(f"Built {len(PAGES)} pages (+404) into {OUT}/ · towns {len(M)} · verified {k['verified']} · partial {k['partial']} · unverified {k['unverified']} · BASE={BASE} PREFIX='{PREFIX}' FORM={'on' if SHOW_FORM else 'off'}")

if __name__ == "__main__":
    main()
