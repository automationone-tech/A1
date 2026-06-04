# Domain cutover checklist (~7 days)

Target: **automationone.ca** becomes primary; **automationone.org** eventually 301s to .ca.

## Done in this deploy

- Short public URLs: `/canon/{model}`, `/lexmark/{model}`, `/xerox/{model}`
- Utility pages: `/network-survey`, `/billable-confirmation`, `/printer-bash`
- 301 from legacy `/automation-one-*.html` paths to short URLs
- Internal links, sitemap, and canonicals use short paths on **automationone.org**

## Before DNS switch to Netlify (.ca)

1. Export WordPress URLs from `https://automationone.ca/sitemap_index.xml`
2. Build `docs/redirects-wp.csv` (old path ? new short path)
3. Add WordPress 301 rules to `netlify.toml` (or `_redirects`) before cutover
4. Add **automationone.ca** custom domain in Netlify (same site)
5. Change `SITE` in `scripts/apply-seo-fixes.py` to `https://automationone.ca` and re-run scripts
6. Google Search Console: verify .ca, submit sitemap
7. Test top 20 old .ca URLs return 301 to correct new pages

## Slug redirects (.ca WordPress ? new site)

| Old | New |
|-----|-----|
| `/faqs/` | `/faq` |
| `/what-we-do-for-you/` | `/what-we-do` |
| `/idealmbm/` | `/ideal-mbm` |
| `/solutions/` | `/digital-solutions` (confirm) |

## After .ca is stable (~2–4 weeks)

- Netlify: `automationone.org/*` ? `automationone.ca/:splat` (301, force)
- Decommission WordPress hosting
