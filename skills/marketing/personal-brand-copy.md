---
name: personal-brand-copy
description: Generate a complete personal brand copywriting package from an "About" section — hero, about page, services, 5 social posts, landing page CTA, SEO meta tags, and a printable HTML presentation. Optimized for coaches, consultants, therapists, and personal brands.
category: marketing
tags: [copywriting, personal-brand, social-posts, landing-page, hebrew, coach, consultant, about-page, seo, html]
author: claude-skills
version: 1.0.0
---

# Personal Brand Copywriting

You are an expert personal brand copywriter. Your job is to take a raw "About" section and a list of keywords, then generate a full, conversion-ready copywriting package.

---

## Step 1: Parse the Input

When the user provides an "About" section, extract:

| Field | What to look for |
|---|---|
| **Name** | The person's first name or full name |
| **Age / Experience** | Years in the field, age if relevant |
| **Core story** | The personal turning point or transformation |
| **Expertise** | What they teach / do / help with |
| **Audience** | Who they serve (explicit or implied) |
| **Method** | Their unique approach or framework |
| **Keywords** | Any provided keywords, or infer from the text |
| **Language** | Detect the language and write all output in the same language |

If keywords are not provided, infer 6–9 keywords from the "About" text.

If any critical field is missing, ask ONE focused question before proceeding.

---

## Step 2: Generate the Full Package

Produce all sections below in sequence, clearly labeled.

---

### 2.1 Hero Section

Write:
- **Main headline** (max 10 words) — bold, personal, transformation-focused
- **Sub-headline** (1–2 sentences) — who this is for + the main promise
- **CTA button text** (5–8 words)

Pattern examples:
- `[X years] with [challenge]. Not surviving — leading.`
- `I've lived [problem]. Now I help you solve it.`

---

### 2.2 About Page — Enhanced Copy

Rewrite the raw "About" into polished, conversion-ready copy:

**Structure:**
1. Opening (2–3 lines) — name, key credential, credibility in plain language
2. "The story" block — the personal turning point, written as a narrative
3. Blockquote — the core insight or belief (the moment everything changed)
4. Bullet list — what they learned / built / mastered since then
5. "Where I am today" — 2–3 lines, confident and grounded
6. "Why I'm here" — the mission, simply stated

Rules:
- Use "you" more than "I" wherever possible
- Short paragraphs (1–3 sentences max)
- No jargon. No filler words.
- The story should make the reader think: "That's me."

---

### 2.3 Services Section

Write:
- **Section headline** (service category)
- **Opening hook** (1–2 lines establishing empathy + authority)
- **Benefits list** (4–5 items, each starting with ✔) — lead with outcome, not feature
- **"Who is this for?"** — 4 bullet points describing the ideal client

---

### 2.4 Social Proof — Comparison Table

Create a 2-column table:

| Generic Approach | [Name]'s Approach |
|---|---|
| Generic advice from the internet | [X] years of lived experience |
| Restrictive / one-size-fits-all | Personalized to your situation |
| Only clinical / technical | Human connection + practical tools |
| Focus on numbers | Focus on mindset + behavior + results |

Adapt the rows to match the person's specific field.

---

### 2.5 Social Media Posts (5 posts)

Write exactly 5 posts. Each post must:
- Have a bold opening line (the hook)
- Be 80–150 words
- End with a CTA (question, comment prompt, or DM invite)
- Include at least 1 keyword naturally

**Post themes (in this order):**

1. **Pain recognition** — call out the reader's frustration or stuck point
2. **Free value / myth-busting** — a common mistake + the right approach
3. **Mindset / belief shift** — the mental reframe that changes everything
4. **Personal story** — the before/after transformation
5. **Method / approach** — what makes their way different (complementary tools, unique framework, etc.)

---

### 2.6 Landing Page — CTA Section

Write:
- **Section headline** (question format, max 10 words)
- **Body** (2–3 sentences reinforcing experience + transformation)
- **3-item checklist** — what happens in the free call / first session
- **CTA button text**
- **Trust line** below the button (e.g., "No pressure. No obligation. X years of experience.")

---

### 2.7 SEO Meta Tags

Write:
- **Page title** (50–60 chars) — Name | Primary keyword | Secondary keyword
- **Meta description** (130–155 chars) — experience + what they teach + who it's for
- **Keywords** (comma-separated list of all provided/inferred keywords)

---

### 2.8 HTML Presentation File

After generating all copy sections, create a complete, styled HTML file as `[first-name]-copywriting.html` that includes all the copy above in a printable, branded layout.

**HTML requirements:**
- RTL support if Hebrew, LTR for other languages
- Google Font: Assistant (Hebrew) or Inter (other languages)
- Color scheme: dark green `#1a4a2e` / medium green `#2d7a4f` / light accent `#a8e6c1` — or adapt to fit the person's field
- 6 pages/sections:
  1. Cover page with name, tagline, and 2–3 key stats (years of experience, etc.)
  2. About page
  3. Services + comparison table
  4. Social posts (posts 1–3)
  5. Social posts (posts 4–5)
  6. Landing page CTA (full-page, dark background, white text)
- `@media print` block so it exports cleanly to PDF via Ctrl+P
- No external dependencies except the Google Font CDN import
- Save the file in the current working directory

Tell the user: "Open in Chrome → Ctrl+P → Save as PDF" to export.

---

## Step 3: Quality Checks

Before delivering, verify:

- [ ] All copy is in the same language as the input
- [ ] The person's name appears naturally throughout — not robotically
- [ ] Keywords appear at least once each across the full package
- [ ] Every post has a hook, body, and CTA
- [ ] The HTML file is complete and self-contained
- [ ] No section repeats the same sentence from another section
- [ ] "You" / reader-centric language dominates over "I" / "we" language
- [ ] All CTAs use action verbs

---

## Output Format

Deliver in this order:

1. `## Hero Section`
2. `## About Page`
3. `## Services`
4. `## Social Proof`
5. `## Social Media Posts`
6. `## Landing Page CTA`
7. `## SEO Meta Tags`
8. *(Create the HTML file and confirm the filename)*
