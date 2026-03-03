# Director Mode Improvement Proposal

## Problem Statement

The current director mode PLAN phase requires the AI to produce both:
1. **Structured data** (JSON schema for `director_complete_plan` tool)
2. **Rich narrative content** (detailed explanations, decision rationale, trade-off analysis)

This creates a fundamental conflict that impacts the quality and reliability of the planning phase.

### Issues with Current Approach

#### 1. JSON Schema Limitations
- **Rigid structure** - requires exact schema compliance
- **Custom fields may be silently dropped** - AI adds `key_decisions` array but tool may not preserve it
- **No support for formatting** - markdown, code blocks, tables all lost in JSON
- **Large nested JSON is error-prone** - one missing quote/bracket breaks everything
- **Escaping complexity** - quotes, newlines, special characters must be escaped

#### 2. Content Quality vs Structure Trade-off
- Rich explanations need formatting (bullet points, emphasis, tables, code examples)
- JSON escaping makes content hard to read and write
- Tool response truncation may hide errors or content
- AI cannot verify what user actually sees vs what was sent

#### 3. Debugging Challenges
- When `director_complete_plan` fails, unclear why (no detailed error messages)
- No visibility into whether custom fields are preserved or dropped
- Can't tell if content was truncated or rejected silently
- AI doesn't know what user saw vs what was sent
- Tool response: "Plan rejected" or "Plan cancelled" with no context

#### 4. Real-World Example (This Session)
```
User: "Build music learning SaaS with decision rationale"
AI: Sends detailed JSON with key_decisions arrays for each slice
Tool: "Director plan approval cancelled"
User: "I didn't see any decision rationale"
AI: "I sent it in the JSON but can't verify what you saw"
Result: Confusion, wasted time, unclear what went wrong
```

---

## Proposed Solutions

### Option 1: Separate Plan Document + Structured Slices ⭐ RECOMMENDED

#### Workflow
```
1. AI writes comprehensive plan as markdown document
   Location: .clarity/plans/<session_id>_plan.md
   
2. Plan document includes:
   - Executive summary
   - Tech stack decisions with full rationale
   - Architecture diagrams (mermaid)
   - Decision tables comparing alternatives
   - Trade-off analysis
   - Risk assessment
   - Implementation approach
   
3. AI calls director_complete_plan with MINIMAL JSON:
   {
     "summary": "Brief one-line overview",
     "plan_document": ".clarity/plans/<session_id>_plan.md",
     "slices": [
       {
         "title": "Foundation & Multi-Tenant Infrastructure",
         "description": "Set up FastAPI, PostgreSQL, multi-tenant middleware",
         "files_to_create": ["backend/app/main.py", ...],
         "files_to_modify": [],
         "test_criteria": ["Server starts", "Migrations run", ...],
         "decision_docs": [
           "docs/decisions/001-tech-stack.md",
           "docs/decisions/002-multi-tenancy.md"
         ]
       },
       // ... more slices
     ]
   }
   
4. User reviews rich markdown plan (formatted, easy to read)

5. User approves/rejects with feedback

6. On approval, slices are used for execution tracking
```

#### Benefits
- ✅ **Rich content in markdown** - AI's strength, proper formatting
- ✅ **Simple JSON** - less error-prone, easier to validate
- ✅ **Decisions documented in version control** - can be reviewed, diffed, referenced
- ✅ **Plan readable even if tool fails** - file exists independently
- ✅ **Matches real-world workflow** - RFC/design doc → implementation tickets
- ✅ **Easy to iterate** - just edit markdown file and resubmit
- ✅ **Better debugging** - can inspect plan file directly
- ✅ **Supports diagrams** - mermaid, ASCII art, tables

#### Implementation Requirements
1. **Add `plan_document` field** to `director_complete_plan` tool schema (optional string)
2. **Allow `write_file` in PLAN mode** for `.clarity/plans/*.md` files only (whitelist)
3. **UI enhancement**: Display markdown plan prominently in approval screen
4. **UI enhancement**: Show slices as summary/checklist below plan
5. **Optional**: Add `decision_docs` array to slice schema (list of markdown files)
6. **Optional**: Auto-generate ADR (Architecture Decision Record) files during planning

#### Example Plan Document Structure
```markdown
# Music Learning Academy SaaS - Implementation Plan

## Executive Summary
Build a multi-tenant SaaS platform for music academies with 6 vertical slices...

## Tech Stack Decisions

### Backend: FastAPI vs Django vs Flask
**Chosen:** FastAPI

**Rationale:**
- Native async/await support (critical for WebRTC signaling, video streaming)
- Automatic OpenAPI documentation (accelerates frontend development)
- 3x faster than Flask in benchmarks
- Modern Python 3.10+ features (type hints, pattern matching)

**Alternatives Considered:**
| Option | Pros | Cons | Why Not Chosen |
|--------|------|------|----------------|
| Django | Mature, batteries-included | Async support still maturing, heavier | Better for monoliths, not API-first SaaS |
| Flask | Simple, mature | No native async, needs extensions | Slower performance, more boilerplate |
| Node.js | Good async support | Different ecosystem | Python better for future ML features |

**Trade-offs:** FastAPI is newer (less mature) but async benefits outweigh this.

### Database: PostgreSQL vs MySQL vs MongoDB
...

## Implementation Slices

### Slice 1: Foundation & Multi-Tenant Infrastructure
**Goal:** Set up project structure, database, multi-tenant middleware

**Files to Create:**
- `backend/app/main.py` - FastAPI entry point
- `backend/app/core/database.py` - PostgreSQL connection
- ...

**Test Criteria:**
- [ ] Server starts and responds to /health
- [ ] Database migrations run successfully
- [ ] Tenant middleware extracts subdomain
...
```

---

### Option 2: Iterative Approval Flow

#### Workflow
```
1. AI presents plan as formatted markdown in chat (not as file)
2. User reads and provides feedback in conversation
3. AI revises based on feedback
4. Iterate until user is satisfied
5. User explicitly approves: "looks good, proceed"
6. AI converts approved plan to minimal JSON
7. AI calls director_complete_plan
8. Execution begins
```

#### Benefits
- ✅ User sees full plan before commitment
- ✅ Natural conversation flow
- ✅ AI can use formatting, tables, emphasis in chat
- ✅ Less risk of tool failures hiding content

#### Drawbacks
- ❌ Requires manual approval step (more user interaction)
- ❌ Plan not automatically saved to file (lost in chat history)
- ❌ Harder to track plan versions
- ❌ Can't reference plan later

---

### Option 3: Enhance JSON Schema (Keep Everything in JSON)

#### Approach
Add explicit `decisions` field to slice schema with full type definitions:

```typescript
interface DirectorPlan {
  summary: string;
  slices: Slice[];
}

interface Slice {
  title: string;
  description: string;
  files_to_create: string[];
  files_to_modify: string[];
  test_criteria: string[];
  decisions?: Decision[];  // NEW - explicitly supported
}

interface Decision {
  question: string;           // "What backend framework to use?"
  chosen: string;             // "FastAPI"
  rationale: string;          // Why this was chosen (max 500 chars)
  alternatives: Alternative[]; // Other options considered
  trade_offs: string;         // What we're giving up (max 300 chars)
}

interface Alternative {
  option: string;        // "Django"
  pros: string;          // Strengths (max 200 chars)
  cons: string;          // Weaknesses (max 200 chars)
  why_not_chosen: string; // Specific reason (max 200 chars)
}
```

#### Implementation Requirements
1. **Update tool schema** to explicitly include `decisions` field
2. **Add validation** for required fields and character limits
3. **Echo back** what was received: "Received plan with 6 slices, 24 decisions"
4. **Better error messages**: "Slice 3 missing required field: test_criteria"
5. **UI enhancement**: Display decisions in expandable sections

#### Benefits
- ✅ Keeps everything in one place (single source of truth)
- ✅ Explicit schema validation
- ✅ AI knows exactly what fields are supported
- ✅ Structured data easier to query/filter

#### Drawbacks
- ❌ Still limited by JSON formatting (no markdown, code blocks)
- ❌ Large nested structures error-prone
- ❌ Hard to read/write complex explanations in JSON strings
- ❌ Character limits may force oversimplification
- ❌ No support for diagrams, tables, formatted code

---

### Option 4: Hybrid - Markdown References in JSON

#### Workflow
```
1. AI writes decision documents as markdown files:
   docs/decisions/001-tech-stack.md
   docs/decisions/002-multi-tenancy.md
   docs/decisions/003-authentication.md
   etc.

2. AI calls director_complete_plan with references:
   {
     "summary": "6-slice MVP...",
     "slices": [{
       "title": "Foundation",
       "description": "...",
       "files_to_create": [...],
       "test_criteria": [...],
       "rationale_doc": "docs/decisions/001-tech-stack.md",
       "rationale_summary": "FastAPI for async, PostgreSQL for multi-tenancy, Docker for consistency"
     }]
   }

3. UI shows summary inline, links to full decision docs
```

#### Benefits
- ✅ Best of both worlds (structured + rich content)
- ✅ Structured data for execution tracking
- ✅ Rich docs for understanding decisions
- ✅ Decisions in version control (ADR pattern)
- ✅ Can reference decisions across slices

#### Drawbacks
- ❌ More complex implementation (need to manage file references)
- ❌ Requires file creation before tool call
- ❌ Need to validate referenced files exist
- ❌ Potential for orphaned files

---

## Comparison Matrix

| Aspect | Option 1: Separate Doc | Option 2: Iterative | Option 3: Enhanced JSON | Option 4: Hybrid |
|--------|------------------------|---------------------|-------------------------|------------------|
| **Rich formatting** | ✅ Full markdown | ✅ In chat | ❌ Limited | ✅ In separate files |
| **Structured data** | ✅ Simple JSON | ✅ After approval | ✅ Comprehensive | ✅ JSON + refs |
| **Version control** | ✅ Plan file | ❌ Chat only | ✅ In tool data | ✅ Decision files |
| **Easy to debug** | ✅ Inspect file | ⚠️ Check chat | ❌ JSON parsing | ⚠️ Multiple files |
| **Implementation complexity** | ⭐ Low | ⭐ Lowest | ⭐⭐ Medium | ⭐⭐⭐ High |
| **User experience** | ✅ Read formatted doc | ✅ Natural flow | ⚠️ Read JSON | ✅ Inline + links |
| **AI ease of use** | ✅ Write markdown | ✅ Write markdown | ❌ Complex JSON | ⚠️ Multiple files |
| **Failure resilience** | ✅ File persists | ❌ Lost in chat | ❌ All or nothing | ⚠️ Partial |

---

## Recommendation: **Option 1** (Separate Plan Document)

### Why This is the Best Choice

1. **Aligns with industry best practices**
   - Real teams write design docs (RFC, ADR) before implementation
   - Separates planning (narrative) from execution (structured)
   - Matches how humans naturally think and communicate

2. **Leverages AI strengths**
   - AI excels at writing clear, formatted explanations
   - Markdown is natural language-friendly
   - Can include diagrams, tables, code examples

3. **Reduces tool complexity**
   - Simple JSON schema (less error-prone)
   - Clear separation of concerns
   - Easier to validate and debug

4. **Better user experience**
   - Read formatted plan with proper headings, emphasis, tables
   - Can skim, search, reference later
   - Version controlled (can diff changes)

5. **Debuggable and resilient**
   - If tool fails, plan file still exists
   - Can inspect file directly
   - Can manually edit if needed

6. **Extensible**
   - Easy to add diagrams (mermaid)
   - Can link to external resources
   - Can include code examples with syntax highlighting

### Implementation Priority

**Phase 1: Minimal Viable Change**
- Add `plan_document` field to `director_complete_plan` (optional)
- Allow `write_file` in PLAN mode for `.clarity/plans/*.md` only
- UI displays plan document if provided (fallback to summary if not)

**Phase 2: Enhanced Experience**
- Add `decision_docs` array to slice schema
- UI shows decision docs as expandable sections
- Auto-generate table of contents for plan

**Phase 3: Advanced Features**
- Mermaid diagram rendering in plan docs
- Diff view for plan revisions
- Export plan as PDF/HTML

---

## Example Workflow Comparison

### Current Workflow (Problematic)
```
1. User: "Build music learning SaaS with decision rationale"
2. AI: *attempts to fit everything into JSON*
3. AI: Calls director_complete_plan with massive nested JSON:
   {
     "slices": [{
       "key_decisions": [{
         "decision": "FastAPI over Django/Flask",
         "rationale": "Native async/await support...",
         "alternatives": {
           "Django": "Excellent for traditional web apps but...",
           "Flask": "Mature and simple but lacks native async..."
         }
       }]
     }]
   }
4. Tool: "Director plan approval cancelled"
5. User: "I didn't see any decision rationale"
6. AI: "I sent it in key_decisions but tool may have dropped it"
7. Result: ❌ Confusion, wasted time, unclear what went wrong
```

### Proposed Workflow (Option 1)
```
1. User: "Build music learning SaaS with decision rationale"
2. AI: *writes .clarity/plans/session_123_plan.md*
   - Executive summary
   - Tech stack decisions with tables comparing alternatives
   - Architecture diagrams
   - Implementation slices
   - Risk assessment
3. AI: Calls director_complete_plan:
   {
     "summary": "6-slice MVP: Foundation, Auth, Scheduling, Live Video, Lessons, Payments",
     "plan_document": ".clarity/plans/session_123_plan.md",
     "slices": [
       {
         "title": "Foundation & Multi-Tenant Infrastructure",
         "description": "FastAPI, PostgreSQL, Docker",
         "files_to_create": ["backend/app/main.py", ...],
         "test_criteria": ["Server starts", "Migrations run", ...]
       },
       // ... 5 more slices
     ]
   }
4. UI: Displays formatted markdown plan with TOC, syntax highlighting
5. User: Reads plan, sees decision tables, diagrams
6. User: "Change PostgreSQL to MySQL" (feedback)
7. AI: Updates plan document, resubmits
8. User: Approves
9. Result: ✅ Clear plan, documented decisions, smooth approval
```

---

## Technical Considerations

### Security
- **Whitelist file paths**: Only allow writes to `.clarity/plans/*.md` in PLAN mode
- **Validate file content**: Ensure markdown only (no script injection)
- **Size limits**: Max 100KB per plan document (prevent abuse)

### Performance
- **Lazy loading**: Don't load plan document until user requests it
- **Caching**: Cache rendered markdown to avoid re-parsing
- **Streaming**: For large plans, stream content progressively

### Backward Compatibility
- **Optional field**: `plan_document` is optional, existing code works
- **Fallback**: If no plan document, show summary as before
- **Migration**: Existing plans continue to work unchanged

---

## Questions for Dev Team

1. **Is there a size limit** on the `slices` parameter in `director_complete_plan`?
2. **Are custom fields preserved** (like `key_decisions`) or silently dropped?
3. **What does the user actually see** when `director_complete_plan` is called?
4. **Can we add `plan_document` field** to reference a markdown file?
5. **Can we whitelist `write_file`** in PLAN mode for `.clarity/plans/*.md` only?
6. **What caused "Plan approval cancelled"** in this session? (debugging info)
7. **Is there logging** of what JSON was received by the tool?
8. **Should decision rationale be** in JSON schema or separate markdown files?

---

## Success Metrics

After implementing Option 1, we should see:

- ✅ **Fewer plan rejections** due to JSON errors
- ✅ **Higher user satisfaction** with plan clarity
- ✅ **Faster iteration** on plans (easier to edit markdown than JSON)
- ✅ **Better documentation** (plans are version controlled)
- ✅ **Reduced debugging time** (can inspect plan files directly)
- ✅ **More comprehensive plans** (AI not limited by JSON constraints)

---

## Conclusion

The root issue is asking AI to produce **structured data** (JSON) when the task requires **rich narrative** (explanations, comparisons, trade-offs, diagrams).

**Solution:** Separate concerns
- **Markdown** for planning and decision rationale (human-readable, AI-friendly)
- **JSON** for execution tracking (machine-readable, structured)

This matches how real development teams work (design docs → tickets) and plays to the strengths of both AI (writing explanations) and structured tools (tracking progress).

**Recommendation:** Implement Option 1 (Separate Plan Document) in phases, starting with minimal changes to prove the concept.

---

**Document Version:** 1.0  
**Author:** AI Coding Agent  
**Date:** 2025-02-15  
**Context:** Director Mode PLAN phase improvement proposal based on real-world usage issues
