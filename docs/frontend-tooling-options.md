# Frontend Tooling Options — Music Learning Academy

## Context

We're building a multi-tenant SaaS platform for music academies. Each academy gets a public-facing landing page (`/join/<slug>/`) that serves as their storefront — the page academy owners share with prospective students and parents.

### Current Stack
- **Backend:** Django 4.2 + Django Templates (server-rendered)
- **CSS:** Tailwind CSS via CDN (`<script src="https://cdn.tailwindcss.com">`)
- **Components:** DaisyUI 4.12 via CDN (`<link href="...daisyui...">`)
- **Interactivity:** HTMX 2.0 (server-driven, no client-side state)
- **Build step:** None — everything loaded via CDN, no npm/node

### Why We're Evaluating
- The landing page is every academy's first impression — it must look polished and professional
- DaisyUI's default components make sites look generic (the "template site" problem)
- Tailwind CDN ships ~300KB of unused CSS and doesn't support custom plugins/fonts
- Dynamic per-academy branding (colors) currently works via runtime Tailwind config — this approach has limitations
- Competitors like Artium Academy have polished, custom-designed pages with animations, video testimonials, and rich visual design

### What We Need From the Frontend
1. **Per-academy theming** — each academy has a `primary_color` (hex) that drives buttons, accents, badges
2. **Professional landing pages** — hero, course grid, instructor cards, pricing, signup form
3. **Responsive** — mobile-first, works on all devices
4. **Accessible** — proper heading hierarchy, aria labels, keyboard navigation
5. **Fast** — landing pages are public-facing and SEO-relevant
6. **Maintainable** — coding agents (AI) frequently edit templates, so the system needs to be straightforward

---

## Options

### Option A: Keep Tailwind CDN + DaisyUI (Current Setup)

No changes. Continue loading Tailwind and DaisyUI from CDN with no build step.

**How dynamic theming works:** Tailwind config is set at runtime via inline `<script>` in `base.html`:
```html
<script>
    tailwind.config = {
        theme: { extend: { colors: {
            primary: '{{ current_academy.primary_color|default:"#6366f1" }}',
        }}}
    }
</script>
```

| Pros | Cons |
|------|------|
| Zero setup — already working | Every DaisyUI site looks the same out of the box |
| Dynamic `primary_color` per academy works at runtime | Tailwind CDN is ~300KB (no tree-shaking or purging) |
| No npm, no node, no build pipeline to maintain | Can't use custom Tailwind plugins, fonts, or deep config |
| Any developer/AI agent can edit templates immediately | Limited to DaisyUI's predefined component set |
| Hot reload = just refresh the browser | No PostCSS, no autoprefixer, no CSS nesting |
| Simplest possible setup | Not production-grade for performance-sensitive pages |

**Best for:** Rapid prototyping, internal/admin pages, teams that want zero frontend complexity.

**Not ideal for:** Public-facing marketing pages that need to look unique and load fast.

---

### Option B: Vite + Tailwind + DaisyUI (Compiled Build)

Add a frontend build pipeline using Vite. Tailwind and DaisyUI are installed as npm packages and compiled to a static CSS file that Django serves.

**How dynamic theming works:** Switch from runtime Tailwind config to CSS custom properties:
```css
/* Compiled Tailwind config references CSS variables */
:root { --color-primary: #6366f1; }
```
```html
<!-- Django template sets the variable per academy -->
<style>:root { --color-primary: {{ academy.primary_color }}; }</style>
```

**Setup required:**
- `package.json` with `tailwindcss`, `daisyui`, `vite`, `postcss`, `autoprefixer`
- `vite.config.js` + `tailwind.config.js` + `postcss.config.js`
- `npm run dev` (watch mode) during development alongside `python manage.py runserver`
- `npm run build` in CI/CD and deployment pipeline
- Django `{% static 'dist/main.css' %}` instead of CDN links

| Pros | Cons |
|------|------|
| Tree-shaken CSS (~10-20KB vs ~300KB) | Adds npm/node as a project dependency |
| Full Tailwind config (custom fonts, animations, spacing, plugins) | Need to run `npm run build` before deploy |
| PostCSS plugins (autoprefixer, nesting, minification) | Dev workflow requires two processes (Vite watcher + Django) |
| DaisyUI still available as a base component set | Dynamic theming requires CSS variables approach (slightly more work) |
| Can progressively add custom components alongside DaisyUI | Coding agents need to understand the build pipeline |
| Production-grade performance | Initial setup effort (~1-2 hours) |
| Can add `@apply` directives for reusable utility classes | |

**Best for:** Teams ready for a professional build pipeline while keeping DaisyUI as a component foundation. Good middle ground.

**Migration path:** Can be done incrementally — replace CDN links with compiled output, keep all existing templates working.

---

### Option C: Vite + Tailwind + Fully Custom Components (Drop DaisyUI)

Replace DaisyUI entirely with hand-crafted Tailwind components. Build a custom design system from scratch, inspired by reference sites like Artium Academy.

**How it works:** Create a library of reusable template partials (Django `{% include %}`) styled with Tailwind utilities. No external component library — you own every pixel.

**Example custom component:**
```html
<!-- templates/components/_course_card.html -->
<div class="group relative overflow-hidden rounded-2xl bg-white shadow-md
            hover:shadow-xl transition-all duration-300">
    <div class="aspect-video overflow-hidden">
        <img src="{{ course.thumbnail.url }}" class="w-full h-full object-cover
             group-hover:scale-105 transition-transform duration-500">
    </div>
    <div class="p-6">
        <span class="text-xs font-semibold uppercase tracking-wider text-primary">
            {{ course.instrument }}
        </span>
        <h3 class="mt-2 text-lg font-bold">{{ course.title }}</h3>
        <!-- ... -->
    </div>
</div>
```

| Pros | Cons |
|------|------|
| Fully unique design — no "template site" look | Most work upfront — must design and build every component |
| Total control over every pixel, animation, transition | No component library to lean on for common patterns |
| Can match any reference design (Artium, Tonara, etc.) | Requires strong design sense or a Figma/design reference |
| Smallest possible CSS bundle (only what you use) | Longer development time per new page or feature |
| Premium, professional feel | Higher maintenance — you own the entire component set |
| No dependency on DaisyUI's update cycle | Consistency requires discipline (design tokens, naming conventions) |

**Best for:** Standing out visually, competing with funded startups on design quality. Best long-term option if design differentiation matters.

**Risk:** Without a designer or Figma reference, "custom" can mean "inconsistent." Need clear design tokens (colors, spacing, typography, shadows, border-radius) defined upfront.

---

### Option D: Vite + Tailwind + Alpine.js + Headless Components

Use Tailwind for all styling, add Alpine.js for lightweight client-side interactivity, and use headless UI patterns for accessible interactive components (dropdowns, modals, tabs, accordions).

**How it works:** Alpine.js handles client-side state (toggle menus, tabs, carousels) while HTMX continues to handle server communication. Headless components provide accessible behavior without styling — you style everything with Tailwind.

**Example:**
```html
<!-- Alpine.js for client-side tab switching -->
<div x-data="{ tab: 'monthly' }">
    <button @click="tab = 'monthly'" :class="tab === 'monthly' && 'bg-primary text-white'">
        Monthly
    </button>
    <button @click="tab = 'annual'" :class="tab === 'annual' && 'bg-primary text-white'">
        Annual
    </button>
    <div x-show="tab === 'monthly'"><!-- monthly plans --></div>
    <div x-show="tab === 'annual'"><!-- annual plans --></div>
</div>
```

| Pros | Cons |
|------|------|
| Full design control (no DaisyUI styling constraints) | Two JS interaction models to manage (HTMX + Alpine.js) |
| Accessible interactive components (focus traps, aria attributes) | Adds ~15KB for Alpine.js |
| Lightweight — Alpine.js is much smaller than React/Vue | Team needs to learn Alpine.js patterns |
| Good for landing page interactions (carousels, tabs, accordions) | More complex than pure HTMX for simple cases |
| Tailwind for styling = complete visual control | Need to decide which interactions use HTMX vs Alpine |
| Battle-tested accessibility patterns | Slightly more JS code in templates |

**Best for:** Custom design with accessible, polished interactions (tab switchers, animated carousels, pricing toggles) without going full SPA.

**Note on HTMX + Alpine.js coexistence:** This is a well-documented pattern. HTMX handles server communication (forms, navigation, partial updates). Alpine.js handles client-only UI state (toggles, tabs, animations). They don't conflict.

---

## Comparison Matrix

| Criteria | A: CDN (Current) | B: Vite + DaisyUI | C: Vite + Custom | D: Vite + Alpine |
|----------|:-:|:-:|:-:|:-:|
| **Setup effort** | None | Medium | High | Medium |
| **Design control** | Low | Medium | Full | High |
| **Page load performance** | Poor (300KB CSS) | Good (10-20KB) | Best | Good |
| **Component quality** | Generic (DaisyUI) | DaisyUI + custom | Fully custom | Custom + accessible |
| **Dynamic theming** | Easy (runtime) | CSS variables | CSS variables | CSS variables |
| **Interactivity** | HTMX only | HTMX only | HTMX only | HTMX + Alpine.js |
| **Maintenance burden** | Lowest | Low | Highest | Medium |
| **Dev workflow** | 1 process | 2 processes | 2 processes | 2 processes |
| **Unique look** | No | Somewhat | Yes | Yes |
| **Migration effort** | N/A | Low | High | Medium |

---

## Recommendations by Scenario

**"We want to move fast and iterate on features"** → Option B
- Upgrade the build pipeline, keep DaisyUI for speed, customize where it matters (landing page, pricing)

**"We want to look premium and compete on design"** → Option C
- Drop DaisyUI, build custom components, invest in a design reference (Figma or a benchmark site)

**"We want polish + interactions without heavy JS"** → Option D
- Best of both worlds: custom design + Alpine.js for landing page interactions (carousels, tabs, animated counters)

**"We want to ship the landing page this week"** → Option A (then migrate to B or D)
- Build with current stack, upgrade the tooling in a separate sprint

---

## Questions to Consider

1. **Do we have a design reference?** (Figma, a competitor's site, a theme we like?) — This matters more than which tooling we pick. Beautiful code with no design direction = inconsistent UI.

2. **How often do we build new pages?** — If we're mostly iterating on existing pages, the tooling matters less. If we're building 10+ new pages, a proper build pipeline pays for itself.

3. **Do we need client-side interactions on the landing page?** — Carousels, animated counters, tab switchers, scroll animations. If yes, Alpine.js (Option D) is worth adding. If not, Options B or C are simpler.

4. **What's our deployment pipeline?** — Adding `npm run build` to the deployment means Docker, CI/CD, and `build.sh` all need updating. Not hard, but needs to be planned.

5. **Can we do a phased migration?** — Start with Option B (Vite + DaisyUI), then progressively replace DaisyUI components with custom ones on high-visibility pages (landing page, pricing) while keeping DaisyUI for internal admin pages. This is the lowest-risk path to Option C.
