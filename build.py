#!/usr/bin/env python3
"""Generate case-study and blog HTML from the Consulting markdown sources."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONSULTING = Path("/home/cursor/Documents/Consulting")
CASES = CONSULTING / "Case Studies"
POSTS = CONSULTING / "Blog posts"

LINKEDIN = "https://linkedin.com/in/ftriboix"

CONSENT_AND_TAG = """    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('consent', 'default', {
        ad_storage: 'denied',
        ad_user_data: 'denied',
        ad_personalization: 'denied',
        analytics_storage: 'denied',
        functionality_storage: 'denied',
        personalization_storage: 'denied',
        security_storage: 'granted',
        wait_for_update: 500
      });
      try {
        var savedConsent = localStorage.getItem('ft-consent');
        if (savedConsent === 'granted') {
          gtag('consent', 'update', {
            ad_storage: 'granted',
            ad_user_data: 'granted',
            ad_personalization: 'granted',
            analytics_storage: 'granted',
            functionality_storage: 'denied',
            personalization_storage: 'denied'
          });
        } else if (savedConsent === 'denied') {
          gtag('consent', 'update', {
            ad_storage: 'denied',
            ad_user_data: 'denied',
            ad_personalization: 'denied',
            analytics_storage: 'denied',
            functionality_storage: 'denied',
            personalization_storage: 'denied'
          });
        }
      } catch (ignore) {}
    </script>
    <script async src="https://www.googletagmanager.com/gtm.js?id=GTM-5CVMNLWQ"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
    </script>"""


def html_esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def prepare_markdown(md: str) -> str:
    """Insert a blank line before indented lists so pandoc actually emits <ul>/<ol>."""
    lines = md.split("\n")
    out: list[str] = []

    def is_list_item(line: str) -> bool:
        stripped = line.lstrip()
        return stripped.startswith(("- ", "* ")) or bool(re.match(r"\d+\. ", stripped))

    for line in lines:
        if out and is_list_item(line) and out[-1].strip() and not is_list_item(out[-1]):
            out.append("")
        out.append(line)
    return "\n".join(out)


def pandoc(md: str) -> str:
    result = subprocess.run(
        [
            "pandoc",
            "-f",
            "markdown-smart+autolink_bare_uris",
            "-t",
            "html5",
            "--wrap=none",
        ],
        input=prepare_markdown(md),
        text=True,
        capture_output=True,
        check=True,
    )
    html = result.stdout
    if "\u2014" in html or "&mdash;" in html:
        raise SystemExit("pandoc emitted an em-dash; refuse to publish")
    return html


def header(active: str) -> str:
    def item(href: str, label: str, key: str) -> str:
        current = ' aria-current="page"' if active == key else ""
        return f'          <a href="{href}"{current}>{label}</a>'

    return f"""    <header class="site-header">
      <div class="wrap header-inner">
        <a class="wordmark" href="../index.html">Fabrice Triboix</a>
        <nav class="site-nav" aria-label="Primary">
{item("../index.html#offers", "Offers", "offers")}
{item("../index.html#work", "Work", "work")}
{item("../index.html#writing", "Writing", "writing")}
          <a
            href="{LINKEDIN}"
            target="_blank"
            rel="noopener noreferrer"
            >LinkedIn</a
          >
        </nav>
      </div>
    </header>"""


def footer() -> str:
    return f"""    <footer class="site-footer">
      <div class="wrap footer-inner">
        <p class="footer-name">Fabrice Triboix</p>
        <p>Independent consultant. Based in London; clients wherever they are.</p>
        <p>
          <a
            href="{LINKEDIN}"
            target="_blank"
            rel="noopener noreferrer"
            >linkedin.com/in/ftriboix</a
          >
        </p>
        <p class="footer-legal">
          Falcon One Limited, 269 Farnborough Road, Farnborough, GU17 4LY.
          Registered in England no 5854724.
        </p>
        <p class="footer-consent">
          <button type="button" class="consent-manage">Privacy choices</button>
        </p>
      </div>
    </footer>
    <script src="../consent.js"></script>"""


def page(
    *,
    title: str,
    description: str,
    active: str,
    back_href: str,
    back_label: str,
    body: str,
) -> str:
    return f"""<!DOCTYPE html>
<html lang="en-GB">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{html_esc(title)} | Fabrice Triboix</title>
    <meta name="description" content="{html_esc(description)}" />
    <meta name="theme-color" content="#001733" />
{CONSENT_AND_TAG}
    <link rel="stylesheet" href="../styles.css" />
  </head>
  <body>
    <a class="skip" href="#main">Skip to content</a>
{header(active)}
    <main id="main" class="article">
      <div class="article-inner">
        <a class="back" href="{back_href}">{html_esc(back_label)}</a>
{body}
      </div>
    </main>
{footer()}
  </body>
</html>
"""


def parse_case(md: str) -> tuple[str, str, dict[str, str], str]:
    title_line, rest = md.split("\n", 1)
    title = title_line.lstrip("# ").strip()
    brief_at = rest.find("The engagement in brief:")
    sit_at = rest.find("## Situation")
    if brief_at == -1 or sit_at == -1:
        raise SystemExit("case study missing expected headings")
    intro = rest[:brief_at].strip()
    brief = rest[brief_at:sit_at]
    body = rest[sit_at:].strip()
    meta: dict[str, str] = {}
    for line in brief.splitlines():
        line = line.strip()
        if line.startswith("- ") and ": " in line:
            key, value = line[2:].split(": ", 1)
            meta[key.strip()] = value.strip()
    return title, intro, meta, body


def meta_html(meta: dict[str, str]) -> str:
    order = ["Client", "Sector", "When", "Role", "Stack"]
    parts = ['          <dl class="meta">']
    for key in order:
        if key not in meta:
            continue
        parts.append("            <div>")
        parts.append(f"              <dt>{html_esc(key)}</dt>")
        parts.append(f"              <dd>{html_esc(meta[key])}</dd>")
        parts.append("            </div>")
    parts.append("          </dl>")
    return "\n".join(parts)


def link_cases(html: str, slug: str) -> str:
    if slug == "natwest-per-tenant-egress.html":
        html = html.replace(
            "has its own write-up",
            'has its own <a href="natwest-observability-you-can-trust.html">write-up</a>',
        )
    if slug == "natwest-observability-you-can-trust.html":
        html = html.replace(
            "see the per-tenant egress case study",
            'see the <a href="natwest-per-tenant-egress.html">per-tenant egress case study</a>',
        )
    return html


def indent_block(html: str, spaces: int = 10) -> str:
    pad = " " * spaces
    lines = html.strip().splitlines()
    return "\n".join(pad + line if line else "" for line in lines)


CASE_STUDIES = [
    {
        "src": "natwest-per-tenant-egress.md",
        "slug": "natwest-per-tenant-egress.html",
        "description": "I designed and built the per-tenant egress solution for NatWest Bank's next-generation platform.",
    },
    {
        "src": "natwest-observability-you-can-trust.md",
        "slug": "natwest-observability-you-can-trust.html",
        "description": "I took observability on NatWest Bank's multi-tenant platform from a proof of concept to a production service that proves it works.",
    },
    {
        "src": "pfizer-passwordless-databases.md",
        "slug": "pfizer-passwordless-databases.html",
        "description": "I moved Pfizer's data and BI applications from database passwords to RDS IAM authentication.",
    },
    {
        "src": "hmrc-hawk-both-sides-of-a-platform.md",
        "slug": "hmrc-hawk-both-sides-of-a-platform.html",
        "description": "On HMRC's HAWK platform I worked on the platform itself and looked after one of its tenants.",
    },
]

BLOGS = [
    {
        "src": "blog-20261118-tenant-isolation-isnt-just-compliance.md",
        "slug": "tenant-isolation-is-not-just-a-compliance-problem.html",
        "image": "tenant-isolation-is-not-just-a-compliance-problem.png",
        "image_class": "article-hero article-diagram",
        "description": "Tenant isolation is a compliance requirement, and also a security and availability problem when tenants share resources.",
    },
    {
        "src": "blog-20261111-gcp-outage.md",
        "slug": "what-should-a-fintech-cto-learn-about-the-gcp-outage.html",
        "image": None,
        "description": "What a fintech CTO or Head of Platform should take from the GCP europe-west2-b outage of 20 October 2026.",
    },
    {
        "src": "blog-20261104-is-your-multi-tenant-platform-becoming-a-business-risk.md",
        "slug": "is-your-multi-tenant-platform-becoming-a-business-risk.html",
        "image": "is-your-multi-tenant-platform-becoming-a-business-risk.jpg",
        "description": "Scaling a multi-tenant platform can turn architecture weaknesses into a business risk.",
    },
    {
        "src": "blog-20261028-what-does-multi-tenant-mean.md",
        "slug": "what-does-multi-tenant-even-mean.html",
        "image": "what-does-multi-tenant-mean.jpg",
        "description": "What multi-tenant means on a platform at a bank or a fintech, as opposed to SaaS.",
    },
    {
        "src": "blog-20261021-when-to-build-a-multi-tenant-platform.md",
        "slug": "when-should-a-company-build-a-multi-tenant-platform.html",
        "image": "when-to-build-a-multi-tenant-platform.jpg",
        "description": "There is no off-the-shelf fully functional multi-tenant platform you can buy.",
    },
    {
        "src": "blog-20261014-shared-egress-is-how-tenants.md",
        "slug": "a-shared-egress-is-how-tenants-become-each-others-incidents.html",
        "image": "shared-egress.png",
        "description": "Shared egress is how one tenant becomes another tenant's incident.",
    },
    {
        "src": "blog-20261007-what-should-the-platform-team-actually-own.md",
        "slug": "what-should-the-platform-team-actually-own.html",
        "image": "what-should-the-platform-team-actually-own.png",
        "description": "Let responsibilities follow governance, and use managed services and automation to keep the effort light.",
    },
    {
        "src": "blog-20260930-your-dashboards-are-green-your-platform-broken.md",
        "slug": "your-dashboards-are-green-your-platform-is-still-broken.html",
        "image": "your-dashboards-are-green-your-platform-broken.png",
        "description": "Green infrastructure dashboards are not proof that the platform is doing its job.",
    },
    {
        "src": "blog-20260923-dont-bolt-observability-at-the-end.md",
        "slug": "dont-bolt-observability-onto-your-platform-at-the-end.html",
        "image": "dont-bolt-observability.png",
        "description": "Observability should be designed into the platform from the beginning, with canaries as each capability is built.",
    },
    {
        "src": "blog-20260916-what-cto-should-know-before-choosing-k8s.md",
        "slug": "what-a-cto-should-know-before-choosing-kubernetes.html",
        "image": None,
        "description": "A short comparison of Kubernetes and autoscaling groups, for CTOs choosing a platform.",
    },
]


def build_cases() -> None:
    out_dir = ROOT / "case-studies"
    out_dir.mkdir(exist_ok=True)
    for spec in CASE_STUDIES:
        md = (CASES / spec["src"]).read_text(encoding="utf-8")
        title, intro, meta, body_md = parse_case(md)
        intro_html = link_cases(pandoc(intro), spec["slug"])
        body_html = link_cases(pandoc(body_md), spec["slug"])
        body = (
            f"        <h1>{html_esc(title)}</h1>\n"
            f"{indent_block(intro_html)}\n"
            f"{meta_html(meta)}\n"
            f"{indent_block(body_html)}\n"
        )
        html = page(
            title=title,
            description=spec["description"],
            active="work",
            back_href="../index.html#work",
            back_label="Back to work",
            body=body,
        )
        dest = out_dir / spec["slug"]
        dest.write_text(html, encoding="utf-8")
        print(f"wrote {dest}")


def build_blogs() -> None:
    out_dir = ROOT / "blog"
    out_dir.mkdir(exist_ok=True)
    for spec in BLOGS:
        md = (POSTS / spec["src"]).read_text(encoding="utf-8")
        first = md.split("\n", 1)[0]
        title = first.lstrip("# ").strip()
        converted = pandoc(md)
        converted = re.sub(r"^<h1[^>]*>.*?</h1>\s*", "", converted, count=1, flags=re.S)
        image_html = ""
        if spec["image"]:
            image_class = spec.get("image_class", "article-hero")
            image_html = (
                f'        <img class="{html_esc(image_class)}" src="../assets/blog/{spec["image"]}" '
                f'alt="{html_esc(title)}" width="1600" height="900" />\n'
            )
        body = (
            f"{image_html}"
            f"        <h1>{html_esc(title)}</h1>\n"
            f"{indent_block(converted)}\n"
        )
        html = page(
            title=title,
            description=spec["description"],
            active="writing",
            back_href="../index.html#writing",
            back_label="Back to writing",
            body=body,
        )
        dest = out_dir / spec["slug"]
        dest.write_text(html, encoding="utf-8")
        print(f"wrote {dest}")


if __name__ == "__main__":
    build_cases()
    build_blogs()
