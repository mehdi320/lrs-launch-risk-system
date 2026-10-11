# LRS — English version of the Resources tab content (Ads Library, Changelog, Benchmark).
#
# Same structure as resources_content.py (French). pilot_server.py picks one
# or the other according to the request language (lrs_i18n). Keep both files
# in sync when you add a card or a guide.

ADS_LIBRARY = {
    "meta": {
        "label": "Meta Ads",
        "cards_heading": "Quick frameworks", "guides_heading": "Complete Meta Ads guide",
        "cards": [
            {
                "title": "Hook Formula — 4 types", "color": "accent", "icon": "🎯",
                "items": [
                    "Question: “Why aren't your Meta ads converting?”",
                    "Shock stat: “73% of campaigns fail on day 1. Here's why”",
                    "Pattern interrupt: unexpected visual + short text",
                    "Identification: “If you run paid traffic...”",
                ],
            },
            {
                "title": "Meta ad structure", "color": "success", "icon": "📐",
                "items": [
                    "0–3s: visual hook + text overlay (one sentence max)",
                    "3–15s: body — problem → solution → proof",
                    "15–30s: clear CTA + urgency (“Offer ends Sunday”)",
                    "Primary text: 125 characters before “See more” → the hook must be there",
                ],
            },
            {
                "title": "CTR benchmarks (cold traffic)", "color": "warning", "icon": "📊",
                "items": [
                    "> 2% CTR: good — publish more",
                    "> 4% CTR: excellent — scale the budget",
                    "< 1% CTR: rework the creative or the audience is too broad",
                    "Acceptable CPM: €8–18 (ecom/digital)",
                    "Frequency > 3.5: creative fatigue, swap the creative",
                ],
            },
            {
                "title": "Primary text templates", "color": "cyan", "icon": "✍️",
                "items": [
                    "PAS: Problem → Agitate (“you're losing $X a day”) → Solve",
                    "Social proof: “[Name] got [result] in [timeframe]”",
                    "Direct: “[Benefit] without [pain]. Here's how”",
                    "Question + answer: “Want X? Here's what the pros do”",
                ],
            },
        ],
        "guides": [
            {"title": "🎯 Audience strategy — from zero to scale", "body": """**Phase 1 — Cold traffic testing**
- Broad (no interests) on wide purchase behaviors — €20/day budget per ad set
- 1-3% lookalike of your best buyers (LAL)
- 1-2 broad but well-targeted interests (skip the obvious ones)

**Phase 2 — Scale what works**
- ROAS > 2.5 → double the budget every 3 days at most (not every day)
- CBO (Campaign Budget Optimization) once you have 2+ winning ad sets
- Don't touch an active ad set during its first 3 days: let the algorithm learn

**Phase 3 — Retargeting**
- 7-day visitors who didn't buy: show social proof (reviews, results)
- 14-day add-to-carts who didn't buy: urgency + a slightly different offer
- 180-day buyers: upsell / cross-sell — very low CPM, high ROAS"""},
            {"title": "📐 Winning creative formats in 2025", "body": """**Static image with text overlay** (still works)
- Plain background or product alone — white text on a dark background
- The rule: 1 image = 1 message = 1 CTA
- 1:1 ratio for Feed, 9:16 for Stories/Reels

**15–30s UGC** (best ROAS right now)
- A real person on camera, natural sound, casual outfit
- Structure: pain point 0-3s → solution → demo → result
- No background music, no logo at the start: it must feel native

**Native Reels with voiceover**
- TikTok visual trends adapted to Meta
- Text hook in the first 2 seconds
- Captions are a must (85% watch without sound)

**Ecom carousel**
- Slide 1: main benefit (not the product)
- Slides 2-4: proof, features, results
- Final slide: CTA + offer"""},
            {"title": "⚙️ Optimal account structure", "body": """**Recommended 2025 structure:**
```
CBO campaign — [Objective: Sales]
  +-- Ad set 1: Broad 18-45 (no interests)
  +-- Ad set 2: 1-3% buyer LAL
  +-- Ad set 3: Broad interest #1
      +-- Creative A (static image)
      +-- Creative B (15s UGC)
      +-- Creative C (native Reel)
```

**Golden rules:**
- 1 Prospecting campaign + 1 Retargeting campaign (keep them separate!)
- At least 3 creatives per ad set to give the algorithm room
- Never raise the budget by more than 20% at once: it resets the learning phase
- Pixel: the Purchase event is required before launch (conversion event)"""},
        ],
    },
    "tiktok": {
        "label": "TikTok Ads",
        "cards_heading": "Quick frameworks", "guides_heading": "Complete TikTok Ads guide",
        "cards": [
            {
                "title": "The first-2-seconds rule", "color": "tiktok", "icon": "⚡",
                "items": [
                    "A scroll lasts 0.5s: your hook has to stop the thumb",
                    "✅ Unexpected visual OR a shocking text overlay right away",
                    "✅ Start IN MEDIAS RES (mid-action)",
                    "❌ Logo at the start = guaranteed skip",
                    "❌ Slow intro with music = lost audience",
                ],
            },
            {
                "title": "TikTok ad video structure", "color": "tiktok", "icon": "📱",
                "items": [
                    "0-2s: visual hook + text (pattern interrupt)",
                    "2-8s: problem or identification (“If you do X...”)",
                    "8-18s: solution + quick demo",
                    "18-25s: social proof (before/after, testimonial)",
                    "25-30s: clear CTA + urgency",
                ],
            },
            {
                "title": "TikTok Ads benchmarks", "color": "success", "icon": "📊",
                "items": [
                    "✅ CTR > 2.5%: good for cold traffic",
                    "✅ CPM: €5–12, lower than Meta",
                    "⚠️ 6s view-through rate > 25%: the hook works",
                    "🚀 ROAS > 2.0 before you scale",
                    "Frequency > 2.5 over 7 days: new creative needed now",
                ],
            },
            {
                "title": "Winning native formats", "color": "cyan", "icon": "🎬",
                "items": [
                    "Face-to-camera UGC: 15–30s, natural ambient sound",
                    "Spark Ads: boost your organic TikTok posts",
                    "Trending audio: use trending sounds within 48h",
                    "Text overlay: auto captions OR styled manual ones",
                    "Duet / Reaction: a real-time reaction to the product",
                ],
            },
        ],
        "guides": [
            {"title": "🎬 Hooks that stop the scroll", "body": """**The 5 hook types that convert:**

1. **The direct question**: “Do you know why your ROAS drops every month?”
2. **The shocking result**: “I made $12,000 in 4 days with a $300 ad”
3. **The counter-intuitive**: “Stop targeting your competitors on Meta. Here's why”
4. **The identification**: “This problem hits EVERY ecom store in 2025”
5. **The teaser**: “I'll show you exactly how I did it... watch till the end”

**Common mistakes:**
- Text overlay too long (6 words max in the hook)
- Face out of frame or badly lit
- Poor audio quality (a deal breaker on TikTok)
- Vague CTA (“click here”) → be specific (“Link in bio, 48h offer”)"""},
            {"title": "⚙️ TikTok Ads campaign setup (2025 structure)", "body": """**Minimum budget:** €30–50/day so the algorithm can learn properly.

**Recommended structure:**
```
Campaign — [Objective: Conversions / Purchase]
  +-- Ad group 1: Broad (18-35) — no interests
  +-- Ad group 2: Custom audience (30-day visitors)
  +-- Ad group 3: 1-5% buyer lookalike
      +-- Creative 1 (15s UGC)
      +-- Creative 2 (text overlay + product)
      +-- Creative 3 (20s testimonial)
```

**Spark Ads vs. non-Spark:**
- Spark Ads (boosting an organic post) = stronger social credibility, visible comments
- Non-Spark = full control, ideal for testing angles without touching your organic account
- Recommendation: test both and compare CTR

**TikTok Pixel:** install the TikTok pixel AND the Conversions API (server-side) to get around ad blockers: +15-25% more tracked data."""},
            {"title": "🔄 Creative testing rhythm", "body": """**TikTok golden rule:** creatives burn out 3x faster than on Meta.

**Recommended cycle:**
- Weeks 1-2: test 3-5 creatives, €30-50/day per ad group
- Day 3: check the 6s view-through rate. < 20% = the hook failed, cut the creative
- Day 5: check CTR and CPA. Beating target = scale the budget x1.5
- Week 3: make 2-3 variations of the winners (same angle, different format)
- Week 4+: new creatives on new angles if ROAS drops

**Creative rotation:** at least 1 new creative per week to keep performance up."""},
        ],
    },
    "google": {
        "label": "Google Ads",
        "cards_heading": "Quick frameworks", "guides_heading": "Complete Google Ads guide",
        "cards": [
            {
                "title": "Search RSA ad structure", "color": "google_blue", "icon": "🔍",
                "items": [
                    "Headline 1 (30 chars): exact main keyword",
                    "Headline 2 (30 chars): main benefit + a number",
                    "Headline 3 (30 chars): CTA or urgency (“From $47”)",
                    "Description 1 (90 chars): main USP + proof",
                    "Description 2 (90 chars): main objection + guarantee",
                ],
            },
            {
                "title": "Must-have extensions", "color": "google_blue", "icon": "🔧",
                "items": [
                    "Sitelinks: 4 links to key pages (FAQ, Pricing, Testimonials...)",
                    "Callouts: short USPs (“24h delivery”, “30-day guarantee”)",
                    "Structured snippets: list of products/services",
                    "Call extension: visible phone number (great for B2B)",
                    "Price extension: your offers with visible prices",
                ],
            },
            {
                "title": "Match types", "color": "google_green", "icon": "🎯",
                "items": [
                    "[Exact]: maximum control, low volume",
                    "“Phrase”: balance between volume and relevance",
                    "Broad: high volume, needs a negative keyword list",
                    "→ Start with Exact, widen once CPA is on target",
                    "→ Negative list: exclude off-target terms from day 1",
                ],
            },
            {
                "title": "Quality Score — the 3 pillars", "color": "google_yellow", "icon": "⭐",
                "items": [
                    "1. Ad relevance (keyword in the headline = higher QS)",
                    "2. Expected CTR vs. competitors (creative = differentiation)",
                    "3. Landing page experience (LRS helps you here 🚦)",
                    "QS 7-10: CPC up to 50% lower vs. QS < 5",
                    "Slow LP (> 3s) = lower QS — optimize your Core Web Vitals",
                ],
            },
        ],
        "guides": [
            {"title": "🏗️ Recommended account structure", "body": """**SKAG vs. themed ad groups (2025):**
SKAGs (1 keyword per ad group) are outdated. Google favors RSAs and smart broad match.

**Recommended themed structure:**
```
Account
  +-- Search campaign — [Main product]
  |     +-- Ad group: purchase keywords ("buy X", "X price", "order X")
  |     +-- Ad group: comparison keywords ("X vs Y", "best X")
  |     +-- Ad group: problem keywords ("how to [solve problem]")
  |
  +-- Shopping campaign — [Optimized product feed]
  |
  +-- Retargeting campaign — [RLSA + Display]
```

**Testing budget:** at least €20/day per Search campaign so the algorithm gets enough data within 7-14 days."""},
            {"title": "📈 Bidding strategies — when to use what", "body": """| Strategy | When to use it |
|-----------|-----------------|
| Maximize clicks | Launch, goal = data |
| Maximize conversions | After 30+ conversions/month |
| Target CPA | Stable budget + reliable conversion history |
| Target ROAS | Ecom with variable basket values |
| Target CPM | Display/YouTube, awareness only |

**Rule:** never change the bidding strategy during the first 2 weeks. The algorithm needs 7-14 days to learn.

**Performance Max:** avoid it on pure cold traffic, PMax will cannibalize your Search campaigns. Turn it on once Search works and you have conversion data."""},
            {"title": "🛒 Google Shopping — optimize your feed", "body": """**The 3 elements behind 80% of Shopping success:**

1. **Product title** (the most important):
   - Format: `[Brand] [Product type] [Main attribute] [Size/Color/Variant]`
   - Example: “Nike Air Max 90 White Men's 9 — Running Shoes”
   - The keyword must sit in the first 70 characters

2. **Product image**:
   - White or transparent background, no lifestyle shots for Shopping
   - Product centered, filling > 75% of the frame
   - High-resolution PNG (min. 800x800)

3. **Price**:
   - A visible strikethrough price (compare-at price) improves CTR
   - Shipping costs clearly shown (or “Free shipping”)
   - Merchant Center promotions = “Promotion” badge on the ad

**Bid segmentation:** create separate product groups for your bestsellers (high bid) vs. the full catalog (low bid)."""},
        ],
    },
    "funnel": {
        "label": "Ecom Funnel",
        "cards_heading": "Funnel structures", "guides_heading": "The unbreakable rules of a converting landing page",
        "cards": [
            {
                "title": "Direct Response funnel", "color": "accent", "icon": "🎯",
                "items": [
                    "Ad → short landing page → checkout",
                    "⚡ The simplest, ideal for testing",
                    "LP: 500-800 words, 1 CTA, no nav",
                    "Checkout: 1 page, lots of trust signals",
                    "Upsell: order bump on the checkout",
                ],
            },
            {
                "title": "VSL funnel (Video Sales Letter)", "color": "success", "icon": "🎬",
                "items": [
                    "Ad → LP with video → checkout → upsells",
                    "📹 8-20 min VSL for $97+ products",
                    "Autoplay video without controls (where possible)",
                    "CTA appears at 60% of the video",
                    "Upsell 1 (complementary) + Upsell 2 (premium)",
                ],
            },
            {
                "title": "Lead Magnet funnel", "color": "warning", "icon": "📧",
                "items": [
                    "Ad → opt-in (email) → email nurturing → sale",
                    "🎁 Ideal for: info products, coaching, SaaS",
                    "Lead magnet: high perceived value, fast result",
                    "5-email sequence: value → value → pitch → urgency → last chance",
                    "Parallel retargeting on opt-ins who didn't convert",
                ],
            },
        ],
        "cards2": [
            {
                "title": "High-converting LP structure", "color": "accent", "icon": "📄",
                "items": [
                    "① Hero: headline + subheadline + CTA above the fold",
                    "② Problem: “Are you struggling with...”",
                    "③ Solution: your product = the bridge",
                    "④ Proof: before/after, testimonials, numbers",
                    "⑤ Offer: what they get (offer stack)",
                    "⑥ Guarantee: lower the perceived risk",
                    "⑦ Final CTA: urgency + button",
                ],
            },
            {
                "title": "Mistakes that kill conversion", "color": "danger", "icon": "⚠️",
                "items": [
                    "❌ Visible header navigation (leak = -20-40% CVR)",
                    "❌ Generic CTA (“Learn more”, “Click here”)",
                    "❌ Price without context (no comparison / strikethrough)",
                    "❌ Missing or hidden guarantee",
                    "❌ No social proof above the fold",
                    "❌ Page slower than 3s (Google: -53% bounce rate)",
                ],
            },
            {
                "title": "Offer Stack — how to present the offer", "color": "success", "icon": "🎁",
                "items": [
                    "List EVERYTHING the customer gets, with a dollar value",
                    "Main product: “Value: $197”",
                    "Bonus 1: “Value: $97” (should feel worth more than the price)",
                    "Bonus 2: “Value: $47”",
                    "30-day guarantee: “Zero risk”",
                    "Strikethrough total → “Today only: $47”",
                ],
            },
            {
                "title": "Checkout optimization", "color": "warning", "icon": "🛒",
                "items": [
                    "1-page checkout = best CVR (Shopify, ThriveCart...)",
                    "Visible order bump (+15-25% average order value)",
                    "Secure payment logos under the button",
                    "Order summary visible next to the form",
                    "A testimonial or stat under the checkout CTA",
                ],
            },
        ],
        "guides": [
            {"title": "📊 CVR benchmarks by page type", "body": """| Page type | Low CVR | Average CVR | Excellent CVR |
|---|---|---|---|
| Cold traffic landing page | < 1% | 1.5–3% | > 4% |
| Ecom product page | < 1.5% | 2–4% | > 5% |
| Checkout (LP visitors) | < 30% | 40–60% | > 70% |
| Opt-in page (lead magnet) | < 20% | 30–50% | > 60% |
| Upsell 1 | < 10% | 15–25% | > 35% |

*These benchmarks vary with price, niche and traffic source. Use LRS to find what's dragging your CVR down.*"""},
        ],
    },
    "copywriting": {
        "label": "Copywriting",
        "cards_heading": "Copywriting frameworks", "guides_heading": "Ready-to-use templates",
        "cards": [
            {
                "title": "PAS — Problem · Agitate · Solve", "color": "accent", "icon": "🔥",
                "items": [
                    "P: name the problem EXACTLY the way the customer feels it",
                    "A: agitate — “And it costs you $X a month / wrecks your...”",
                    "S: present your solution as the obvious answer",
                    "⚡ Best for: primary text, email, VSL intro",
                ],
            },
            {
                "title": "AIDA — Attention · Interest · Desire · Action", "color": "success", "icon": "📈",
                "items": [
                    "A: Attention — strong hook (stat, question, shock)",
                    "I: Interest — why it matters TO THEM",
                    "D: Desire — concrete benefits + proof",
                    "A: Action — clear CTA + urgency",
                    "⚡ Best for: landing pages, email sequences",
                ],
            },
            {
                "title": "BAB — Before · After · Bridge", "color": "warning", "icon": "🌉",
                "items": [
                    "Before: “You used to spend 2 hours tweaking your ads...”",
                    "After: “Imagine knowing your exact score before spending $1”",
                    "Bridge: “That's exactly what LRS™ does in 15s”",
                    "⚡ Best for: testimonials, UGC ads, welcome emails",
                ],
            },
            {
                "title": "The 4 U's — Urgent · Unique · Useful · Ultra-specific", "color": "cyan", "icon": "✅",
                "items": [
                    "Urgent: why act now? (price, stock, deadline)",
                    "Unique: what do YOU have that nobody else does?",
                    "Useful: what concrete, measurable result?",
                    "Ultra-specific: “23% CVR in 7 days” > “more sales”",
                    "⚡ A checklist for every headline you write",
                ],
            },
            {
                "title": "Proven hook formulas", "color": "danger", "icon": "💡",
                "items": [
                    "“[Number] [persona] got [result] in [timeframe]”",
                    "“The real reason [problem persists]”",
                    "“Stop [common action]. Here's what actually works”",
                    "“How to [desired result] without [usual pain]”",
                    "“What [authority] doesn't want you to know about [topic]”",
                ],
            },
        ],
        "guides": [
            {"title": "📝 Meta Ads primary text templates (copy-paste)", "body": """**PAS template (30-60 words):**
```
You spend $500 a month on Meta ads and wonder why your ROAS is stuck at 1.2?

The real reason: your landing page doesn't convert the traffic you send it.

[Product name] analyzes your LP in 15 seconds and tells you exactly what's blocking conversions.

👉 Try it free → [Link]
```

**Social proof template (40-70 words):**
```
"I spent 3 months testing ads without understanding why nothing scaled.

LRS told me in 15 seconds that my hook scored 2/5. I changed the headline.

The next week: ROAS 3.8 instead of 1.4."

— [Name], ecom store owner (niche X)

→ Get your LRS score: [Link]
```

**Direct response template (20-40 words):**
```
Is your landing page ready for paid traffic?

Score /20 · Action plan · Rewrites generated in 15 seconds.

Used by [X] media buyers.

Try it now → [Link]
```"""},
            {"title": "🎯 How to write a headline that converts", "body": """**The 3 parts of a perfect headline:**

1. **Specific benefit** (not a feature) + **timeframe** + **no pain**
   - ❌ “Improve your ads with our AI tool”
   - ✅ “Double your ROAS in 7 days without changing your ad budget”

2. **Add a number**: specific numbers are 28% more memorable
   - ❌ “Save time on your audits”
   - ✅ “Audit your landing page in 15 seconds flat”

3. **Speak to the skeptic**: anticipate objection #1
   - ❌ “The tool that revolutionizes paid traffic”
   - ✅ “The first paid traffic audit tool that tells you exactly WHAT to fix”

**Quick test:** if your headline could work for any competitor, it's too generic. Rework it."""},
            {"title": "⚡ Writing a CTA that converts", "body": """**Rule: the CTA must be the logical continuation of the promise**

| ❌ Generic CTA | ✅ Specific CTA |
|---|---|
| “Buy now” | “Get my score /20 →” |
| “Learn more” | “See how to double my ROAS” |
| “Sign up” | “Start my free audit” |
| “Click here” | “Analyze my landing page now” |

**Add credible urgency:**
- Limited time: “Offer valid until [near date]”
- Limited stock: “Access limited to 50 users this month”
- Expiring bonus: “Free bonus if you join before midnight”

⚠️ Fake urgency destroys trust. Only use what's real and verifiable."""},
        ],
    },
}

CHANGELOG_VERSIONS = [
    {"version": "V2.6 — August 2026", "items": [
        "🆕 Bulk Audit: audit up to 20 URLs in 1 click + CSV import + CSV export of results",
        "🆕 Monitoring: score alerts (drop/gain ≥ 2 pts), score trend per page",
        "🆕 Automatic scheduled audits: checks every 7/14/30 days, run at startup",
        "🆕 Interactive onboarding: a getting-started guide for new users",
        "🆕 Monitoring tab with podium, comparison table and alert badge",
    ]},
    {"version": "V2.5", "items": [
        "🆕 Saved audit profiles (load / save your usual settings)",
        "🆕 Score delta: overall progress since the first audit, shown in History",
        "🆕 Recommendation implementation tracker (checkboxes + progress bar)",
        "🆕 Re-audit button: URL pre-filled automatically from History",
        "🆕 Multi-page projects: group a full funnel and audit it in 1 click",
        "🆕 Client PDF report: client-branded export with the recipient's name",
    ]},
    {"version": "V2.4", "items": [
        "🆕 Professional PDF report export (LRS branding, dark background, 4 pages)",
        "🆕 Comparison mode: audit 2 URLs side by side",
        "🆕 Before/After mode: compare an audit with a previous one",
        "🆕 In-app changelog",
        "🆕 2025 Benchmark Report (downloadable PDF, worth €27-47)",
    ]},
    {"version": "V2.3", "items": [
        "🆕 Persistent history (JSON), survives a page refresh",
        "🆕 Warning for JavaScript pages / thin content",
        "🆕 Visual score gauge (red/orange/green banner)",
        "🆕 Few-shot examples in the prompt, for more consistent scoring",
        "🆕 Automatic OpenAI retry (3 attempts with backoff)",
        "🆕 Page language detection (FR / EN / Mixed)",
    ]},
    {"version": "V2.2", "items": [
        "🔧 Fixed product page detection (/products/ was classified as Catalog)",
        "🆕 Adaptive scoring by page type (product page ≠ landing page)",
        "🆕 Preview of the scraped content (debug)",
        "🆕 Above-the-fold priority when scraping",
        "🆕 Score evolution chart in History",
        "🔧 Improved User-Agent for better compatibility",
    ]},
    {"version": "V2.1", "items": [
        "🔧 Bug 1: scoring too harsh for established brands → Established brand / New launch selector",
        "🔧 Bug 2: automatic page type detection (Sales, Catalog, SaaS, Blog, Lead Gen)",
        "🔧 Bug 3: granular recommendations: Quick Wins, Long Term, Priority Action #1 with how_exactly",
        "🆕 max_tokens raised to 4500",
    ]},
    {"version": "V2.0 — Initial release", "items": [
        "✅ Funnel Only / Ads Only / Full Risk audit",
        "✅ Hook/Offer/Trust/Friction scoring out of 20",
        "✅ Custom market context",
        "✅ Action plan, Rewrite, Ad Creative",
        "✅ .txt export",
        "✅ Pre-launch checklist",
        "✅ Session history",
        "✅ Password access gate",
        "✅ Streamlit Cloud deploy",
    ]},
]

BENCHMARK_INTRO = (
    "Average scores by niche (Ecom, SaaS, Lead Gen, Coaching…), the top 10 landing page mistakes, "
    "anatomy of a perfect page (18+/20 LRS Score), 6 quick wins you can apply in under an hour, "
    "CVR benchmarks by industry, the top 5 converting hooks of 2025, and a 30-day roadmap to go "
    "from 10 to 18/20."
)

BENCHMARK_STATS = [
    {"label": "Average Ecom score", "value": "11.2 / 20", "sub": "-1.8 vs SaaS · based on 200+ LRS audits"},
    {"label": "Mistake #1", "value": "Generic hook", "sub": "found on 78% of pages · fix: specific promise + a number"},
    {"label": "Average CVR uplift", "value": "+2.1 pts", "sub": "after quick wins · on LRS-audited pages ≥ 12/20"},
]
