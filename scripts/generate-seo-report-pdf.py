#!/usr/bin/env python3
"""Generate Automation One SEO / AEO / Performance / Migration PDF report."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "Automation-One-SEO-AEO-Performance-Report.pdf"
SITE_ORG = "https://automationone.org"
SITE_CA = "https://automationone.ca"
REPORT_DATE = date.today().strftime("%B %d, %Y")
BULLET = "\u2022 "


def score_bar(score: int, width: float = 4.8 * inch) -> Table:
    fill = min(max(score, 0), 100) / 100.0 * width
    gap = width - fill
    t = Table([[""]], colWidths=[fill, gap] if gap > 0 else [fill], rowHeights=[10])
    style = [
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#1f5cf5")),
        ("LINEBELOW", (0, 0), (-1, 0), 0, colors.HexColor("#d9e6ff")),
    ]
    if gap > 0:
        style.append(("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#eef4ff")))
    t.setStyle(TableStyle(style))
    return t


def styled_table(data, col_widths, header_color="#1547d1", font_size=8.5):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_color)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), font_size),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d9e6ff")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f8ff")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return t


def priority_table(rows, col_widths=(0.6 * inch, 5.7 * inch)):
    return styled_table([["Priority", "Action"]] + list(rows), col_widths, font_size=9)


def bullets(story, items, body_style):
    for item in items:
        story.append(Paragraph(BULLET + item, body_style))


def build_story():
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "AOTitle", parent=styles["Title"], fontSize=24,
        textColor=colors.HexColor("#1547d1"), spaceAfter=10, alignment=TA_CENTER,
    )
    h1 = ParagraphStyle(
        "AOH1", parent=styles["Heading1"], fontSize=15,
        textColor=colors.HexColor("#1547d1"), spaceBefore=12, spaceAfter=6,
    )
    h2 = ParagraphStyle(
        "AOH2", parent=styles["Heading2"], fontSize=11,
        textColor=colors.HexColor("#0f389e"), spaceBefore=8, spaceAfter=4,
    )
    body = ParagraphStyle("AOBody", parent=styles["BodyText"], fontSize=9.5, leading=13)
    small = ParagraphStyle("AOSmall", parent=body, fontSize=8, textColor=colors.grey)

    story = []

    # ---- Cover ----
    story.append(Spacer(1, 1.0 * inch))
    story.append(Paragraph("Automation One", title))
    story.append(Paragraph("SEO, AEO, Performance &amp; Domain Migration Report", title))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(SITE_ORG, ParagraphStyle("sub", parent=body, alignment=TA_CENTER, fontSize=11)))
    story.append(Paragraph(SITE_CA + " (current WordPress site)", ParagraphStyle("sub2", parent=body, alignment=TA_CENTER, fontSize=10)))
    story.append(Paragraph(f"Report date: {REPORT_DATE}", ParagraphStyle("dt", parent=body, alignment=TA_CENTER)))
    story.append(Spacer(1, 0.25 * inch))
    story.append(
        Paragraph(
            "Includes: live audit of automationone.org (Netlify static site), comparison with "
            "automationone.ca (WordPress), short-URL plan for long product filenames, and phased "
            "migration plan (.ca primary, .org eventually 301 to .ca).",
            ParagraphStyle("note", parent=body, alignment=TA_CENTER, fontSize=8.5),
        )
    )
    story.append(PageBreak())

    # ---- Executive summary ----
    story.append(Paragraph("Executive Summary", h1))
    story.append(
        Paragraph(
            "The <b>new Netlify site</b> (automationone.org) is stronger on speed, catalogue page weight, "
            "on-page structure, FAQ/AEO scaffolding, and unique product metadata. The <b>current .ca site</b> "
            "(WordPress + Yoast) still has more indexed URLs (198 product pages, 51 blog posts) and established "
            "search history. A smooth shutdown of WordPress requires a <b>redirect map</b>, <b>short public URLs</b> "
            "for long .html product paths, and making <b>automationone.ca</b> the canonical domain before "
            "redirecting .org to .ca.",
            body,
        )
    )
    scores = [
        ("New site (.org) overall readiness", 78, "Live on Netlify; footers/nav/products UX updated June 2026"),
        ("Old site (.ca) SEO maturity", 68, "WordPress still on many URLs; products page still ~1.2 MB"),
        ("New vs old performance", 88, "Products page ~4x smaller on .org (live check June 2026)"),
        ("Migration readiness", 58, "Short product URLs done; WordPress 301 map + .ca DNS still needed"),
    ]
    score_table = [["Category", "Score", "Notes"]] + [[a, str(b), c] for a, b, c in scores]
    story.append(styled_table(score_table, [2.2 * inch, 0.7 * inch, 3.4 * inch]))
    story.append(PageBreak())

    # ---- .ca vs .org comparison ----
    story.append(Paragraph("Website Comparison: automationone.ca vs automationone.org", h1))
    story.append(
        Paragraph(
            "Live measurements from June 2026. .ca runs WordPress behind Cloudflare; .org is static HTML on Netlify.",
            body,
        )
    )
    compare = [
        ["Area", "automationone.ca (current)", "automationone.org (new)", "Winner"],
        ["Platform", "WordPress + Yoast SEO", "Static HTML on Netlify", "New (simpler, faster ops)"],
        ["Homepage HTML", "~424 KB, ~0.45s (live)", "~424 KB, ~0.54s (live)", "Tie (both large HTML)"],
        ["Products page", "~1,235 KB, ~1.6s (live)", "~279 KB, ~0.57s (live)", "New (4x smaller)"],
        ["Contact page", "~350 KB (typical WP)", "~123 KB, ~0.35s (live)", "New"],
        ["Canon hub (/canon)", "~818 KB, ~1.2s", "Lighter static pages", "New"],
        ["Homepage title", "Keyword-heavy (Printing Vancouver...)", "Brand-focused", "New"],
        ["H1 on homepage", "0 H1 detected", "1 H1", "New"],
        ["Meta + canonical + OG", "Yes", "Yes (all 100 pages)", "Tie"],
        ["JSON-LD (homepage)", "3 blocks", "LocalBusiness + FAQ on key pages", "New (clearer)"],
        ["Sitemap size", "~198 products, 29 pages, 51 posts", "99 static URLs", "Old has more URLs today"],
        ["robots.txt", "WordPress (wp-admin rules)", "Simple + sitemap", "New"],
        ["AEO", "51 blog posts (long-tail)", "FAQ + llms.txt + LocalBusiness", "Old volume; new structure"],
        ["Est. mobile PSI (perf)", "45-55 on heavy pages", "52-62 home; catalogue still heavy", "New"],
    ]
    story.append(styled_table(compare, [1.15 * inch, 1.85 * inch, 1.85 * inch, 0.55 * inch], font_size=7.5))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("<b>Bottom line:</b> Migrate to the new site on .ca as soon as redirects are mapped. The new build is already better for performance and structured SEO/AEO; preserve .ca URL equity with 301 redirects.", body))

    story.append(Paragraph("Live HTML document metrics (.org)", h2))
    org_perf = [
        ["URL", "Time (s)", "HTML size", "Est. mobile PSI perf*"],
        ["/", "0.54", "424 KB", "52-62"],
        ["/products", "0.57", "279 KB", "48-58"],
        ["/contact", "0.35", "123 KB", "58-68"],
        ["/faq", "0.57", "121 KB", "58-68"],
        ["/about", "0.47", "142 KB", "55-65"],
        ["hero-printer-loop.mp4", "-", "6.7 MB", "Hurts LCP if autoplay"],
    ]
    story.append(styled_table([["URL", "Time", "Size", "PSI est."]] + org_perf[1:], [1.4 * inch, 0.75 * inch, 0.85 * inch, 1.9 * inch], header_color="#1f5cf5"))
    story.append(Paragraph("*HTML transfer only; run PageSpeed Insights for full lab scores.", small))
    story.append(PageBreak())

    # ---- SEO / AEO on new site ----
    story.append(Paragraph("SEO &amp; AEO on the New Site (Completed)", h1))
    bullets(story, [
        "Meta description on all 100 HTML pages",
        "Unique title + description on 35 Canon product pages",
        "rel=canonical, Open Graph, Twitter cards, og-image.png on every page",
        "robots.txt, sitemap.xml (99 URLs), llms.txt, favicons, webmanifest",
        "FAQPage JSON-LD (18 questions); LocalBusiness on home + contact",
        "automation-one-homepage-6.html: noindex; canonical to /",
        "Pretty URLs for main sections via netlify.toml (/products, /faq, etc.)",
    ], body)
    story.append(Paragraph("Remaining for perfect SEO/AEO", h2))
    story.append(priority_table([
        ("P1", "Submit sitemap after .ca cutover; verify Search Console on automationone.ca"),
        ("P1", "301 map every high-traffic WordPress URL to new paths"),
        ("P2", "Verify short URLs in Search Console after .ca cutover (implemented on .org)"),
        ("P2", "Product + BreadcrumbList JSON-LD on all SKU pages"),
        ("P2", "Decide blog strategy: redirect 51 posts vs migrate vs 410"),
        ("P3", "Organization sameAs (Google Business Profile); lastmod in sitemap"),
    ]))
    story.append(PageBreak())

    # ---- Long URL plan ----
    story.append(Paragraph("Fixing Long Product Page URLs", h1))
    story.append(
        Paragraph(
            "Physical files use long names such as "
            "<b>automation-one-canon-color-imagerunner-advance-dx-c3926i.html</b> (61 characters). "
            "There are ~70+ product pages with the automation-one-{brand}- prefix. Main pages already "
            "have short browser paths (/products, /faq); <b>product pages still show long .html URLs</b> "
            "in the address bar. <b>Status (June 2026):</b> Short paths are live on automationone.org "
            "via netlify.toml (/canon/..., /lexmark/..., /xerox/..., plus utility pages). "
            "Canonicals and sitemap should use short URLs; re-point to automationone.ca at cutover.",
            body,
        )
    )
    story.append(Paragraph("Recommended approach (safest)", h2))
    bullets(story, [
        "<b>Do not rename files on disk</b> (avoids breaking relative links and assets).",
        "Add <b>short public URLs</b> via Netlify 200 rewrites to existing .html files.",
        "Set canonical, og:url, and sitemap entries to the short URL only.",
        "Add 301 redirects from old long .html paths to short paths.",
        "Bulk-update internal hrefs in HTML (products grid, nav, breadcrumbs).",
    ], body)
    story.append(Paragraph("Target URL pattern", h2))
    url_map = [
        ["Today (example)", "Target public URL"],
        ["automation-one-canon-imagerunner-advance-dx-4945i.html", "/canon/imagerunner-advance-dx-4945i"],
        ["automation-one-lexmark-m5270.html", "/lexmark/m5270"],
        ["automation-one-xerox-altalink-c8170.html", "/xerox/altalink-c8170"],
        ["automation-one-network-installation-survey.html", "/network-survey"],
        ["automation-one-billable-confirmation.html", "/billable-confirmation"],
    ]
    story.append(styled_table(url_map, [3.2 * inch, 2.9 * inch], font_size=8))
    story.append(Paragraph("Implementation steps", h2))
    bullets(story, [
        "Script: generate netlify.toml [[redirects]] for each automation-one-{brand}-*.html",
        "Update apply-seo-fixes.py canonical base to https://automationone.ca + short paths",
        "Regenerate sitemap.xml with short URLs only",
        "Search Console URL inspection after cutover",
    ], body)
    story.append(PageBreak())

    # ---- Domain migration ----
    story.append(Paragraph("Domain Migration Plan", h1))
    story.append(
        Paragraph(
            "<b>Goal:</b> Shut down WordPress on automationone.ca, serve the new static site on both "
            ".ca and .org, then eventually <b>301 redirect automationone.org to automationone.ca</b> "
            "so .ca is the permanent primary domain.",
            body,
        )
    )

    story.append(Paragraph("Phase 0 - Prep (1-2 weeks, .ca still on WordPress)", h2))
    story.append(priority_table([
        ("P0", "Export all URLs from https://automationone.ca/sitemap_index.xml"),
        ("P0", "Build redirects-ca.csv: old WordPress path to new path (301)"),
        ("P0", "Map top paths: /, /about/, /products/, /canon/, /contact/, /service/, /toner/, /faqs/"),
        ("P0", "Decide fate of 51 blog posts (redirect to /resources, /faq, or keep /blog/)"),
        ("P0", "Map 198 old WooCommerce product URLs to new SKU pages or discontinued hub"),
        ("P0", "Implement short product URLs on Netlify before cutover"),
        ("P0", "Set canonicals to https://automationone.ca/... before .org redirect"),
    ]))

    story.append(Paragraph("WordPress slug mismatches (need explicit 301)", h2))
    slug_map = [
        ["Old (.ca)", "New site path"],
        ["/faqs/", "/faq"],
        ["/what-we-do-for-you/", "/what-we-do"],
        ["/idealmbm/", "/ideal-mbm"],
        ["/solutions/", "/digital-solutions or /what-we-do (choose one)"],
        ["Trailing slashes", "Normalize with Netlify 301 rules"],
    ]
    story.append(styled_table(slug_map, [2.2 * inch, 3.9 * inch], font_size=8.5))

    story.append(Paragraph("Phase 1 - Dual domain on Netlify (cutover week)", h2))
    bullets(story, [
        "Netlify: add custom domain automationone.ca + www.automationone.ca (same deploy as .org)",
        "Point .ca DNS to Netlify",
        "Deploy redirects-ca.csv / netlify.toml 301 rules for all old .ca URLs",
        "Google Search Console: add automationone.ca property; submit new sitemap",
        "Bing Webmaster: same",
        "Update GBP, email signatures, print ads to automationone.ca after live verification",
        "Optional: keep WordPress 48-72h for rollback only",
    ], body)

    story.append(Paragraph("Phase 2 - Stabilize (2-4 weeks)", h2))
    bullets(story, [
        "Monitor 404s in Netlify + Search Console weekly; add missing redirects",
        "Both domains serve same site; canonicals always point to https://automationone.ca",
        "GSC Change of address if Google still treats .org as primary",
    ], body)

    story.append(Paragraph("Phase 3 - .org redirects to .ca (when ready)", h2))
    story.append(
        Paragraph(
            "Add to netlify.toml (only after .ca redirects work and Search Console is clean):<br/>"
            "<font size='8'>[[redirects]] from = \"https://automationone.org/*\" "
            "to = \"https://automationone.ca/:splat\" status = 301 force = true</font>",
            body,
        )
    )
    bullets(story, [
        "Also 301 www.automationone.org to https://automationone.ca/",
        "Do not flip until: WP redirect map live, short URLs work, .ca indexed with low critical errors",
    ], body)

    story.append(Paragraph("Phase 4 - Decommission WordPress", h2))
    bullets(story, [
        "Cancel WP hosting after ~30 days stable .ca traffic",
        "Keep domain registration; DNS stays on Netlify",
    ], body)
    story.append(PageBreak())

    # ---- Migration timeline ----
    story.append(Paragraph("Suggested Timeline", h1))
    timeline = [
        ["Phase", "Duration", "Activities"],
        ["Prep", "Weeks 1-2", "Redirect map, short URLs, blog/product decisions"],
        ["Cutover", "Week 3", ".ca DNS to Netlify; 301s live; GSC submit"],
        ["Stabilize", "Weeks 4-7", "Fix 404s; canonicals on .ca; monitor rankings"],
        ["Final", "Week 8+", ".org 301 to .ca; shut down WordPress"],
    ]
    story.append(styled_table(timeline, [1.0 * inch, 1.0 * inch, 4.1 * inch]))

    story.append(Paragraph("Migration SEO / AEO checklist", h2))
    mig = [
        ["Priority", "Task"],
        ["P0", "301 every old .ca URL that had traffic (Analytics + GSC export)"],
        ["P0", "One canonical domain: https://automationone.ca everywhere"],
        ["P0", "New sitemap on .ca; resubmit in GSC"],
        ["P1", "Short public URLs for all product pages"],
        ["P1", "Product JSON-LD on SKU pages"],
        ["P1", "Blog strategy (redirect vs new /blog/)"],
        ["P2", "Performance sprint (hero video, shared CSS)"],
        ["P2", "Organization sameAs to Google Business Profile"],
    ]
    story.append(styled_table(mig, [0.65 * inch, 5.65 * inch], font_size=8.5))

    story.append(PageBreak())

    # ---- Performance roadmap ----
    story.append(Paragraph("Performance Roadmap (New Site)", h1))
    story.append(
        Paragraph(
            "Homepage: ~406 KB HTML (~191 KB inline CSS). Products: ~278 KB, 307 images "
            "(lazy-loading enabled). Hero video: 6.7 MB MP4.",
            body,
        )
    )
    story.append(priority_table([
        ("P1", "PageSpeed Insights on /, /products, /contact; fix LCP and render-blocking fonts"),
        ("P1", "Hero: poster + preload=none; static image on mobile"),
        ("P1", "Self-host or subset Google Fonts"),
        ("P2", "Extract shared CSS to cached site.css"),
        ("P2", "Products: paginate or virtualize 307 catalogue images"),
        ("P2", "WebP/AVIF for large hero images"),
    ]))
    story.append(Paragraph("Estimated PageSpeed (mobile, homepage)", h2))
    psi = [
        ["Category", "Current est.", "Target"],
        ["Performance", "52-62", "85-92"],
        ["Accessibility", "85-90", "92-96"],
        ["Best Practices", "90-96", "96-100"],
        ["SEO (Lighthouse)", "92-98", "98-100"],
    ]
    story.append(styled_table(psi, [1.5 * inch, 1.25 * inch, 1.25 * inch], header_color="#0f389e"))

    story.append(PageBreak())

    # ---- Master checklist ----
    story.append(Paragraph("Master Checklist", h1))
    checklist = [
        ["Area", "Task", "Status"],
        ["New site", "Meta + canonical + OG all pages", "Done"],
        ["New site", "Canon unique titles (35 pages)", "Done"],
        ["New site", "FAQPage + LocalBusiness JSON-LD", "Done"],
        ["New site", "robots.txt + sitemap + llms.txt", "Done"],
        ["URLs", "Short product URLs (/canon/..., /lexmark/...)", "Done on .org"],
        ["Migration", "WordPress 301 redirect map", "To do"],
        ["Migration", ".ca on Netlify (same deploy)", "To do"],
        ["Migration", "GSC sitemap on .ca", "To do"],
        ["Migration", ".org 301 to .ca", "Later"],
        ["Perf", "PSI Performance 90+", "To do"],
        ["AEO", "Product schema all SKUs", "To do"],
        ["Trust", "GBP linked in schema", "To do"],
    ]
    story.append(styled_table(checklist, [0.9 * inch, 3.5 * inch, 1.0 * inch], font_size=8))

    story.append(PageBreak())

    # ---- Simple next-steps (plain language) ----
    story.append(Paragraph("Simple To-Do List (Start Here)", h1))
    story.append(
        Paragraph(
            "Think of this like moving houses: the <b>new house</b> is built (automationone.org on Netlify). "
            "Your <b>old address</b> (automationone.ca) still has the old furniture (WordPress). "
            "You need to put a sign on the old address that says \"we moved here\" (301 redirects), "
            "then tell Google the new address.",
            body,
        )
    )
    simple_steps = [
        ("1", "Open the new site", "Visit https://automationone.org and click around. If something looks wrong, fix it before switching .ca."),
        ("2", "Make a list of old links", "Export every URL from https://automationone.ca/sitemap_index.xml (like a phone book of old pages)."),
        ("3", "Match old to new", "For each old link, write which new page it should open (example: /faqs/ goes to /faq). Save as docs/redirects-wp.csv."),
        ("4", "Add redirects in Netlify", "Put those rules in netlify.toml so old .ca links automatically jump to the right new page."),
        ("5", "Connect .ca to Netlify", "In Netlify: add automationone.ca as a custom domain. At your domain registrar: point .ca DNS to Netlify."),
        ("6", "Tell Google", "In Google Search Console: add automationone.ca, submit the new sitemap, watch for 404 errors for 2-4 weeks."),
        ("7", "Update the real world", "Change Google Business Profile, email signatures, and printed stuff to say automationone.ca."),
        ("8", "Turn off WordPress", "Only after .ca works and redirects are good for ~30 days. Cancel old hosting."),
        ("9", "Later: .org to .ca", "When everything is calm, make automationone.org automatically forward to automationone.ca (one permanent address)."),
    ]
    story.append(
        styled_table(
            [["Step", "What to do", "Why"]] + [[a, b, c] for a, b, c in simple_steps],
            [0.45 * inch, 2.5 * inch, 3.2 * inch],
            font_size=8,
        )
    )
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("<b>Already done for you:</b> New site design updates pushed to Netlify; short product URLs on .org; SEO tags on all pages.", body))

    story.append(Spacer(1, 0.15 * inch))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#d9e6ff")))
    story.append(
        Paragraph(
            f"Automation One | {SITE_ORG} | {SITE_CA} | {REPORT_DATE}<br/>"
            "Regenerate: python3 scripts/generate-seo-report-pdf.py",
            small,
        )
    )
    return story


def main() -> None:
    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=letter,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        title="Automation One SEO AEO Performance Migration Report",
        author="Automation One",
    )
    doc.build(build_story())
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
