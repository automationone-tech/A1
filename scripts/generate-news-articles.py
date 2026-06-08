#!/usr/bin/env python3
"""Generate full Latest News article pages from the hub template."""
from __future__ import annotations

import re
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "automation-one-latest-news.html"

ARTICLE_CSS = """
/* ---------- News article pages ---------- */
body.news-article-page {
  background:
    radial-gradient(88% 72% at 82% 0%, rgba(31, 92, 245, 0.14) 0%, transparent 58%),
    linear-gradient(180deg, #f8faff 0%, #eef4ff 100%);
}
body.news-article-page .subpage-hero {
  min-height: clamp(360px, 52vh, 520px);
  overflow: hidden;
}
.news-article-hero-card {
  position: relative;
  z-index: 2;
  max-width: 920px;
  padding: clamp(28px, 5vw, 48px) 0 clamp(36px, 6vw, 56px);
}
.news-article-brand-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 52px;
  margin-bottom: 18px;
  padding: 10px 20px;
  border: 1px solid rgba(31, 92, 245, 0.22);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 12px 28px -18px rgba(10, 40, 112, 0.35);
}
.news-article-hero-logo {
  display: block;
  width: auto;
  object-fit: contain;
}
.news-article-brand-pill[data-brand="canon"] .news-article-hero-logo { max-height: 34px; max-width: 96px; }
.news-article-brand-pill[data-brand="xerox"] .news-article-hero-logo { max-height: 30px; max-width: 88px; }
.news-article-brand-pill[data-brand="lexmark"] .news-article-hero-logo { max-height: 34px; max-width: 104px; }
.news-article-brand-pill[data-brand="fp"] .news-article-hero-logo { max-height: 36px; max-width: 58px; }
.news-article-brand-pill[data-brand="ideal"] .news-article-hero-logo { max-height: 36px; max-width: 94px; }
.news-article-brand-pill[data-brand="more"] .news-article-hero-logo { max-height: 38px; max-width: 38px; }
.news-article-hero-card h1 {
  color: var(--blue-900);
  font-family: var(--font-display);
  font-size: clamp(38px, 5.6vw, 72px);
  line-height: 0.98;
  letter-spacing: -0.055em;
  max-width: 900px;
}
.news-article-hero-card h1 em { color: var(--blue-500); font-style: italic; }
.news-date {
  flex: 0 0 100%;
  color: var(--ink-soft);
  font-size: 13px;
  font-weight: 650;
  letter-spacing: 0.02em;
}
.news-article-date {
  margin-top: 14px;
  color: rgba(255, 255, 255, 0.88);
  font-size: 14px;
  font-weight: 650;
  letter-spacing: 0.02em;
}
.news-article-return { margin-top: 24px; }
.news-article-shell { padding: clamp(28px, 5vw, 56px) 0 clamp(48px, 8vw, 88px); }
.news-article {
  border: 1px solid rgba(15, 56, 158, 0.12);
  border-radius: 28px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 24px 70px -48px rgba(10, 40, 112, 0.55);
}
.news-article-photo {
  position: relative;
  min-height: clamp(220px, 32vw, 360px);
  background:
    radial-gradient(72% 80% at 16% 18%, rgba(31, 92, 245, 0.18), transparent 62%),
    linear-gradient(135deg, #eef4ff, #ffffff);
}
.news-article-photo img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  padding: clamp(22px, 4vw, 46px);
  filter: drop-shadow(0 28px 44px rgba(6, 26, 74, 0.18));
}
.news-article-body { padding: clamp(28px, 4vw, 52px); }
.news-article-lead {
  margin-top: 18px;
  color: var(--ink-soft);
  font-size: clamp(18px, 2vw, 22px);
  line-height: 1.5;
  max-width: 780px;
}
.news-article-body h2 {
  margin-top: 32px;
  margin-bottom: 12px;
  color: var(--blue-900);
  font-family: var(--font-display);
  font-size: clamp(26px, 3vw, 36px);
  letter-spacing: -0.04em;
  line-height: 1.05;
}
.news-article-body p {
  color: var(--ink-soft);
  font-size: 17px;
  line-height: 1.62;
  max-width: 760px;
}
.news-article-body p + p { margin-top: 14px; }
.news-article-body ul {
  margin-top: 14px;
  padding-left: 22px;
  max-width: 760px;
  color: var(--ink-soft);
  font-size: 17px;
  line-height: 1.58;
}
.news-article-body li + li { margin-top: 8px; }
.news-article .news-read-full { margin-top: 0; }
"""

ARTICLES = [
    {
        "slug": "canon",
        "filename": "automation-one-latest-news-canon.html",
        "path": "/latest-news/canon",
        "title": "Canon Smart Service and imageFORCE Expansion | Automation One",
        "description": "Full briefing on Canon Smart Support Chat, imageFORCE A3 expansion, and what AI-assisted MFP service means for BC offices.",
        "kicker": "Canon",
        "headline": 'Canon is pushing the office MFP from hardware into <em>smarter service.</em>',
        "image": "canon-imageforce-c3150-front.png",
        "image_alt": "Canon imageFORCE office printer",
        "pills": ["Canon", "AI support", "imageFORCE"],
        "lead": "Canon's latest office story is twofold: new imageFORCE A3 devices for dealers and customers, plus AI-assisted support tools that help technicians diagnose and resolve printer issues faster.",
        "sections": [
            {
                "h2": "Smart Support Chat changes how service teams work",
                "paragraphs": [
                    "Canon launched Smart Support Chat, an AI-based support system for office multifunction device maintenance. The platform is designed to help field technicians and call-center staff resolve printer issues faster by combining device operating data, manuals, parts information, and remote panel access in one guided workflow.",
                    "Rather than treating every service call as a blank slate, the system gives technicians context before they arrive on site or while they are on the phone with a customer. That matters in busy offices where downtime on a core MFP can stall billing, client service, or internal approvals.",
                    "Canon has indicated expansion into the U.S. and Japan in 2026, which signals that this is not a pilot feature but part of a broader service strategy for office fleets.",
                ],
            },
            {
                "h2": "imageFORCE expansion strengthens the A3 lineup",
                "paragraphs": [
                    "Alongside the service story, Canon U.S.A. expanded the imageFORCE lineup with the C3100 and 4100 Series A3 multifunction printers. These devices target offices that need durable A3 capability, stronger workflow features, and a platform dealers can standardize around.",
                    "For customers comparing Canon against Xerox or Lexmark in the same office segment, the practical question is no longer only print speed. It is how well the device fits managed service, security expectations, and the software stack around scanning and document routing.",
                ],
            },
            {
                "h2": "What BC customers should watch",
                "paragraphs": [
                    "If you already run Canon devices, the direction is clear: uptime, remote visibility, and service responsiveness are becoming part of the product value. That is good news for offices with mixed fleets, satellite locations, or limited internal IT support.",
                    "If you are evaluating a replacement cycle, ask your dealer how Smart Support Chat will affect response times, remote diagnostics, and preventive maintenance. The hardware still matters, but the service layer around it is now part of the buying decision.",
                ],
            },
        ],
        "why": "For customers, the value of an office fleet is increasingly tied to uptime, remote service visibility, energy efficiency, and workflow software  -  not just pages per minute.",
        "sources": [
            ("Canon Smart Support Chat", "https://global.canon/en/news/2026/20260206.html"),
            ("imageFORCE expansion", "https://www.printing.org/content/2026/06/04/canon-u.s.a.--inc.-expands-imageforce-lineup-with-the-launch-of-imageforce-c3100-and-4100-series-a3-multifunction-printers"),
        ],
    },
    {
        "slug": "xerox",
        "filename": "automation-one-latest-news-xerox.html",
        "path": "/latest-news/xerox",
        "title": "Xerox AI and Managed IT Services | Automation One",
        "description": "Full briefing on Xerox IT as a Service, Quocirca AI leadership, and the post-Lexmark workplace platform strategy.",
        "kicker": "Xerox",
        "headline": 'Xerox is leaning hard into <em>AI-enabled workplace services.</em>',
        "image": "xerox-altalink-c8230-main-transparent.png",
        "image_alt": "Xerox AltaLink multifunction printer",
        "pills": ["Xerox", "AI", "Managed IT"],
        "lead": "Xerox's 2026 news centers on the company becoming a services-led, software-enabled workplace technology provider, while broadening its portfolio after the Lexmark acquisition.",
        "sections": [
            {
                "h2": "Xerox IT as a Service broadens the offer",
                "paragraphs": [
                    "Xerox launched Xerox IT as a Service, an AI-powered ServiceNow platform aimed at SMB and mid-market technology operations. The move is significant because it positions Xerox as more than a print vendor: it is packaging help-desk style operations, workflow tooling, and managed support into a recurring service model.",
                    "For offices that already depend on Xerox for devices and managed print, this creates a natural upsell path into broader workplace technology management. For buyers comparing vendors, it raises a new question: can one partner cover print, IT operations, and workflow automation without fragmenting support?",
                ],
            },
            {
                "h2": "Analyst recognition reinforces the software story",
                "paragraphs": [
                    "Quocirca named Xerox a leader in its 2026 AI and ACT assessments, citing workflow automation, cloud integration, and ecosystem strength. That matters because analyst framing increasingly treats print vendors as workflow platforms, not hardware suppliers.",
                    "The recognition aligns with Xerox's public messaging around document intelligence, cloud collaboration, and AI-assisted operations. Customers evaluating AltaLink or PrimeLink devices should weigh software compatibility and managed services alongside device specs.",
                ],
            },
            {
                "h2": "Lexmark integration is part of the platform play",
                "paragraphs": [
                    "Xerox is also integrating Lexmark devices and software into a broader print and managed services portfolio. That reduces the risk of a mixed-environment buyer feeling forced to choose one brand for every floor and every department.",
                    "The combined story is a workplace stack: devices, service, software, and now managed IT. For BC businesses, the practical takeaway is to evaluate total support coverage, not just the box on the spec sheet.",
                ],
            },
        ],
        "why": "The Xerox story is moving beyond print alone: managed IT, AI workflow, document intelligence, and device fleet service are becoming part of one workplace stack.",
        "sources": [
            ("Xerox IT as a Service", "https://investors.xerox.com/news-releases/news-release-details/xerox-launches-xerox-it-service-help-simplify-technology-reduce"),
            ("Quocirca AI Leader", "https://www.news.xerox.com/news/xerox-named-a-leader-in-quocirca-ai-vendor-landscape-2026-report"),
        ],
    },
    {
        "slug": "lexmark",
        "filename": "automation-one-latest-news-lexmark.html",
        "path": "/latest-news/lexmark",
        "title": "Lexmark and Xerox Portfolio Integration | Automation One",
        "description": "Full briefing on the Xerox-Lexmark acquisition, unified A3 portfolio, and what integration means for mixed fleets.",
        "kicker": "Lexmark",
        "headline": "Lexmark's latest chapter is about <em>scale and integration.</em>",
        "image": "lexmark-office-printer.png",
        "image_alt": "Lexmark office printer",
        "pills": ["Lexmark", "Xerox integration", "A3 portfolio"],
        "lead": "After Xerox completed its Lexmark acquisition in 2025, the combined company has moved quickly to align portfolios, sales motions, and software compatibility.",
        "sections": [
            {
                "h2": "Acquisition creates scale in managed print",
                "paragraphs": [
                    "Xerox completed its acquisition of Lexmark in 2025, positioning the combined company among the top five players in major print segments and strengthening managed print services capacity. Scale matters because large fleets need consistent supplies logistics, service coverage, and software support across regions.",
                    "For Lexmark customers, the immediate concern is continuity: device support, supplies, and service contracts. Early integration messaging has focused on keeping Lexmark's A3 strengths while folding go-to-market and software tooling into Xerox's broader platform.",
                ],
            },
            {
                "h2": "Unified A3 portfolio simplifies buying",
                "paragraphs": [
                    "Lexmark's 9-Series A3 printers and MFPs are being made available through Xerox sellers in a unified market approach. That gives buyers a wider set of options under one commercial relationship, which can simplify procurement for organizations standardizing on a single dealer partner.",
                    "Lexmark devices are also being tied into Xerox Managed Print Services, Easy Assist, Print & Scan Experience, App Gallery, ConnectKey apps, and Workflow Central. The goal is to make mixed-brand environments easier to operate, not harder.",
                ],
            },
            {
                "h2": "What mixed fleets should plan for",
                "paragraphs": [
                    "If your office already runs Lexmark alongside Xerox or other brands, the integration story is mostly about software and service alignment. Ask how device monitoring, user experience, and app deployment will work across both product lines.",
                    "If you are mid-cycle on a Lexmark refresh, compare not only device performance but also the long-term support path under the combined company. The hardware may look familiar; the service and software wrapper is what is changing.",
                ],
            },
        ],
        "why": "For buyers, the practical question becomes compatibility: mixed Xerox and Lexmark environments are being positioned as easier to manage under one service and workflow model.",
        "sources": [
            ("Acquisition completed", "https://www.businesswire.com/news/home/20250630740275/en/Xerox-Completes-the-Acquisition-of-Lexmark-Uniting-Two-Industry-Leaders"),
            ("Unified A3 portfolio", "https://news.xerox.co.uk/news/releases-20260302"),
        ],
    },
    {
        "slug": "fp",
        "filename": "automation-one-latest-news-fp.html",
        "path": "/latest-news/fp",
        "title": "FP Mailing and Digital Business Solutions | Automation One",
        "description": "Full briefing on FP mailing, shipping, dealer tools, and 2026 mailroom modernization direction.",
        "kicker": "FP",
        "headline": 'FP is narrowing focus around <em>mailing, shipping, and digital process automation.</em>',
        "image": "postbase-mailing-solutions.png",
        "image_alt": "FP PostBase mailing solution",
        "pills": ["FP", "Mailing", "Digital business"],
        "lead": "Francotyp-Postalia's recent updates point to a more focused company: mailing and shipping equipment, digital business solutions, and dealer support infrastructure.",
        "sections": [
            {
                "h2": "A tighter focus after portfolio changes",
                "paragraphs": [
                    "FP describes its core work as Mailing & Shipping Solutions plus Digital Business Solutions for office and workflow efficiency. After selling its Mail Services division in 2024, public updates emphasize mailing equipment, shipping workflows, office solutions, and process automation rather than broad corporate diversification.",
                    "That focus is useful for customers who want a clear mailroom partner without unrelated service lines complicating support or contract scope.",
                ],
            },
            {
                "h2": "2026 dealer direction points to smarter mailrooms",
                "paragraphs": [
                    "FP North America set a 2026 direction around net-new customer growth, smarter workflows, AI-driven service, and upgraded dealer infrastructure. For mailroom managers, that translates into better visibility, faster support, and more integration between physical mail and digital processes.",
                    "PostBase and related mailing platforms remain central, but the conversation is widening to include shipping labels, hybrid mail, and workflow automation around outgoing documents.",
                ],
            },
            {
                "h2": "Why mailroom modernization still matters",
                "paragraphs": [
                    "Even as offices digitize, outbound mail, parcels, and compliance-related document handling remain operational bottlenecks. FP's positioning reflects that reality: the mailroom is a business system, not a back-office afterthought.",
                    "Offices evaluating FP should look at total cost of postage handling, shipping integration, dealer response times, and how mailing equipment connects to accounts payable, client onboarding, or fulfillment workflows.",
                ],
            },
        ],
        "why": "Mailrooms are no longer just postage meters. Customers increasingly want shipping workflows, dealer support visibility, hybrid mail, and document automation in the same conversation.",
        "sources": [
            ("FP business areas", "https://www.fp-francotyp.com/en/"),
            ("FP 2026 dealer summit", "https://www.fp-usa.com/fp-leadership-sets-course-for-2026-at-nds"),
        ],
    },
    {
        "slug": "ideal",
        "filename": "automation-one-latest-news-ideal-mbm.html",
        "path": "/latest-news/ideal-mbm",
        "title": "Ideal.MBM Document Security and Finishing | Automation One",
        "description": "Full briefing on Destroyit shredders, Triumph cutters, AeroCut finishing, and high-security paper handling.",
        "kicker": "Ideal.MBM",
        "headline": "Ideal.MBM remains focused on <em>secure paper handling.</em>",
        "image": "ideal-shredder-product.png",
        "image_alt": "Ideal.MBM Destroyit shredder",
        "pills": ["Ideal.MBM", "Security", "Finishing"],
        "lead": "The Ideal.MBM story is less about splashy corporate news and more about dependable categories: Destroyit shredders, Triumph cutters, AeroCut finishing systems, and high-security destruction.",
        "sections": [
            {
                "h2": "Core categories stay consistent",
                "paragraphs": [
                    "MBM Corporation highlights Destroyit business shredders, Triumph paper cutters and trimmers, AeroCut finishing equipment, folders, bookletmakers, and related office finishing tools. That consistency is a strength for customers who need reliable replacements, parts, and service on familiar product lines.",
                    "While MFP vendors chase AI headlines, Ideal.MBM continues to solve a durable problem: what to do with sensitive paper once it exists in the office.",
                ],
            },
            {
                "h2": "High-security options for regulated environments",
                "paragraphs": [
                    "Current high-security shredder guidance emphasizes model fit by office scale, automatic oiling, ECC, Smart Shred Control, and NSA/CSS-listed options for sensitive environments. Government, legal, healthcare, and finance customers still need destruction standards that software alone cannot replace.",
                    "Choosing the right Destroyit model is less about marketing and more about sheet capacity, duty cycle, shred level, and whether staff can operate the unit safely without slowing down daily work.",
                ],
            },
            {
                "h2": "Finishing and in-house production",
                "paragraphs": [
                    "Beyond security, Ideal.MBM remains relevant wherever businesses produce booklets, trimmed collateral, or finished documents in-house. That includes marketing teams, print rooms, schools, and franchises that want control over short-run production without outsourcing every job.",
                    "Pairing finishing equipment with a managed print environment can reduce outside print spend and keep confidential materials inside the building.",
                ],
            },
        ],
        "why": "As businesses digitize, the paper that remains is often sensitive. Shredding, cutting, and finishing equipment still matter for security, compliance, and in-house document production.",
        "sources": [
            ("MBM product portfolio", "https://mbmcorp.com/"),
            ("High-security Destroyit guide", "https://www.destroyit-shredder.com/blogs/destroyit/best-mbm-destroyit-high-security-shredders-for-business-and-government-data-protection"),
        ],
    },
    {
        "slug": "more",
        "filename": "automation-one-latest-news-industry.html",
        "path": "/latest-news/industry",
        "title": "Office Technology Industry Trends 2026 | Automation One",
        "description": "Full briefing on Quocirca ACT, AI-ready print, cloud capture, and the shift from devices to connected workflow.",
        "kicker": "Industry",
        "headline": 'The whole category is shifting from devices to <em>connected workflow.</em>',
        "image": "solutions-office-bg.png",
        "image_alt": "Modern office workplace",
        "pills": ["Industry trends", "Automation", "Workflow"],
        "lead": "The latest industry research frames office equipment as part of a broader technology ecosystem: AI, cloud print, capture, security, sustainability, and workflow automation.",
        "sections": [
            {
                "h2": "ACT reframes how vendors are judged",
                "paragraphs": [
                    "Quocirca's ACT framework evaluates vendors on Automation and AI, Cloud and Collaboration, and Technology Ecosystems. That is a useful lens for buyers because it forces comparisons beyond engine speed and monthly duty cycle.",
                    "Vendors that score well tend to integrate capture, cloud storage, security, and service tooling into one coherent experience rather than selling isolated hardware.",
                ],
            },
            {
                "h2": "2026 trends favor software and services",
                "paragraphs": [
                    "Quocirca's 2026 trends report says differentiation is moving toward software and services, with AI-ready print and capture environments creating new value. Offices are being asked to connect printers and scanners to document workflows, identity systems, and line-of-business apps.",
                    "Managed print is evolving into managed document infrastructure: devices as connected nodes in a smart office, not standalone boxes in the corner.",
                ],
            },
            {
                "h2": "What this means for buying decisions",
                "paragraphs": [
                    "The buying decision is becoming less about a single device and more about the partner who can connect printing, scanning, service, security, supplies, and digital processes. That favors dealers who understand both hardware and the office systems around it.",
                    "For BC businesses, the question to ask is not only which model to lease. It is which partner can keep the fleet secure, visible, supported, and integrated as the office becomes more automated.",
                ],
            },
        ],
        "why": "The buying decision is becoming less about a single box and more about the partner who can connect printing, scanning, service, security, supplies, and digital processes.",
        "sources": [
            ("Quocirca ACT framework", "https://quocirca.com/content/quocirca-publishes-industry-first-act-framework/"),
            ("Print industry trends 2026", "https://quocirca.com/content/print-industry-trends-2026/"),
        ],
    },
]

BASE_PUBLISH_DATE = date(2026, 6, 7)


def publish_date_for_index(index: int) -> tuple[str, str]:
    published = BASE_PUBLISH_DATE - timedelta(days=index)
    return published.isoformat(), f"{published.strftime('%B')} {published.day}, {published.year}"


BRAND_LOGOS: dict[str, tuple[str, str]] = {
    "canon": ("brand-logo-canon.png", "Canon logo"),
    "xerox": ("brand-logo-xerox.png", "Xerox logo"),
    "lexmark": ("brand-logo-lexmark.png", "Lexmark logo"),
    "fp": ("brand-logo-fp.png", "FP logo"),
    "ideal": ("brand-logo-ideal.png", "Ideal MBM logo"),
    "more": ("ao-nav-logo-primary.png", "Automation One logo"),
}


def pills_html(pills: list[str]) -> str:
    return "".join(f'<span class="news-pill">{p}</span>' for p in pills)


def sections_html(sections: list[dict]) -> str:
    chunks = []
    for sec in sections:
        chunks.append(f"<h2>{sec['h2']}</h2>")
        for para in sec["paragraphs"]:
            chunks.append(f"<p>{para}</p>")
    return "\n              ".join(chunks)


def sources_html(sources: list[tuple[str, str]]) -> str:
    return "\n                ".join(
        f'<a href="{url}" target="_blank" rel="noopener noreferrer">{label}</a>'
        for label, url in sources
    )


def article_body(article: dict) -> str:
    logo_src, logo_alt = BRAND_LOGOS[article["slug"]]
    date_iso, date_display = article["date_iso"], article["date_display"]
    return f"""<section class="subpage-hero subpage-hero--photo news-article-hero">
  <img class="subpage-hero-photo" src="latest-news-hero-newsroom.png" width="1920" height="1080" alt="" aria-hidden="true" loading="eager" decoding="async" fetchpriority="high" />
  <div class="container">
    <div class="news-article-hero-card reveal">
      <span class="news-article-brand-pill" data-brand="{article['slug']}"><img class="news-article-hero-logo" src="{logo_src}" alt="{logo_alt}" decoding="async" /></span>
      <h1>{article['headline']}</h1>
      <p class="news-article-date"><time datetime="{date_iso}">{date_display}</time></p>
      <a href="automation-one-latest-news.html" class="cta cta-primary cta-pill-arrow news-article-return">Return to News</a>
    </div>
  </div>
</section>

<section class="news-article-shell">
  <div class="container">
    <article class="news-article reveal">
      <div class="news-article-photo"><img src="{article['image']}" alt="{article['image_alt']}" loading="eager" decoding="async" /></div>
      <div class="news-article-body">
        <div class="news-meta"><time class="news-date" datetime="{date_iso}">{date_display}</time>{pills_html(article['pills'])}</div>
        <p class="news-article-lead">{article['lead']}</p>
        {sections_html(article['sections'])}
        <div class="news-why"><strong>Why it matters</strong>{article['why']}</div>
        <div class="news-source-row">
          {sources_html(article['sources'])}
        </div>
      </div>
    </article>
  </div>
</section>
"""


def patch_template(html: str, article: dict) -> str:
    out = html
    out = out.replace('class="subpage latest-news-page"', 'class="subpage news-article-page"')
    out = out.replace('aria-current="page">Latest News', '>Latest News')
    out = out.replace(
        '<div class="sticky-nav-group" data-nav="offer">\n      <button type="button" class="sticky-nav-trigger" aria-expanded',
        '<div class="sticky-nav-group" data-nav="offer">\n      <button type="button" class="sticky-nav-trigger is-nav-current" aria-expanded',
        1,
    )
    out = out.replace(
        '<div class="sticky-nav-group" data-nav="who">\n      <button type="button" class="sticky-nav-trigger is-nav-current" aria-expanded',
        '<div class="sticky-nav-group" data-nav="who">\n      <button type="button" class="sticky-nav-trigger" aria-expanded',
        1,
    )
    out = re.sub(r'\n        <a href="automation-one-latest-news\.html"[^>]*>Latest News</a>', '', out)
    out = re.sub(r"<title>.*?</title>", f"<title>{article['title']}</title>", out, count=1)
    out = re.sub(
        r'<meta name="description" content="[^"]*"',
        f'<meta name="description" content="{article["description"]}"',
        out,
        count=1,
    )
    seo_block = f"""<!-- ao-seo-start -->
<link rel="canonical" href="https://automationone.org{article['path']}" />
<meta property="og:type" content="article" />
<meta property="og:site_name" content="Automation One" />
<meta property="og:url" content="https://automationone.org{article['path']}" />
<meta property="og:title" content="{article['title']}" />
<meta property="og:description" content="{article['description']}" />
<meta property="og:image" content="https://automationone.org/og-image.png" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{article['title']}" />
<meta name="twitter:description" content="{article['description']}" />
<meta name="twitter:image" content="https://automationone.org/og-image.png" />
<!-- ao-seo-end -->"""
    out = re.sub(r"<!-- ao-seo-start -->.*?<!-- ao-seo-end -->", seo_block, out, count=1, flags=re.S)

    if "/* ---------- News article pages ---------- */" not in out:
        out = out.replace("</style>", ARTICLE_CSS + "\n</style>", 1)

    start = out.index('<section class="subpage-hero subpage-hero--photo latest-news-hero">')
    end = out.index('<section class="cta-section"', start)
    out = out[:start] + article_body(article) + "\n\n" + out[end:]
    return out


def main() -> None:
    template = TEMPLATE.read_text(encoding="utf-8")
    for index, article in enumerate(ARTICLES):
        date_iso, date_display = publish_date_for_index(index)
        article = {**article, "date_iso": date_iso, "date_display": date_display}
        path = ROOT / article["filename"]
        path.write_text(patch_template(template, article), encoding="utf-8")
        print(f"Wrote {path.name} ({date_display})")


if __name__ == "__main__":
    main()
