#!/usr/bin/env python3
"""Build the public funding catalog and unsent application drafts.

Facts are limited to the public investor page plus program pages checked on
2026-09-24. This script does not submit anything.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CHECKED = "2026-09-24"

COMPANY = (
    "WisdomTwin, Inc. builds AI Judgment Twins for regulated enterprises. "
    "A Wisdom Twin is role-specific governed judgment, not a cloned person and "
    "not an autonomous employee. A named human remains accountable. The "
    "deployment thesis is on-premises or customer private cloud, and that "
    "boundary is a pilot acceptance target, not a certification already achieved."
)

FACTS = (
    "The company is pre-revenue. Current demonstrations are five founder-built "
    "synthetic scenarios. WisdomTwin is raising USD $1,000,000 through a "
    "proposed post-money SAFE. Cap, discount, and other economic terms are not "
    "stated because they are not agreed. Roman Bodnarchuk is Co-Founder and CEO "
    "in Toronto. Stella Cabrera is Co-Founder, Governance, based in Dubai. "
    "Public pages: https://wisdomtwin.ai/invest and https://wisdomtwin.ai/demo."
)


def row(
    name,
    url,
    apply_url,
    deadline,
    status,
    fit,
    focus,
    geography,
    instrument,
    requirements,
    source,
    action,
    hook,
):
    return {
        "name": name,
        "url": url,
        "apply_url": apply_url,
        "deadline": deadline,
        "status": status,
        "fit_score": fit,
        "focus": focus,
        "geography": geography,
        "instrument": instrument,
        "requirements": requirements,
        "contact_email": None,
        "source_checked": source,
        "action": action,
        "thesis_hook": hook,
    }


# action: review_draft | founder_decision | credits_draft | do_not_apply | reconcile_ledger
P = []

P.append(row(
    "Y Combinator Winter 2027",
    "https://www.ycombinator.com/",
    "https://www.ycombinator.com/apply",
    "2026-11-02T20:00:00-07:00",
    "open_verified",
    4,
    "Broad pre-seed and seed, including AI",
    "In person, San Francisco, January–March 2027",
    "YC standard deal; confirm current terms in the application",
    "Working company. Batch is in person in San Francisco. On-time deadline is 2 November 2026, 8pm PT. Late applications are still read, without a promised decision date.",
    f"{CHECKED} official apply page",
    "review_draft",
    "YC funds companies early and has a long record with AI infrastructure and enterprise software. WisdomTwin is a Delaware company with a built, synthetic product and a regulated-enterprise buyer, which is a plausible W27 profile if the founders can be in San Francisco for the batch.",
))

P.append(row(
    "Techstars Boston Spring 2027",
    "https://www.techstars.com/accelerators/boston",
    "https://www.techstars.com/accelerators/boston",
    "2026-11-18",
    "open_verified",
    5,
    "AI/ML, healthtech, critical infrastructure; industry-agnostic",
    "Boston",
    "Investment terms were not on the program page checked today. Confirm them in the portal before agreeing.",
    "Applications opened 24 August 2026. Final deadline 18 November 2026. Program starts 8 March 2027. Demo Day 3 June 2027.",
    f"{CHECKED} official Boston accelerator page",
    "review_draft",
    "The Boston page names AI/ML and critical infrastructure. That is the buyer set for governed decisions in insurance, health systems, and financial services. One Techstars application should be used if the portal allows Boston and another city together. Do not file two different essays.",
))

P.append(row(
    "NVIDIA Inception",
    "https://www.nvidia.com/en-us/startups/",
    "https://www.nvidia.com/en-us/startups/",
    None,
    "rolling_verified",
    5,
    "AI startups at any funding stage",
    "Worldwide",
    "No program fee and no equity, per the program page. Benefits are tools, training, preferred hardware pricing, and partner offers, not a cash seed round.",
    "No cohort deadline. A pitch deck is requested. Funding status is requested. Incorporation is not a hard blocker on the published FAQ, but WisdomTwin is incorporated.",
    f"{CHECKED} official Inception page excerpt",
    "credits_draft",
    "Private-deployment pilots need GPU capacity. Inception is a non-dilutive infrastructure path, separate from the USD $1M SAFE.",
))

P.append(row(
    "Microsoft for Startups",
    "https://www.microsoft.com/en-us/startups",
    "https://www.microsoft.com/en-us/startups",
    None,
    "rolling_verified",
    4,
    "Startup cloud and AI credits, enterprise go-to-market",
    "Worldwide",
    "Up to USD $150,000 in credits over time, based on Azure use. Not a priced equity round.",
    "Apply on the Microsoft for Startups site. Investor-network members can unlock a higher tier. Do not claim an investor relationship WisdomTwin does not have.",
    f"{CHECKED} official Microsoft for Startups page",
    "credits_draft",
    "Regulated buyers often already run Microsoft identity and cloud. Credits support a private-deployment pilot without treating credits as revenue.",
))

P.append(row(
    "AWS Activate",
    "https://aws.amazon.com/activate/",
    "https://aws.amazon.com/activate/",
    None,
    "rolling_verified",
    4,
    "Cloud credits for early-stage startups",
    "Worldwide",
    "Published ceiling is up to USD $200,000 in Activate Credits. Additional AI credits are described as a later conversation, not an automatic grant.",
    "Founders tier is for early companies without an Activate Provider. Portfolio tier needs a provider organization ID. Use Founders tier unless a provider ID is real.",
    f"{CHECKED} official AWS for Startups page and Activate credits guide",
    "credits_draft",
    "Activate offsets infrastructure cost while the SAFE round is open. It is not a substitute for the round and it is not customer traction.",
))

P.append(row(
    "Google for Startups Cloud, Start tier",
    "https://cloud.google.com/startup",
    "https://cloud.google.com/startup/faq",
    None,
    "rolling_verified",
    3,
    "Cloud credits. AI-first Scale tier is for companies that have already raised",
    "Worldwide",
    "Start tier is for a digital-native startup with an MVP that plans to raise. The up-to-USD $350,000 AI package is for VC-funded Scale startups. Do not apply for that package as if WisdomTwin were already financed.",
    "Needs a Google Cloud billing account ID and a business email on the wisdomtwin.ai domain.",
    f"{CHECKED} official Cloud startup FAQ and AI program page",
    "credits_draft",
    "Start-tier credits can support evaluation infrastructure. The AI Scale tier's funding test is not met: external capital raised is USD $0.",
))

P.append(row(
    "Alchemist Accelerator",
    "https://www.alchemistaccelerator.com/",
    "https://www.alchemistaccelerator.com/apply",
    None,
    "unverified",
    5,
    "Enterprise and deep-tech startups selling to businesses",
    "Silicon Valley, with city cohorts that open and close separately",
    "Terms change by class. Do not reuse an old SAFE amount.",
    "The apply URL responds, but this session did not confirm an open class, a deadline, or current terms. Alchemist Chicago's deadline of 20 August 2026 has passed.",
    f"{CHECKED} apply URL reached; Chicago class page shows a closed deadline",
    "founder_decision",
    "Alchemist is one of the closer thesis matches because it selects enterprise startups. Submit only after the live class, video requirement, and terms are read in a browser.",
))

P.append(row(
    "500 Global Fellowship, Batch 37",
    "https://500.co/founders/flagship",
    "https://500.co/founders/flagship",
    "2026-10-02",
    "founder_decision",
    3,
    "Early-stage founders, four months in San Francisco",
    "San Francisco, 30 November 2026 – 9 April 2027",
    "Page says accepted companies can receive up to USD $50,000 immediately, with more possible later. The same page repeats a Phase 1 program fee of USD $35,000 in several blocks, including placeholder layout text. Treat the fee as unconfirmed until a human reads the live form.",
    "Deadline on the page checked today is 2 October 2026. Founders should be in the U.S. or plan to be within six months.",
    f"{CHECKED} official flagship page. This supersedes any earlier October 11 / USD $150k note.",
    "founder_decision",
    "The residency is a real open window, and the displayed fee may consume a large share of a USD $1M raise. Decide the fee and the San Francisco requirement before anyone pastes an application.",
))

P.append(row(
    "Antler Canada",
    "https://www.antler.co/location/canada",
    "https://www.antler.co/apply?location=CA-TOR",
    None,
    "founder_decision",
    2,
    "Inception-stage residency; also works with teams that have started",
    "Toronto. Residencies start late March and September. Applications are continuous.",
    "The Canada location page currently says USD $250,000 for 9 percent. An older Antler Canada post described USD $150,000 for 10 percent plus a matching facility. Confirm the live term. Either term is a different instrument from the proposed SAFE.",
    "One application at a time across Antler locations. Visa rules apply to the chosen city. WisdomTwin already has two founders and a Delaware corporation, so this is not a co-founder-matching use case.",
    f"{CHECKED} Antler Canada location page and Toronto apply page",
    "founder_decision",
    "Toronto presence is real, but Antler's published check buys a large founding stake. That conflicts with an already-formed company raising a SAFE unless Antler offers a different path in writing.",
))

P.append(row(
    "The Open Accelerator Residency",
    "https://www.redhat.com/en/about/open-accelerator",
    "https://www.redhat.com/en/about/open-accelerator",
    None,
    "unverified",
    4,
    "Early-stage AI for business, open source, enterprise readiness",
    "16 weeks in Boston, next cohort described as starting 1 February 2027",
    "IBM Ventures investment is mentioned by secondary writeups. Amount was not on the pages read here. Do not state an amount.",
    "Secondary sources said the next round opened 15 September 2026 and that founders must be on site four days a week. Confirm the live interest form before relying on that.",
    "Secondary report dated 2026-09-06. Official page not fully re-read this session.",
    "founder_decision",
    "Enterprise AI plus an on-site Boston residency can fit the buyer, and it is a heavy time commitment. Confirm the form is actually open.",
))

# Closed or ineligible — no sendable application
closed = [
    row("Creative Destruction Lab 2026/27", "https://creativedestructionlab.com/", "https://creativedestructionlab.com/application-triage/", "2026-07-24", "closed_verified", 5, "Science and technology ventures; no fees and no equity", "17 locations, including Toronto", "Mentorship. Not a cash seed round.", "Official page says applications for 2026/27 are closed. Earlier streams closed 15 June (Defence) and 21 June (Quantum).", f"{CHECKED} official triage page", "do_not_apply", "Strong Toronto fit. The cycle is closed. Do not send the old unsent inquiry as if the portal were open. Watch the next cycle."),
    row("NEXT AI 2026", "https://www.nextcanada.com/next-ai/", "https://www.nextcanada.com/next-ai/", "2025-12-10", "closed_verified", 4, "AI ventures", "Toronto, Montreal, or remote", "Program and partner perks. Confirm any stipend on the next cycle's page.", "The page still shows a 10 December 2025 deadline. It also requires Canadian incorporation and a distinct technical co-founder. WisdomTwin is a Delaware corporation and that technical-co-founder test is not met.", f"{CHECKED} NEXT AI page excerpt", "do_not_apply", "Do not apply to a closed cohort or certify Canadian incorporation."),
    row("Alchemist Chicago 2026", "https://www.alchemistaccelerator.com/alchemist-chicago", "https://www.alchemistaccelerator.com/alchemist-chicago", "2026-08-20", "closed_verified", 4, "Deep tech", "Chicago bootcamp, then San Francisco for companies that advance", "The closed class page described a USD $50,000 SAFE for startups that advance. That term is not an offer to WisdomTwin.", "Deadline 20 August 2026 has passed.", f"{CHECKED} official Chicago page", "do_not_apply", "Closed. Use the main Alchemist apply decision instead of this class."),
    row("Techstars Founder Catalyst Global Fall 2026", "https://www.techstars.com/techstars-founder-catalyst-global-fall-2026-program", "https://www.techstars.com/techstars-founder-catalyst-global-fall-2026-program", "2026-08-21", "closed_verified", 1, "Pre-accelerator", "Istanbul, Sarajevo, Omaha, Uzbekistan, Belfast only", "Program access, not the core Techstars investment", "Closed 21 August 2026 and limited to those partner cities.", f"{CHECKED} official program page excerpt", "do_not_apply", "Geography and calendar both miss."),
    row("500 Global Eurasia Batch 11", "https://500.co/founders/eurasia/accelerator", "https://500.co/founders/eurasia/accelerator", "2026-08-09", "closed_verified", 1, "Tech startups with operations in listed Eurasian countries", "Eurasia", "Accelerator investment; confirm only if a future batch is open", "Final deadline was 9 August 2026. WisdomTwin does not have the required regional operations.", f"{CHECKED} official Eurasia page excerpt", "do_not_apply", "Closed and geographically ineligible."),
    row("MassChallenge Switzerland 2026", "https://masschallenge.org/programs-switzerland/", "https://masschallenge.org/programs-switzerland/", "2026-03-04", "closed_verified", 2, "Equity-free accelerator", "Switzerland", "No equity, per prior program design. Confirm if a 2027 page appears.", "2026 intake ran 14 January 2026 to 4 March 2026. No 2027 window was published in the 21 September internal check. Re-open only when MassChallenge publishes a date.", "Internal verification 2026-09-21 against the program page. Not re-fetched today.", "do_not_apply", "Closed. Do not file a late application."),
    row("Askya AI Growth Platform 2026", "https://vc4a.com/askya-investment-partners/askya-ai-growth-platform-cohort-2026/", "https://vc4a.com/askya-investment-partners/askya-ai-growth-platform-cohort-2026/", "2026-09-30", "ineligible", 1, "African AI startups with commercial traction", "Africa", "Zero-equity program. Optional later investment up to USD $200,000.", "Requires an African incorporation or primary market, a paying customer or signed pilot, and an African founder or diaspora founder. WisdomTwin does not meet that test.", f"{CHECKED} program listing", "do_not_apply", "Do not apply. Eligibility would be false."),
    row("Tehnopol AI Accelerator", "https://www.tehnopol.ee/en/accelerator/the-ai-accelerator/", "https://www.tehnopol.ee/en/accelerator/the-ai-accelerator/", "2026-09-25", "ineligible", 2, "Early AI teams, equity-free", "Estonia", "Free. A EUR 10,000 grant is competitive, not guaranteed.", "The page is aimed at Estonian businesses and teams that can build a prototype during the program. Deadline 25 September 2026. Do not certify an Estonian operating base.", f"{CHECKED} official page excerpt", "do_not_apply", "Deadline is immediate and the geographic test is not met."),
    row("Oregon AI Accelerator Cohort 2", "https://oregonaix.com/program", "https://oregonaix.com/program", "2026-09-01", "unverified", 2, "Equity-free AI cohort in Portland", "Oregon", "No equity required to participate, per the program page. Optional university IP terms are separate.", "The page both names a 1 September 2026 final deadline and still invites applications. A human must see which banner is current before anyone applies.", f"{CHECKED} program page excerpt, status contradictory", "founder_decision", "Do not apply on a contradictory deadline. Equity-free is attractive only if the cohort is actually open and a Portland commitment is acceptable."),
    row("Entrepreneur First", "https://www.joinef.com/", "https://www.joinef.com/", None, "ineligible", 1, "Talent investor that matches co-founders before a company exists", "Multiple cities", "EF invests in individuals on its own terms.", "WisdomTwin is already incorporated with named co-founders and a product. EF's core path is the wrong stage.", "Program model checked against EF's public description. Current city deadline not re-fetched.", "do_not_apply", "Wrong stage. Do not recast an existing company as an idea-stage individual application."),
    row("NRC IRAP", "https://nrc.canada.ca/en/support-technology-innovation", "https://nrc.canada.ca/en/support-technology-innovation", None, "ineligible", 4, "Non-dilutive R&D support for Canadian SMEs, including AI", "Canada", "Advisory support and project funding. Not a SAFE.", "Requires a for-profit corporation incorporated and operating in Canada, a CRA business number, and Canadian economic benefit. WisdomTwin, Inc. is a Delaware corporation. No Canadian subsidiary is formed.", f"{CHECKED} official IRAP eligibility page", "do_not_apply", "Blocked until a Canadian corporation exists and an Industrial Technology Advisor accepts the file. Do not apply with the Delaware entity."),
    row("NRC IRAP Defence Industry Assist", "https://www.canada.ca/en/national-research-council.html", "https://nrc.canada.ca/en/support-technology-innovation", None, "ineligible", 2, "Advice and funding for Canadian SMEs on dual-use technology", "Canada", "Government program funding, not venture equity.", "Same Canadian-incorporation gate as IRAP. This catalog does not treat WisdomTwin as a defence contractor and does not claim a defence use case.", f"{CHECKED} Government of Canada announcement and IRAP eligibility", "do_not_apply", "Ineligible on entity. Also out of thesis unless the founder later defines a civilian regulated workflow and a Canadian entity."),
    row("CanExport Innovation", "https://www.tradecommissioner.gc.ca/en/our-solutions/funding-financing-international-business/canexport-innovation.html", "https://www.deleguescommerciaux.gc.ca/en/our-solutions/funding-financing-international-business/canexport-innovation/applicant-guide.html", None, "ineligible", 2, "International R&D partnering costs", "Canada", "Reimbursement program for eligible Canadian organizations.", "Requires a Canadian legal entity, CRA business number, and a prototype at the program's stated readiness level, plus a foreign partner. The subsidiary decision is still open.", f"{CHECKED} official applicant guide", "do_not_apply", "Do not apply before a Canadian entity and a real foreign R&D partner exist."),
    row("Innovative Solutions Canada", "https://ised-isde.canada.ca/site/innovative-solutions-canada/en", "https://ised-isde.canada.ca/site/innovative-solutions-canada/en", None, "ineligible", 3, "Government challenge buys from Canadian innovators", "Canada", "Contracts or grants under published challenges.", "Canadian-bidder rules apply to most calls. Check the specific challenge. Do not file a Delaware company as a Canadian bidder.", "Official program home. Individual challenges not opened this session.", "do_not_apply", "Watch for a challenge that matches a governed decision workflow, then confirm bidder eligibility."),
    row("NEXT Canada other than NEXT AI", "https://www.nextcanada.com/", "https://www.nextcanada.com/", None, "unverified", 2, "Founder programs", "Canada", "Program-specific.", "Several NEXT streams require Canadian status, a student or recent-graduate test, or a sector test. Read the specific stream.", "Not re-fetched beyond NEXT AI.", "do_not_apply", "Do not use a generic NEXT application."),
]
P.extend(closed)

# Real programs whose live deadline was not re-opened in this session.
# Drafts are thesis notes, not permission to submit.
watch = [
    ("Techstars accelerator directory", "https://www.techstars.com/accelerators", "https://www.techstars.com/accelerators", "Many city and vertical programs", "Worldwide", "Only Boston Spring 2027 was verified open today. Select another city only inside the same portal if its own dates are open.", 4, "The Boston deadline is the one that is verified. Do not assume NYC or a healthcare track shares it."),
    ("Plug and Play", "https://www.plugandplaytechcenter.com/", "https://www.plugandplaytechcenter.com/", "Corporate innovation programs, often by vertical", "Multiple cities", "Official site has been unreadable to automated checks. A human has to confirm the Fintech or Insurtech program, the date, and whether any fee or equity applies.", 4, "A bank or insurer pilot would match the product. The route is not verified, so this is not ready to paste into a form."),
    ("MassChallenge US", "https://masschallenge.org/", "https://masschallenge.org/", "Equity-free accelerator cohorts", "United States, plus other regions", "Cohorts open and close independently. Switzerland 2026 is closed. Confirm a US cohort page before drafting answers.", 3, "Equity-free mentorship is useful only when a live cohort exists."),
    ("ERA", "https://www.eranyc.com/", "https://www.eranyc.com/", "NYC enterprise and media startup accelerator", "New York", "Historical programs take equity and expect time in New York. Current application state was not re-fetched.", 3, "Enterprise mentors in New York are relevant. Confirm the class is open and the equity ask."),
    ("South Park Commons", "https://www.southparkcommons.com/", "https://www.southparkcommons.com/", "Community for people exploring or starting companies", "San Francisco and New York", "Membership and founder fellowship are selective and usually not a standard SAFE application. Confirm the current call.", 3, "SPC is a community path, not a substitute for the USD $1M round."),
    ("HF0", "https://www.hf0.com/", "https://www.hf0.com/", "In-person residency for technical teams", "San Francisco", "Residency model. Confirm whether WisdomTwin already has an application or conversation before starting another.", 3, "A residency can sharpen the product. It is not automatically compatible with founder-led sales in Toronto and Dubai."),
    ("PearX", "https://pear.vc/", "https://pear.vc/", "Pear's pre-seed program", "Silicon Valley", "Pear publishes occasional X cohorts. The live deadline was not confirmed today.", 3, "Pre-seed software fit is plausible. Apply only to a named open cohort."),
    ("a16z speedrun", "https://speedrun.a16z.com/", "https://speedrun.a16z.com/", "Andreessen Horowitz's company-building program", "Mostly in person", "Terms and dates are cohort-specific. Crypto and games have been prominent; do not assume an enterprise-AI seat.", 2, "Check the current cohort thesis before spending an application. Enterprise governance may be outside the live class."),
    ("Neo", "https://neo.com/", "https://neo.com/", "Mentorship and pre-seed for young technical founders", "United States", "Neo's classic profile is a young technical founder. Do not stretch biographies to fit it.", 2, "Likely poor biographical fit. Read the current criteria before applying."),
    ("Sequoia Arc", "https://www.sequoiacap.com/arc/", "https://www.sequoiacap.com/arc/", "Sequoia company-building program", "United States and Europe cohorts have existed", "Invite-heavy. Public application windows open only sometimes.", 3, "Worth a watch. Do not email partners because a program name exists."),
    ("Accel Atoms", "https://www.accel.com/atoms", "https://www.accel.com/atoms", "Accel pre-seed program", "Programs have run in India, Europe, and elsewhere", "Geography and thesis are cohort-specific. A Toronto regulated-enterprise company may not match the open cohort.", 2, "Confirm the live geography. Do not file a generic Accel application."),
    ("Founder Institute", "https://fi.co/", "https://fi.co/en/toronto", "Pre-seed incubator with local chapters", "Toronto chapter exists", "Fee-based. Equity or warrant terms vary. Confirm Toronto dates and the fee in the chapter page.", 2, "A paid incubator is a founder-budget decision, not free capital."),
    ("Berkeley SkyDeck", "https://skydeck.berkeley.edu/", "https://skydeck.berkeley.edu/", "UC Berkeley accelerator", "Berkeley", "Some pads require a Berkeley affiliate and others have accepted outside teams. Read the current pad.", 3, "Possible if an open pad accepts a non-affiliate. Do not claim a university affiliation."),
    ("Stanford StartX", "https://startx.com/", "https://startx.com/", "Stanford founder community", "Palo Alto", "Requires a Stanford founder or equivalent affiliation under its published rules.", 1, "Ineligible unless a founder actually meets the affiliation rule."),
    ("DMZ", "https://dmz.torontomu.ca/", "https://dmz.torontomu.ca/", "Toronto startup programs", "Toronto", "Programs differ for students, international founders, and growth companies. Confirm the specific intake.", 3, "Toronto location fits. Entity and student rules may not."),
    ("MaRS Discovery District", "https://www.marsdd.com/", "https://www.marsdd.com/", "Advisory, workspace, and venture services", "Toronto", "MaRS is not one application. IAF and related funds have their own Canadian rules.", 3, "Use MaRS as a Toronto relationship, not as a form to mass-submit."),
    ("Communitech", "https://www.communitech.ca/", "https://www.communitech.ca/", "Waterloo Region tech programs", "Kitchener-Waterloo", "Program eligibility often expects a Canadian operating company.", 2, "Relevant ecosystem. Confirm the Canadian-entity test first."),
    ("Velocity", "https://velocityincubator.com/", "https://velocityincubator.com/", "University of Waterloo incubator", "Waterloo", "Student or alumni affiliation is the usual path.", 1, "Do not apply without a real Waterloo affiliation."),
    ("University of Toronto Hatchery and related campus incubators", "https://entrepreneurs.utoronto.ca/", "https://entrepreneurs.utoronto.ca/", "Campus venture support", "Toronto", "Most funds and desks require a U of T founder, student, or faculty lead.", 1, "Do not claim a campus affiliation the company does not have."),
    ("Ontario Centre of Innovation", "https://www.oc-innovation.ca/", "https://www.oc-innovation.ca/", "Ontario R&D and adoption programs", "Ontario", "Calls usually require an Ontario or Canadian company and a partner. The subsidiary is not formed.", 3, "Blocked on entity until the founder decides to incorporate in Canada."),
    ("Invest Ontario and regional funds", "https://www.investontario.ca/", "https://www.investontario.ca/", "Provincial investment attraction", "Ontario", "These are not pre-seed application forms for a Delaware software company.", 1, "Wrong instrument."),
    ("BDC Capital", "https://www.bdc.ca/en/bdc-capital", "https://www.bdc.ca/en/bdc-capital", "Venture capital for Canadian companies", "Canada", "BDC funds Canadian businesses. A Delaware parent with no Canadian subsidiary does not fit the published model.", 3, "Revisit only after a Canadian entity exists and a fund's cheque size matches a USD $1M SAFE."),
    ("Scale AI", "https://www.scaleai.ca/", "https://www.scaleai.ca/", "Canadian AI supply-chain and adoption funding", "Canada", "Project calls require a Canadian consortium and are not a pre-seed SAFE. Eligibility must be read per call.", 3, "Useful later for a paid pilot consortium. Not an application to file this week."),
    ("Alberta Innovates", "https://albertainnovates.ca/", "https://albertainnovates.ca/", "Provincial innovation funding", "Alberta", "Alberta presence is generally required.", 1, "No Alberta operating base."),
    ("Innovate BC", "https://www.innovatebc.ca/", "https://www.innovatebc.ca/", "British Columbia programs", "British Columbia", "BC presence is generally required.", 1, "No BC operating base."),
    ("Prompt", "https://www.promptinnov.com/", "https://www.promptinnov.com/", "Quebec industry-research projects", "Quebec", "Quebec company and research partner are typical requirements.", 1, "No Quebec entity."),
    ("Mila, Vector Institute, and Amii", "https://mila.quebec/", "https://vectorinstitute.ai/", "Research institutes and industry partnerships, not pre-seed funds", "Canada", "Partnership applications are not a USD $1M financing. Do not describe a research membership as an investment.", 2, "Optional technical community later. Not a financing application."),
    ("AI2 Incubator", "https://www.ai2incubator.com/", "https://www.ai2incubator.com/", "AI incubator linked to the Allen Institute", "Seattle", "Selective incubator. Current call not confirmed today.", 3, "Technical AI fit is real. Confirm an open call and any Seattle requirement."),
    ("Dreamit", "https://www.dreamit.com/", "https://www.dreamit.com/", "Health, secure, and urban tech programs have existed", "United States", "Vertical programs open and close. Health or secure-tech would be the only relevant tracks.", 3, "Apply only to a named open vertical. Do not use a stale form."),
    ("SOSV", "https://sosv.com/", "https://sosv.com/", "Multi-program fund: HAX, IndieBio, Orbit", "Global", "HAX and IndieBio are hardware, biology, or climate heavy. A software judgment product is a weak match unless a program page says otherwise.", 2, "Default is poor fit. Read the specific program before applying."),
    ("HAX", "https://hax.co/", "https://hax.co/", "Hard-tech accelerator", "Newark and other sites", "Built for physical products. WisdomTwin is software and deployment architecture.", 1, "Wrong instrument."),
    ("IndieBio", "https://indiebio.co/", "https://indiebio.co/", "Life-science accelerator", "San Francisco and New York programs have existed", "Biology companies. A healthcare workflow demo is not a life-science company.", 1, "Wrong science."),
    ("Boost VC", "https://www.boost.vc/", "https://www.boost.vc/", "Pre-seed, historically crypto, VR, and sci-fi tech", "San Mateo", "Thesis may have moved. Confirm it still wants this category.", 2, "Do not apply on an old crypto-era assumption."),
    ("Pioneer", "https://pioneer.app/", "https://pioneer.app/", "Remote tournament-style pre-seed", "Remote", "Tournament format and small checks. Confirm it is still operating.", 2, "Low cheque and odd format relative to a USD $1M SAFE."),
    ("On Deck", "https://www.beondeck.com/", "https://www.beondeck.com/", "Founder fellowships", "Remote and city chapters", "Fellowships are not financing. Many were paused or changed. Confirm the current product.", 1, "Not a funding application."),
    ("Launch Accelerator", "https://www.launch.co/", "https://www.launch.co/", "Jason Calacanis programs", "United States", "Terms and cohorts change. Confirm a live class.", 2, "Only if a current class clearly accepts enterprise AI."),
    ("Founders, Inc.", "https://f.inc/", "https://f.inc/", "San Francisco builder residency", "San Francisco", "Residency and investment terms must be read on the live site.", 2, "Time-zone and residency cost need a founder decision."),
    ("Berkeley SkyDeck variant pads", "https://skydeck.berkeley.edu/apply/", "https://skydeck.berkeley.edu/apply/", "Pad-specific", "Berkeley and partner sites", "Do not file twice. One SkyDeck decision covers the pads.", 2, "Duplicate of the SkyDeck row. Keep a single application if any pad is open."),
    ("Hub71", "https://www.hub71.com/", "https://www.hub71.com/", "Abu Dhabi incentive program", "Abu Dhabi", "Incentive programs require a real Abu Dhabi presence and license. A Dubai-based co-founder does not by itself qualify the company.", 3, "Possible MENA path only with a license plan. Do not imply Hub71 has accepted WisdomTwin."),
    ("DIFC FinTech Hive", "https://www.difc.ae/fintech", "https://www.difc.ae/fintech", "Financial-services innovation programs", "Dubai", "Cohorts and licenses are specific. Governance experience in Dubai is relevant. A license is not already held.", 3, "Worth a founder look because of the Dubai governance base. Confirm the live cohort and license cost."),
    ("in5", "https://in5.ae/", "https://in5.ae/", "Dubai startup enablement", "Dubai", "Enablement and license paths, not a USD $1M lead.", 2, "A presence tool, not the round."),
    ("startAD", "https://startad.ae/", "https://startad.ae/", "NYU Abu Dhabi startup platform", "Abu Dhabi", "Often expects a program application and local presence.", 2, "Secondary to a license decision."),
    ("Flat6Labs", "https://www.flat6labs.com/", "https://www.flat6labs.com/", "Regional seed programs", "MENA", "City programs have their own funds and ownership terms.", 2, "Confirm a city program that accepts a Delaware parent."),
    ("Station F", "https://stationf.co/", "https://stationf.co/", "Paris campus and partner programs", "Paris", "Programs inside Station F have separate applications and often a French-company expectation.", 2, "No French entity."),
    ("Seedcamp", "https://seedcamp.com/", "https://seedcamp.com/", "European pre-seed and seed", "Europe", "Application or intro. European presence is limited to interest, not an office.", 3, "Possible if they will invest in a Delaware company selling into regulated enterprises. Confirm on their site."),
    ("Entrepreneur First London or other EF cities", "https://www.joinef.com/", "https://www.joinef.com/", "Talent investor", "City-specific", "Same stage mismatch as the main EF row.", 1, "Do not file a second EF application."),
    ("Google for Startups Accelerator cohorts", "https://startup.google.com/", "https://startup.google.com/", "Equity-free cohort programs by region and theme", "Region-specific", "Cloud credits and Accelerator cohorts are different. A cohort must list Canada, the US, or a theme WisdomTwin matches, and it must be open.", 3, "Subscribe to the cohort list. Do not reuse the Cloud credit draft as an Accelerator application."),
    ("Intel Ignite", "https://www.intel.com/content/www/us/en/developer/tools/ignite/overview.html", "https://www.intel.com/content/www/us/en/developer/tools/ignite/overview.html", "Deep-tech accelerator, historically", "Various", "The program has been reported as changed or paused in past years. Confirm it exists before applying.", 2, "Unverified. Do not cite it as an open program."),
    ("SAP.iO", "https://sap.io/", "https://sap.io/", "Enterprise software programs", "Global", "Foundry programs are theme-specific. A regulated workflow that sits beside SAP is the only relevant angle.", 3, "Apply only to a published foundry. Do not claim an SAP customer."),
    ("Salesforce", "https://www.salesforce.com/company/ventures/", "https://www.salesforce.com/company/ventures/", "Venture fund and ISV programs", "Global", "Ventures is not an open pre-seed form. AppExchange and ISV programs are partnerships.", 2, "Partnership later, not this SAFE."),
    ("Cisco Investments and Cisco entrepreneurship programs", "https://www.ciscoinvestments.com/", "https://www.ciscoinvestments.com/", "Corporate venture", "Global", "Usually later or strategic. No open pre-seed form was confirmed.", 2, "Do not cold-email a corporate ventures inbox from this list."),
    ("IBM partner and startup programs", "https://www.ibm.com/partnerplus", "https://www.ibm.com/partnerplus", "Partner technology access", "Global", "Partner programs are not cash financing. The Open Accelerator is the IBM-related residency and is listed separately.", 2, "Use the Open Accelerator decision, not a generic IBM partner form, for the residency question."),
    ("Palantir startup and FedStart programs", "https://www.palantir.com/", "https://www.palantir.com/", "Commercial and government deployment programs", "United States", "These are platform and procurement programs. They are not a pre-seed SAFE. Government work also needs a compliance posture the company has not certified.", 2, "Do not apply for a government vehicle. The product is not certified for one."),
    ("Cohere startup programs", "https://cohere.com/", "https://cohere.com/", "Model provider programs, if offered", "Canada and global", "No partnership exists. Do not mention Cohere as part of the WisdomTwin stack unless a current architecture document says so.", 2, "Credits or research access only, and only if Cohere is actually publishing a program."),
    ("Red Hat and IBM Open Accelerator interest list", "https://www.redhat.com/en/about/open-accelerator", "https://www.redhat.com/en/about/open-accelerator", "Same residency as The Open Accelerator", "Boston", "Duplicate of The Open Accelerator row.", 2, "Keep one application."),
    ("AngelList / Wellfound", "https://wellfound.com/", "https://wellfound.com/", "Syndicate and talent marketplace", "Global", "Not a single fund application. A rollup profile can exist later. It is not 200 investor emails.", 2, "Do not message syndicates in bulk."),
    ("NACO", "https://nacocanada.com/", "https://nacocanada.com/", "Canadian angel-group association", "Canada", "NACO is a directory of groups, not a fund that writes a USD $1M cheque by form.", 3, "Use it to find a specific group, then check that group's rules and the ledger."),
    ("New York Angels", "https://www.newyorkangels.com/", "https://www.newyorkangels.com/investment-process", "Angel network application via its published process", "New York; members have invested outside the US", "Member cheques are individual. The network's published range is not a promise.", 3, "A real apply path exists. Reconcile the ledger before submitting so this is not a second touch."),
    ("Golden Seeds", "https://goldenseeds.com/", "https://goldenseeds.com/", "Angel network", "United States", "Process and gender focus are on their site. Read the current criteria.", 2, "Apply only if the published criteria fit. Do not force a narrative."),
    ("Keiretsu Forum", "https://www.keiretsuforum.com/", "https://www.keiretsuforum.com/", "Angel chapters", "Many chapters, including Canada", "Chapter applications and fees vary. Confirm Toronto or a relevant chapter.", 2, "Fee-based chapters need a founder decision."),
    ("Tech Coast Angels", "https://www.techcoastangels.com/", "https://www.techcoastangels.com/", "Southern California angel network", "Southern California", "Application process is public. Geography of the investors is not Toronto.", 2, "Lower priority than a Toronto or enterprise fund."),
    ("Band of Angels", "https://www.bandangels.com/", "https://www.bandangels.com/", "Silicon Valley angel group", "Silicon Valley", "Screening process. Not a fit unless a member intro exists.", 2, "Warm intro only."),
    ("Alliance of Angels", "https://allianceofangels.com/", "https://allianceofangels.com/", "Seattle angel network", "Seattle", "Published screening process.", 2, "Secondary."),
    ("Maple Leaf Angels", "https://www.mapleleafangels.com/", "https://www.mapleleafangels.com/", "Toronto angel group", "Toronto", "Confirm the group is still screening and whether it accepts a Delaware issuer.", 3, "Toronto relevance is high. Confirm the issuer test and the ledger."),
    ("York Angels", "https://yorkangels.com/", "https://yorkangels.com/", "Toronto-area angel group", "Greater Toronto", "Screening through the group, not a cold partner email.", 3, "Same issuer and ledger checks as other Toronto angels."),
    ("TenX Toronto Angel Group", "https://www.tenxtoronto.com/", "https://www.tenxtoronto.com/", "Toronto angel group", "Toronto", "Confirm it is active.", 2, "Directory lead, not a verified open form."),
    ("Vancouver Angel Forum and related BC groups", "https://www.angelinvestorsforum.com/", "https://www.angelinvestorsforum.com/", "BC angels", "British Columbia", "BC-centric. Low priority without a BC plan.", 1, "Skip unless a member asks."),
    ("37 Angels", "https://www.37angels.com/", "https://www.37angels.com/", "New York angel training network", "New York", "Application windows are periodic.", 2, "Confirm a live window."),
    ("Pipeline Angels", "https://pipelineangels.com/", "https://pipelineangels.com/", "Angel network with a specific founder focus", "United States", "Read the eligibility statement. Do not apply if the founder criteria do not match.", 1, "Criteria first."),
    ("Houston Angel Network", "https://houstonangelnetwork.org/", "https://houstonangelnetwork.org/", "Angel network", "Houston", "Energy and Texas focus is common.", 1, "Weak geography."),
    ("Central Texas Angel Network", "https://ctan.com/", "https://ctan.com/", "Angel network", "Austin", "Texas focus.", 1, "Weak geography."),
    ("Hyde Park Angels", "https://www.hydeparkangels.com/", "https://www.hydeparkangels.com/", "Chicago angels", "Chicago", "Application through the group.", 2, "Secondary to Boston and Toronto."),
    ("Launchpad Venture Group", "https://www.launchpadventuregroup.com/", "https://www.launchpadventuregroup.com/", "Boston angels", "Boston", "Often life-science heavy. Read the current thesis.", 2, "Only if they say enterprise software is in scope."),
    ("Golden Triangle Angel Network", "https://goldentriangleangelnet.ca/", "https://goldentriangleangelnet.ca/", "Southern Ontario angels", "Ontario", "Canadian issuer expectations are likely.", 2, "Check entity rules."),
    ("Capital Angel Network", "https://www.capitalangels.ca/", "https://www.capitalangels.ca/", "Ottawa angels", "Ottawa", "Chapter process.", 2, "Secondary Canadian angel path."),
    ("Angels of Many", "https://www.angelsofmany.com/", "https://www.angelsofmany.com/", "Diversity-focused angel group", "Canada", "Confirm the group is accepting pitches.", 2, "Read the criteria before a draft goes anywhere."),
]
for name, url, apply_url, focus, geography, requirements, fit, hook in watch:
    P.append(row(
        name, url, apply_url, None, "unverified", fit, focus, geography,
        "Not a confirmed open cheque. Read the live page.",
        requirements, "Listed from the organization's public site. Deadline not verified in this session.",
        "founder_decision", hook,
    ))

funds = [
    ("Panache Ventures", "https://panache.vc/", "Canada, including Toronto", "Publishes a pitch route and writes first cheques.", 5),
    ("Ripple Ventures", "https://rippleventures.com/", "Canada and the US", "Early cheques; financial, health, and legal technology have been in scope.", 5),
    ("Golden Ventures", "https://golden.ventures/", "North America", "Pre-seed and seed.", 4),
    ("Graphite Ventures", "https://graphitevc.com/", "Toronto", "Canadian B2B.", 4),
    ("Mistral Venture Partners", "https://www.mistral.vc/", "Toronto", "Pre-seed and seed enterprise software. Not Mistral AI.", 4),
    ("Radical Ventures", "https://radical.vc/", "Toronto", "AI fund. Cheque size may be larger than a first USD $1M SAFE.", 4),
    ("Inovia Capital", "https://www.inovia.capital/", "Canada", "Multi-stage. Pre-seed fit must be checked on the current fund.", 3),
    ("Georgian", "https://georgian.io/", "Toronto", "Growth-stage software. Poor fit for a pre-revenue SAFE.", 1),
    ("Version One Ventures", "https://versionone.vc/", "Vancouver and San Francisco", "Pre-seed and seed software.", 3),
    ("Two Small Fish Ventures", "https://twosmallfish.vc/", "Toronto", "Deep-tech and software seed.", 3),
    ("Luge Capital", "https://luge.capital/", "Montreal", "Financial-services technology.", 4),
    ("Impression Ventures", "https://impression.ventures/", "Toronto", "Financial-services technology.", 4),
    ("Framework Venture Partners", "https://framework.vc/", "Toronto", "Enterprise and security seed.", 4),
    ("Whitecap Venture Partners", "https://www.whitecapvp.com/", "Toronto", "B2B software.", 3),
    ("Relay Ventures", "https://relay.vc/", "Toronto", "Mobile and software seed. Confirm the fund is still deploying.", 2),
    ("Flying Fish Ventures", "https://flyingfish.vc/", "Seattle", "AI and enterprise seed.", 3),
    ("Glasswing Ventures", "https://glasswing.vc/", "Boston", "AI enterprise seed.", 4),
    ("Precursor Ventures", "https://precursorvc.com/", "San Francisco", "Pre-seed. Often the first institutional cheque.", 4),
    ("Hustle Fund", "https://www.hustlefund.vc/", "United States", "Pre-seed. Publishes a pitch process.", 3),
    ("First Round Capital", "https://firstround.com/", "United States", "Seed. Usually intro or a published pitch path, not a cold blast.", 3),
    ("NFX", "https://www.nfx.com/", "San Francisco", "Network and marketplace focus is narrower than regulated enterprise.", 2),
    ("Khosla Ventures", "https://www.khoslaventures.com/", "Menlo Park", "Reported Viven backer. Large fund. Warm intro only.", 3),
    ("Foundation Capital", "https://foundationcapital.com/", "Silicon Valley", "Reported Viven backer. Warm intro only.", 3),
    ("FPV Ventures", "https://www.fpvventures.com/", "United States", "Reported Viven backer. Confirm the site and a partner before any note.", 3),
    ("Operator Collective", "https://operatorcollective.com/", "United States", "Operator-LP fund. Community path, not a public form to spam.", 3),
    ("Bessemer Venture Partners", "https://www.bvp.com/", "Global", "Reported Twin1 investor. Usually later than pre-seed.", 2),
    ("Greylock", "https://greylock.com/", "Silicon Valley", "Seed and Series A. Intro-only.", 2),
    ("Felicis", "https://felicis.com/", "Menlo Park", "Seed and growth. Intro-only.", 2),
    ("Amplify Partners", "https://www.amplifypartners.com/", "Menlo Park", "Technical infrastructure seed.", 3),
    ("Conviction", "https://www.conviction.com/", "San Francisco", "AI fund. Intro or published process only.", 3),
    ("Decibel", "https://www.decibel.vc/", "Silicon Valley", "Enterprise seed. Often intro-only.", 3),
    ("Unusual Ventures", "https://unusual.vc/", "Silicon Valley", "Company-building seed.", 3),
    ("Root Ventures", "https://root.vc/", "San Francisco", "Technical pre-seed.", 3),
    ("Heavybit", "https://www.heavybit.com/", "San Francisco", "Developer-tool community and seed. Weak fit unless the product is clearly developer infrastructure.", 2),
    ("Work-Bench", "https://work-bench.com/", "New York", "Enterprise seed.", 4),
    ("Bloomberg Beta", "https://www.bloombergbeta.com/", "San Francisco", "Early, future-of-work angle. Intro-oriented.", 3),
    ("Govtech Fund", "https://govtechfund.com/", "United States", "Government technology. Only relevant if a civilian public-sector workflow is real.", 2),
    ("Shield Capital", "https://shieldcap.com/", "United States", "National-security fund. Do not pitch a defence product the company is not building.", 1),
    ("Lux Capital", "https://www.luxcapital.com/", "New York", "Deep tech. Intro-only and often later.", 2),
    ("DCVC", "https://www.dcvc.com/", "Silicon Valley", "Deep tech. Reported around decision-infrastructure companies. Intro-only.", 3),
    ("Air Street Capital", "https://www.airstreet.com/", "London", "AI fund.", 3),
    ("Focal VC", "https://focal.vc/", "Canada", "Canadian early-stage. Confirm current deployment.", 3),
    ("Forum Ventures", "https://forumvc.com/", "New York and Toronto", "B2B pre-seed programs.", 4),
    ("Highline Beta", "https://highlinebeta.com/", "Toronto", "Venture studio and partnerships.", 3),
    ("Diagram", "https://diagram.com/", "Toronto", "Venture studio. A studio relationship is not a SAFE subscription.", 2),
    ("Intact Ventures", "https://www.intactfc.com/", "Canada", "Insurance corporate venture. Strategic, not an open pre-seed form.", 3),
    ("Thomson Reuters Ventures", "https://www.thomsonreuters.com/en/ventures.html", "Toronto and global", "Information-market corporate venture.", 3),
    ("TELUS Pollinator Fund", "https://www.telus.com/en/pollinatorfund", "Canada", "Impact and health. Thesis must match a published call.", 2),
    ("Portage", "https://www.portageinvest.com/", "Montreal and global", "Financial-services venture. Often later than pre-revenue.", 2),
    ("Wittington Ventures", "https://www.wittingtonventures.com/", "Toronto", "Growth and venture. Cheque size may not fit.", 1),
    ("Real Ventures", "https://realventures.com/", "Montreal", "Fund status has changed in public reporting. Confirm it is deploying before any contact.", 1),
    ("Yaletown Partners", "https://www.yaletown.com/", "Vancouver", "Later-stage technology.", 1),
    ("BDC Seed Venture Fund", "https://www.bdc.ca/en/bdc-capital/funds/seed-venture-fund", "Canada", "Canadian seed fund. Same Canadian-company issue as BDC Capital.", 2),
    ("Export Development Canada", "https://www.edc.ca/", "Canada", "Trade finance for Canadian exporters, not a pre-seed SAFE.", 1),
    ("CDPQ and other pension growth arms", "https://www.cdpq.com/", "Quebec", "Not a pre-seed application.", 1),
    ("RBC and other bank innovation arms", "https://www.rbc.com/", "Canada", "Bank ventures and labs are partnership conversations, not an open form.", 2),
    ("Manulife Ventures", "https://www.manulife.com/", "Canada", "Strategic insurance capital. No open pre-seed form confirmed.", 2),
    ("Sun Life Ventures", "https://www.sunlife.com/", "Canada", "Strategic. No open pre-seed form confirmed.", 2),
    ("CIBC Innovation Banking", "https://www.cibc.com/", "Canada", "Venture debt, not a pre-seed equity application.", 1),
]
for name, url, geography, focus, fit in funds:
    P.append(row(
        name,
        url,
        url,
        None,
        "hold_reconcile",
        fit,
        focus,
        geography,
        "Do not treat a website as permission to email the firm.",
        "The private investor execution ledger already tracks many of these firms, including holds and existing threads. This public list intentionally has no personal emails.",
        "Public firm site. Ledger reconciliation required before any new draft is sent. Ledger contents were not copied here.",
        "reconcile_ledger",
        "Relevant only after the founder confirms there is no existing thread and the current fund still writes pre-seed cheques.",
    ))

def application_text(item: dict) -> str:
    banner = (
        "DRAFT ONLY. NOT SUBMITTED. NOT APPROVED FOR SENDING.\n"
        "This text does not certify eligibility, revenue, customers, or SAFE terms.\n\n"
    )
    header = f"To: {item['name']}\nRoute: {item['apply_url']}\n\n"
    if item["action"] == "do_not_apply":
        body = (
            f"{item['thesis_hook']}\n\n"
            f"Status: {item['status']}. Deadline recorded: {item['deadline'] or 'none'}.\n"
            f"Requirement that blocks a filing: {item['requirements']}\n\n"
            "No email and no form should be sent for this row."
        )
    elif item["action"] == "reconcile_ledger":
        body = (
            f"{item['thesis_hook']}\n\n"
            "No pitch is included. The private execution ledger is the authority on "
            "whether this firm has already been contacted. If a hold or an existing "
            "thread is present, do not open a new one. If the ledger is clear, the "
            "founder can ask for a separate short note that uses only the public facts "
            "below.\n\n"
            f"{COMPANY}\n\n{FACTS}"
        )
    elif item["action"] == "credits_draft":
        body = (
            f"{item['thesis_hook']}\n\n"
            f"{COMPANY}\n\n{FACTS}\n\n"
            "Request: program credits or technical benefits only. This is not an "
            "application for equity investment and it does not ask the program to lead "
            "the SAFE. We will use any credits for evaluation infrastructure inside a "
            "customer-approved boundary. We will not describe credits as revenue.\n\n"
            f"Please use the official route: {item['apply_url']}\n"
            "Deck and demo links are on https://wisdomtwin.ai/invest and "
            "https://wisdomtwin.ai/demo."
        )
    else:
        body = (
            f"{item['thesis_hook']}\n\n"
            f"{COMPANY}\n\n{FACTS}\n\n"
            "What we are asking from this program, if the live terms fit: a place in "
            "the current cohort or a first conversation about the USD $1,000,000 "
            "pre-seed. We are not asking the reader to accept a valuation cap, a "
            "discount, or an in-person move that the founder has not approved.\n\n"
            f"Published constraint to check before pasting: {item['requirements']}\n\n"
            "Roman Bodnarchuk can walk through the synthetic before-and-after demo. "
            "Nothing in this draft has been submitted."
        )
    instructions = (
        f"Open {item['apply_url']} in a browser. "
        "Confirm the deadline, eligibility, and terms on that page. "
        "Paste only if they still match this row. "
        "Do not submit from an agent."
    )
    return {
        "opportunity_name": item["name"],
        "full_text_application": banner + header + body,
        "submit_instructions": instructions,
    }


def main() -> None:
    # Drop exact URL duplicates, keeping the first (usually the verified row).
    seen = set()
    unique = []
    for item in P:
        key = (item["name"], item["url"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)

    ranked = sorted(unique, key=lambda x: (-x["fit_score"], x["name"]))
    actionable = sorted(
        [i for i in unique if i["action"] in {"review_draft", "credits_draft", "founder_decision"}],
        key=lambda i: (
            0 if i["status"] in {"open_verified", "rolling_verified"} else 1,
            -i["fit_score"],
            i["name"],
        ),
    )
    top = []
    for item in actionable:
        if item["name"] in {t["name"] for t in top}:
            continue
        top.append({
            "name": item["name"],
            "url": item["apply_url"],
            "deadline": item["deadline"],
            "status": item["status"],
            "fit_score": item["fit_score"],
        })
        if len(top) == 10:
            break

    catalog = {
        "research_summary": {
            "as_of": CHECKED,
            "total_found": len(unique),
            "open_or_rolling_verified": sum(1 for i in unique if i["status"] in {"open_verified", "rolling_verified"}),
            "closed_or_ineligible": sum(1 for i in unique if i["status"] in {"closed_verified", "ineligible"}),
            "unverified_or_founder_decision": sum(1 for i in unique if i["status"] in {"unverified", "founder_decision"}),
            "ledger_hold_no_email": sum(1 for i in unique if i["action"] == "reconcile_ledger"),
            "submitted": 0,
            "top_10": top,
            "method": (
                "Official pages were fetched for YC, Techstars Boston, 500 Global Fellowship, "
                "CDL, NVIDIA Inception, Microsoft for Startups, AWS Activate, Google for Startups Cloud, "
                "Antler Canada, NEXT AI, Alchemist Chicago, and the IRAP eligibility rules. "
                "Other rows are real organizations whose current deadline was not re-verified today. "
                "Personal emails and the private execution ledger were not copied into this public repository."
            ),
        },
        "full_list": [
            {
                "name": i["name"],
                "url": i["url"],
                "apply_url": i["apply_url"],
                "deadline": i["deadline"],
                "status": i["status"],
                "fit_score": i["fit_score"],
                "focus": i["focus"],
                "geography": i["geography"],
                "instrument": i["instrument"],
                "requirements": i["requirements"],
                "contact_email": None,
                "action": i["action"],
                "source_checked": i["source_checked"],
            }
            for i in ranked
        ],
        "applications": [application_text(i) for i in ranked],
    }

    (ROOT / "funding-catalog.json").write_text(json.dumps(catalog, indent=2), encoding="utf-8")

    lines = [
        "# WisdomTwin funding research",
        "",
        f"As of {CHECKED}. Nothing in this folder was submitted.",
        "",
        f"Rows: {len(unique)}. Verified open or rolling: {catalog['research_summary']['open_or_rolling_verified']}. Closed or ineligible: {catalog['research_summary']['closed_or_ineligible']}. Ledger firms listed without emails: {catalog['research_summary']['ledger_hold_no_email']}.",
        "",
        "The private Drive ledger remains the authority for direct investor contact. This file does not authorize a send.",
        "",
        "## Top reviews",
        "",
    ]
    for item in top:
        lines.append(f"- {item['name']} — {item['status']} — fit {item['fit_score']} — {item['deadline'] or 'no fixed deadline'} — {item['url']}")
    lines.append("")
    lines.append("Full rows and drafts: `funding-catalog.json` and `applications.md`.")
    (ROOT / "research-summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    apps = ["# Draft applications", "", "Each block is unsent. Confirm the live page before pasting.", ""]
    for app in catalog["applications"]:
        apps.append(f"## {app['opportunity_name']}")
        apps.append("")
        apps.append("```text")
        apps.append(app["full_text_application"].rstrip())
        apps.append("```")
        apps.append("")
        apps.append(app["submit_instructions"])
        apps.append("")
    (ROOT / "applications.md").write_text("\n".join(apps), encoding="utf-8")
    print(json.dumps(catalog["research_summary"], indent=2))


if __name__ == "__main__":
    main()
