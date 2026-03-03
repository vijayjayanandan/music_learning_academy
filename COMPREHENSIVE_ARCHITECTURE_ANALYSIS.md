# Music Learning Academy - Comprehensive Architecture Analysis & Implementation Plan

## Executive Summary

This document presents a comprehensive architectural analysis and implementation roadmap for building a world-class online music learning academy platform. Based on deep research into existing platforms, WebRTC optimization, AI music analysis, and educational best practices, this plan enhances the original architecture with critical improvements for scalability, user experience, and competitive differentiation.

**Key Improvements Identified:**
- Enhanced WebRTC audio pipeline specifically optimized for music (up to 520kbps stereo, <50ms latency)
- Advanced music notation system with MusicXML support
- AI-powered practice feedback using TensorFlow.js (SPICE, CREPE models)
- Comprehensive curriculum management aligned with National Music Standards
- Multi-modal pricing strategies (subscriptions, packages, pay-per-lesson)
- COPPA compliance framework for child safety
- Microservices evolution path with gRPC communication
- Advanced performance optimization strategies

---

## 1. Research Findings Summary

### 1.1 Market Analysis - Leading Music Education Platforms

#### QuaverEd (Industry Leader)
- **Impact**: 28,000+ educators, tens of millions of students
- **Adoption**: 15 of 30 largest US school districts
- **Features**: Complete K-5 curriculum with 1000+ interactive resources
- **Key Strength**: Alignment with National Music Standards

#### Key Platform Features Identified:
1. **Real-time Assessment**: Live feedback during lessons (Noteflight)
2. **LMS Integration**: Canvas, Moodle, Blackboard synchronization
3. **Standards Alignment**: National Core Arts Standards compliance
4. **Multi-modal Content**: Video, interactive exercises, sheet music
5. **Progress Tracking**: Portfolio-based assessment systems

### 1.2 WebRTC Audio Optimization for Music

#### Critical Discovery: Standard WebRTC is Insufficient for Music

**Default WebRTC Audio:**
- Mono audio, ~42 kb/s
- Voice-optimized with aggressive processing
- NOT suitable for music education

**Music-Optimized Configuration:**
```javascript
{
  echoCancellation: false,     // Preserves instrument harmonics
  noiseSuppression: false,     // Prevents musical note filtering
  autoGainControl: false,      // Maintains dynamic range
  channelCount: 2,             // Stereo for spatial awareness
  sampleRate: 48000,           // Professional audio quality
  latency: 0,                  // Minimize delay
  // SDP enhancement for 520kbps stereo
  maxaveragebitrate: 510000
}
```

**Opus Codec for Music:**
- Industry standard for WebRTC
- 64-128 kbps recommended for high-fidelity music
- Low latency with excellent quality trade-off

#### JackTrip WebRTC - Game Changer
- **Purpose**: Multi-machine network music performance
- **Innovation**: Routes MediaStream through RTCDataChannel
- **Benefit**: Bypasses encoding/buffering delay
- **Quality**: Uncompressed audio, ultra-low latency
- **Use Case**: Real-time ensemble/collaboration

**Implementation Recommendation:** Start with optimized Opus, add JackTrip-style data channel routing for premium "Studio Quality" tier.

### 1.3 Music Notation Systems

#### VexFlow (Primary Choice)
- **Type**: Open-source HTML5 music engraving
- **Technology**: TypeScript/JavaScript, Canvas/SVG
- **Status**: Actively maintained, industry-standard
- **Limitation**: No native MusicXML support

#### MusicXML Integration
**Community Solutions:**
1. **vexflow-musicxml plugins**: Multiple forks available
2. **Open Sheet Music Display**: Custom engine built on VexFlow
3. **SymphoniaIO/web-musicxml-editor**: Import/export capability

**Recommendation:** Use VexFlow + vexflow-musicxml plugin for import, implement custom export functionality.

#### Additional Notation Needs:
- **ABC Notation**: Text-based, easier for folk/traditional music
- **Guitar Tabs**: Essential for guitar courses
- **Chord Diagrams**: Visual chord representations
- **Interactive Playback**: Sync audio with scrolling notation

### 1.4 AI/ML Music Analysis

#### TensorFlow.js Models Available:

**1. SPICE (Self-Supervised Pitch Estimation)**
- **Source**: TensorFlow Hub official
- **Capability**: Recognize fundamental pitch from mixed audio
- **Advantage**: Works with noise and backing instruments
- **Platforms**: Web (TensorFlow.js), Mobile (TF Lite)

**2. CREPE (Convolutional Representation for Pitch Estimation)**
- **Source**: ML5.js library
- **Strength**: High accuracy for monophonic pitch
- **Integration**: Simple JavaScript API

**3. Essentia.js**
- **Features**:
  - Beat/tempo estimation (BPM)
  - Pitch in monophonic/polyphonic audio
  - Rhythm analysis
  - Chord/tonality recognition
- **Advantage**: Comprehensive music analysis toolkit

#### AI Features to Implement:

**Phase 1 - Core Analysis:**
- Pitch accuracy detection (cents deviation)
- Rhythm/tempo analysis
- Note onset detection

**Phase 2 - Advanced Analysis:**
- Tone quality assessment
- Expression/dynamics evaluation
- Style comparison

**Phase 3 - Intelligent Feedback:**
- Personalized practice plan generation
- Progress prediction
- Automated transcription
- Intelligent recommendations

### 1.5 Educational Best Practices

#### National Music Education Standards 2024

**Four Pillars:**
1. **Creating**: Composing and improvising
2. **Performing**: Singing, playing instruments, ensemble work
3. **Responding**: Analyzing and interpreting music
4. **Connecting**: Relating music to other disciplines

**Implementation in Platform:**
- Curriculum builder aligned with standards
- Assessment rubrics based on competency frameworks
- Progress tracking mapped to learning objectives
- Portfolio-based evidence collection

#### Assessment Strategies:
- **Formative**: Continuous practice feedback
- **Summative**: Performance evaluations
- **Peer Assessment**: Student showcases with reviews
- **Self-Assessment**: Reflection journals
- **Rubric-based**: Standardized criteria

### 1.6 Payment & Pricing Models

#### Escrow Best Practices:
- Hold funds until service completion
- Multi-split payments (platform fee, teacher earning)
- Dispute resolution period (7 days recommended)
- Automated release after criteria met

#### Pricing Strategies:

**1. Subscription Model** (Recommended Primary)
- Monthly: $10-50/month for unlimited content access
- Annual: 15-20% discount
- Freemium: Free basic + Premium features

**2. Pay-Per-Lesson**
- Range: $20-100 per lesson (45-60 min)
- Package discounts: 5-lesson, 10-lesson bundles
- Trial lesson: First lesson 50% off

**3. Tiered Pricing**
- **Basic**: $29/mo - Group lessons, recorded content
- **Standard**: $79/mo - 1:1 lessons (4/month), AI feedback
- **Premium**: $149/mo - Unlimited lessons, studio quality audio, priority support

**4. Hybrid Model** (Best for Marketplace)
- Free course browsing
- Individual course purchase: $50-500
- OR Subscription for unlimited access
- Plus premium features (AI tools, certification)

**Platform Commission:**
- Industry standard: 15-30%
- Our recommendation: 20% (competitive, sustainable)

### 1.7 COPPA Compliance Requirements

#### Critical for Under-13 Users:

**Must Have:**
1. **Age Verification**: Gate before data collection
2. **Parental Consent System**:
   - Verifiable consent mechanism
   - Email + credit card verification
   - Or printed consent form + faxback
3. **School Exception**:
   - Schools can consent on behalf of parents
   - BUT only for educational use
   - Cannot share data for commercial purposes

**Implementation Requirements:**
- Clear, comprehensive privacy policy
- Limited data collection (only what's necessary)
- No behavioral advertising to children
- Secure data storage with encryption
- Data retention limits
- Parental access to child's data
- Parental ability to delete data

**Platform Features Needed:**
- Age gate at registration
- Parent account linking to child accounts
- Separate consent flows for <13
- Data access portal for parents
- Restricted chat features for children
- Content moderation system

### 1.8 NestJS Microservices & Scalability

#### Architecture Evolution Path:

**Phase 1: Modular Monolith** (0-10K users)
- Single NestJS application
- Clear module boundaries
- Shared database
- Easy development and debugging

**Phase 2: Selective Extraction** (10K-100K users)
- Extract high-load services first:
  - Media/WebRTC service
  - Practice analysis service
  - Notification service
- Keep core business logic in monolith

**Phase 3: Full Microservices** (100K+ users)
- Complete service decomposition
- gRPC for inter-service communication
- Event-driven architecture with message queue
- Distributed tracing (Jaeger)

#### Performance Optimization Strategies:

**Database (PostgreSQL):**
1. **Read Replicas**: Separate read/write traffic
2. **Connection Pooling**: pgBouncer (up to 10x improvement)
3. **Query Optimization**:
   - EXPLAIN ANALYZE for slow queries
   - Proper indexing strategy
   - Materialized views for complex aggregations
4. **Partitioning**: Time-series data (practice logs, analytics)
5. **JSONB Optimization**: GIN indexes for JSON queries

**Caching Strategy (Redis):**
1. **L1 - Application Cache**: In-memory cache per instance
2. **L2 - Redis Cache**: Shared across instances
3. **L3 - CDN**: Static assets and media

**Cache Patterns:**
- User sessions: 7-day TTL
- Course catalog: 1-hour TTL
- Teacher availability: 5-min TTL
- Practice analytics: 15-min TTL

**Horizontal Scaling:**
- Stateless application servers
- Session store in Redis
- File uploads to object storage (MinIO/S3)
- WebRTC media servers (Janus, Mediasoup) scaled independently

---

## 2. Current Architecture Assessment

### 2.1 Strengths of Existing Design

✅ **Solid Foundation:**
- Modern TypeScript stack (NestJS + Next.js)
- PostgreSQL with proper normalization
- Docker/Kubernetes deployment path
- Comprehensive module structure

✅ **Good Database Design:**
- UUID primary keys (distributed-friendly)
- JSONB for flexible schemas
- Proper constraints (exclusion for double-booking)
- Full-text search support
- Audit logging built-in

✅ **Security Conscious:**
- JWT authentication
- Rate limiting mentioned
- Input validation patterns
- Audit trail

✅ **Self-Hosting Focus:**
- Open-source stack
- MinIO instead of S3
- MeiliSearch instead of Algolia
- Self-hosted Sentry

### 2.2 Critical Gaps Identified

#### 🎵 Music-Specific Features

**Missing:**
1. **Music Notation System**
   - No sheet music rendering
   - No annotation tools
   - No synchronization with audio playback

2. **Advanced Practice Tools**
   - Basic metronome/tuner mentioned
   - Missing: Slow-down/speed-up
   - Missing: Loop sections
   - Missing: Backing tracks
   - Missing: MIDI support
   - Missing: Multi-track recording

3. **Instrument-Specific Features**
   - No guitar tab support
   - No piano roll editor
   - No drum notation
   - No fingering/bowing diagrams

4. **Audio Pipeline Optimization**
   - Generic WebRTC configuration
   - No mention of music-optimized audio settings
   - No uncompressed audio option for premium

#### 📚 Educational Features

**Missing:**
1. **Curriculum Framework**
   - JSONB curriculum is too flexible
   - No alignment with music education standards
   - No prerequisite tracking system
   - No skill taxonomy

2. **Assessment System**
   - Basic grading exists
   - Missing: Rubric builder
   - Missing: Competency-based progression
   - Missing: Placement tests
   - Missing: Certification system

3. **Learning Analytics**
   - Practice logs exist
   - Missing: Learning path visualization
   - Missing: Predictive analytics
   - Missing: Engagement metrics
   - Missing: Retention analysis

4. **Collaborative Features**
   - 1:1 sessions only
   - Missing: Group lessons
   - Missing: Ensemble practice rooms
   - Missing: Peer review system
   - Missing: Student showcases/recitals

#### 💼 Business Features

**Missing:**
1. **Advanced Monetization**
   - Only pay-per-session
   - Missing: Subscription tiers
   - Missing: Course bundles
   - Missing: Membership levels
   - Missing: Gift cards/vouchers
   - Missing: Referral program

2. **Marketplace Features**
   - No teacher discovery optimization
   - Missing: Teacher ratings/reviews
   - Missing: Featured teacher promotion
   - Missing: Course marketplace
   - Missing: Teacher verification badges

3. **Marketing Tools**
   - Missing: Teacher landing page builder
   - Missing: Email campaign system
   - Missing: SEO optimization
   - Missing: Social media integration
   - Missing: Affiliate system

#### 🔧 Technical Enhancements

**Missing:**
1. **Mobile Strategy**
   - Web-only approach
   - Missing: PWA features
   - Missing: Mobile-specific optimizations
   - Missing: Offline mode

2. **Internationalization**
   - No i18n mentioned
   - Missing: Multi-currency
   - Missing: Timezone handling
   - Missing: Localized content

3. **Content Delivery**
   - Basic MinIO storage
   - Missing: CDN strategy
   - Missing: Adaptive streaming (HLS/DASH)
   - Missing: Progressive download
   - Missing: Thumbnail generation

4. **Advanced Real-time**
   - Basic Socket.io
   - Missing: Presence system
   - Missing: Typing indicators
   - Missing: Read receipts
   - Missing: Multi-server WebSocket scaling

5. **Job Queue System**
   - No async job processing mentioned
   - Needed for: Video encoding, AI analysis, email sending, report generation

---

## 3. Enhanced Architecture Design

### 3.1 Revised Technology Stack

```typescript
const enhancedTechStack = {
  // Backend
  runtime: "Node.js 20 LTS",
  framework: "NestJS",
  api: {
    external: "GraphQL (Apollo Server)",
    internal: "gRPC with Protocol Buffers",
    legacy: "REST for webhooks/uploads"
  },
  realtime: {
    signaling: "Socket.io with Redis adapter",
    webrtc: {
      media: "Mediasoup (SFU)",
      fallback: "Daily.co API (Phase 1)"
    }
  },
  jobQueue: "BullMQ with Redis",

  // Frontend
  framework: "Next.js 14 (App Router)",
  ui: "Tailwind CSS + Shadcn/ui",
  state: "Zustand + React Query",
  audio: "Web Audio API + Tone.js",
  notation: "VexFlow + vexflow-musicxml",

  // AI/ML
  models: {
    pitch: "TensorFlow.js SPICE",
    rhythm: "Essentia.js",
    analysis: "Custom ONNX models"
  },

  // Database
  primary: "PostgreSQL 15",
  cache: {
    L1: "Node-cache (in-memory)",
    L2: "Redis 7 (cluster mode)"
  },
  search: "MeiliSearch + PostgreSQL FTS",
  analytics: "ClickHouse (time-series)",

  // Storage
  objects: "MinIO (S3-compatible)",
  cdn: "Cloudflare R2 + CDN",

  // Infrastructure
  containerization: "Docker",
  orchestration: "Docker Compose → Kubernetes",
  reverseProxy: "Caddy 2",
  webrtc: "Coturn (TURN/STUN)",

  // Monitoring & Observability
  metrics: "Prometheus + Grafana",
  logs: "Loki + Promtail",
  traces: "Jaeger (OpenTelemetry)",
  errors: "Sentry (self-hosted)",
  uptime: "Uptime Kuma",

  // Development
  language: "TypeScript 5",
  testing: {
    unit: "Jest + ts-jest",
    integration: "Supertest + Testcontainers",
    e2e: "Playwright",
    load: "k6"
  },
  ci: "GitHub Actions",
  documentation: {
    api: "Swagger + GraphQL Playground",
    code: "TypeDoc",
    user: "Docusaurus"
  }
}
```

### 3.2 Enhanced System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                       Client Applications                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Web App      │  │ Mobile PWA   │  │ Teacher      │           │
│  │ (Next.js)    │  │ (Progressive)│  │ Dashboard    │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└──────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │   CDN (Cloudflare) │
                    │   - Static Assets  │
                    │   - Media Delivery │
                    └─────────┬─────────┘
                              │
┌──────────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Caddy Reverse Proxy                                      │   │
│  │  - Auto HTTPS                                             │   │
│  │  - Rate Limiting                                          │   │
│  │  - Load Balancing                                         │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐          ┌────▼────┐          ┌────▼────┐
   │GraphQL  │          │REST API │          │WebSocket│
   │Endpoint │          │         │          │(Socket.io)│
   └────┬────┘          └────┬────┘          └────┬────┘
        │                    │                    │
┌───────────────────────────────────────────────────────────────────┐
│                    Application Layer (NestJS)                      │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Auth Module  │  │ User Module  │  │ Course Module│           │
│  │ - JWT        │  │ - Profiles   │  │ - Curriculum │           │
│  │ - OAuth      │  │ - RBAC       │  │ - Content    │           │
│  │ - COPPA      │  │ - Parent     │  │ - Standards  │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │Schedule      │  │Payment       │  │Marketplace   │           │
│  │Module        │  │Module        │  │Module        │           │
│  │ - Calendar   │  │ - Stripe     │  │ - Discovery  │           │
│  │ - Booking    │  │ - Escrow     │  │ - Reviews    │           │
│  │ - Conflicts  │  │ - Subscript. │  │ - Ratings    │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │Notation      │  │Practice      │  │AI Analysis   │           │
│  │Module        │  │Module        │  │Module        │           │
│  │ - VexFlow    │  │ - Tools      │  │ - Pitch      │           │
│  │ - MusicXML   │  │ - Logs       │  │ - Rhythm     │           │
│  │ - Annotation │  │ - Progress   │  │ - Feedback   │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │Community     │  │Analytics     │  │Notification  │           │
│  │Module        │  │Module        │  │Module        │           │
│  │ - Forums     │  │ - Metrics    │  │ - Email      │           │
│  │ - Messaging  │  │ - Reports    │  │ - Push       │           │
│  │ - Showcase   │  │ - ClickHouse │  │ - SMS        │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │Content       │  │Assessment    │  │Curriculum    │           │
│  │Module        │  │Module        │  │Module        │           │
│  │ - CDN Sync   │  │ - Rubrics    │  │ - Standards  │           │
│  │ - Transcoding│  │ - Tests      │  │ - Pathways   │           │
│  │ - Streaming  │  │ - Certs      │  │ - Skills     │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└───────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐  ┌─────────▼────────┐  ┌────────▼────────┐
│ Message Queue  │  │  Job Processing   │  │  Event Bus     │
│ (BullMQ)       │  │  Workers          │  │  (Redis)       │
│ - Video Jobs   │  │  - Transcoding    │  │  - Real-time   │
│ - Email Jobs   │  │  - AI Analysis    │  │  - Updates     │
│ - AI Jobs      │  │  - Reports        │  │  - Presence    │
└────────────────┘  └──────────────────┘  └────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐  ┌─────────▼────────┐  ┌────────▼────────┐
│  PostgreSQL    │  │  Redis Cluster   │  │  MinIO S3      │
│  - Master      │  │  - Cache L2      │  │  - Videos      │
│  - Read Replica│  │  - Sessions      │  │  - Audio       │
│  - Partitioned │  │  - Queue         │  │  - Notation    │
└────────────────┘  └──────────────────┘  └────────────────┘
        │                     │                     │
┌───────▼────────┐  ┌─────────▼────────┐  ┌────────▼────────┐
│  ClickHouse    │  │  MeiliSearch     │  │  Media Servers │
│  - Analytics   │  │  - Course Search │  │  - Mediasoup   │
│  - Time Series │  │  - Teacher Search│  │  - Coturn      │
│  - Metrics     │  │  - Full-text     │  │  - Recording   │
└────────────────┘  └──────────────────┘  └────────────────┘
```

### 3.3 Enhanced Database Schema

#### New Tables for Enhanced Features:

```sql
-- Music Notation
CREATE TABLE sheet_music (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID REFERENCES courses(id),
    title VARCHAR(500) NOT NULL,
    format VARCHAR(50), -- 'musicxml', 'abc', 'pdf'
    content TEXT, -- MusicXML or ABC notation
    file_url TEXT, -- For PDF
    tempo INTEGER,
    key_signature VARCHAR(10),
    time_signature VARCHAR(10),
    difficulty_level INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),

    INDEX idx_sheet_music_course ON sheet_music(course_id)
);

-- Curriculum Standards Alignment
CREATE TABLE learning_standards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL, -- e.g., 'NAfME-MU:Cr1.1.5a'
    category VARCHAR(100), -- 'Creating', 'Performing', 'Responding', 'Connecting'
    grade_level VARCHAR(20),
    description TEXT,
    parent_id UUID REFERENCES learning_standards(id),

    INDEX idx_standards_category ON learning_standards(category),
    INDEX idx_standards_grade ON learning_standards(grade_level)
);

CREATE TABLE course_standards_mapping (
    course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
    standard_id UUID REFERENCES learning_standards(id) ON DELETE CASCADE,
    coverage_level VARCHAR(20), -- 'introduced', 'practiced', 'mastered'
    PRIMARY KEY (course_id, standard_id)
);

-- Assessment Rubrics
CREATE TABLE assessment_rubrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(500) NOT NULL,
    type VARCHAR(50), -- 'performance', 'composition', 'theory'
    criteria JSONB NOT NULL, -- Array of criterion objects
    scoring_guide JSONB, -- Point values and descriptions
    created_by UUID REFERENCES users(id),
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    INDEX idx_rubrics_type ON assessment_rubrics(type)
);

-- Subscription Management
CREATE TABLE subscription_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    billing_period VARCHAR(20), -- 'monthly', 'yearly'
    features JSONB, -- List of included features
    max_lessons_per_month INTEGER,
    is_active BOOLEAN DEFAULT true,
    stripe_price_id VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE user_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    plan_id UUID REFERENCES subscription_plans(id),
    status VARCHAR(50), -- 'active', 'canceled', 'past_due', 'trialing'
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    cancel_at_period_end BOOLEAN DEFAULT false,
    stripe_subscription_id VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    INDEX idx_subscriptions_user ON user_subscriptions(user_id),
    INDEX idx_subscriptions_status ON user_subscriptions(status)
);

-- Teacher Reviews and Ratings
CREATE TABLE teacher_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    teacher_id UUID REFERENCES users(id) ON DELETE CASCADE,
    student_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES class_sessions(id),
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    review_text TEXT,
    criteria_ratings JSONB, -- Detailed ratings: teaching_style, communication, etc.
    is_verified BOOLEAN DEFAULT false, -- Verified as actual student
    is_featured BOOLEAN DEFAULT false,
    helpful_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(student_id, session_id),
    INDEX idx_reviews_teacher ON teacher_reviews(teacher_id),
    INDEX idx_reviews_rating ON teacher_reviews(rating DESC)
);

-- Practice Sessions (Enhanced)
CREATE TABLE practice_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID REFERENCES courses(id),
    assignment_id UUID REFERENCES assignments(id),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    recording_url TEXT,
    ai_feedback JSONB, -- Pitch, rhythm, tone analysis
    self_rating INTEGER CHECK (self_rating BETWEEN 1 AND 5),
    notes TEXT,

    INDEX idx_practice_student ON practice_sessions(student_id),
    INDEX idx_practice_date ON practice_sessions(started_at)
);

-- Learning Pathways
CREATE TABLE learning_pathways (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(500) NOT NULL,
    description TEXT,
    instrument VARCHAR(100),
    difficulty_progression JSONB, -- Ordered course sequence
    estimated_weeks INTEGER,
    prerequisites JSONB,
    created_by UUID REFERENCES users(id),
    is_official BOOLEAN DEFAULT false,

    INDEX idx_pathways_instrument ON learning_pathways(instrument)
);

-- Child Safety (COPPA)
CREATE TABLE parental_consents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    child_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    parent_email VARCHAR(255) NOT NULL,
    parent_name VARCHAR(255),
    consent_method VARCHAR(50), -- 'email_credit_card', 'form_fax', 'video_call'
    consent_given_at TIMESTAMPTZ,
    consent_withdrawn_at TIMESTAMPTZ,
    verification_token VARCHAR(255),
    is_verified BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}',

    INDEX idx_consents_child ON parental_consents(child_user_id),
    INDEX idx_consents_verified ON parental_consents(is_verified)
);

-- Content Moderation
CREATE TABLE content_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reporter_id UUID REFERENCES users(id),
    content_type VARCHAR(50), -- 'forum_post', 'message', 'review'
    content_id UUID NOT NULL,
    reason VARCHAR(100),
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'reviewed', 'actioned', 'dismissed'
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMPTZ,
    action_taken VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    INDEX idx_reports_status ON content_reports(status),
    INDEX idx_reports_content ON content_reports(content_type, content_id)
);

-- Achievements (Enhanced)
CREATE TABLE achievement_progress (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    achievement_id UUID REFERENCES achievements(id) ON DELETE CASCADE,
    progress INTEGER DEFAULT 0, -- For progressive achievements
    completed BOOLEAN DEFAULT false,
    completed_at TIMESTAMPTZ,

    PRIMARY KEY (user_id, achievement_id)
);

-- Teacher Availability (Enhanced)
CREATE TABLE teacher_availability (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    teacher_id UUID REFERENCES users(id) ON DELETE CASCADE,
    day_of_week INTEGER CHECK (day_of_week BETWEEN 0 AND 6), -- 0=Sunday
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    timezone VARCHAR(50) NOT NULL,
    is_recurring BOOLEAN DEFAULT true,
    effective_from DATE,
    effective_until DATE,

    INDEX idx_availability_teacher ON teacher_availability(teacher_id),
    INDEX idx_availability_day ON teacher_availability(day_of_week)
);

-- Notification Preferences
CREATE TABLE notification_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    email_enabled BOOLEAN DEFAULT true,
    push_enabled BOOLEAN DEFAULT true,
    sms_enabled BOOLEAN DEFAULT false,
    preferences JSONB DEFAULT '{
        "lesson_reminders": true,
        "practice_reminders": true,
        "teacher_messages": true,
        "forum_replies": true,
        "achievements": true,
        "marketing": false
    }',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 4. Detailed Implementation Roadmap

### Phase 0: Project Setup & Infrastructure (Week 1-2)

#### Goals:
- Initialize monorepo structure
- Configure development environment
- Set up CI/CD pipeline
- Deploy basic infrastructure

#### Tasks:

**Week 1: Project Initialization**
- [ ] Create monorepo structure with pnpm workspaces
- [ ] Initialize NestJS backend with TypeScript
- [ ] Initialize Next.js 14 frontend (App Router)
- [ ] Configure ESLint, Prettier, Husky
- [ ] Set up Docker Compose for local development
- [ ] Configure PostgreSQL with initial migrations
- [ ] Set up Redis for caching and sessions
- [ ] Initialize MinIO for local S3-compatible storage

**Week 2: CI/CD & Infrastructure**
- [ ] Create GitHub Actions workflow
  - Lint and type-check
  - Unit tests
  - Integration tests
  - Build Docker images
- [ ] Set up development environment documentation
- [ ] Configure environment variable management
- [ ] Set up Caddy reverse proxy
- [ ] Configure Sentry for error tracking
- [ ] Initialize Prometheus + Grafana
- [ ] Create deployment scripts

**Deliverables:**
- ✅ Working local development environment
- ✅ Automated CI/CD pipeline
- ✅ Basic monitoring infrastructure
- ✅ Developer documentation

---

### Phase 1: Foundation & Authentication (Week 3-6)

#### Goals:
- Implement robust authentication system
- Create user management with RBAC
- Build COPPA compliance framework
- Develop basic UI components

#### Backend Tasks:

**Week 3: Authentication Core**
- [ ] User model and database schema
- [ ] JWT authentication service
- [ ] Password hashing with Argon2
- [ ] Login/signup endpoints
- [ ] Email verification flow
- [ ] Password reset flow
- [ ] Refresh token mechanism
- [ ] Session management with Redis

**Week 4: Authorization & COPPA**
- [ ] Role-based access control (RBAC)
  - Student, Teacher, Parent, Admin roles
- [ ] Permission guards and decorators
- [ ] COPPA compliance system:
  - Age gate at registration
  - Parental consent workflow
  - Parent-child account linking
  - Data access/deletion for parents
- [ ] OAuth2 integration (Google, Facebook)
- [ ] 2FA with TOTP (optional)

**Week 5-6: User Management**
- [ ] User profile CRUD
- [ ] Teacher profile enhancement
  - Bio, experience, instruments taught
  - Video introduction
  - Availability settings
- [ ] Student profile
  - Musical background
  - Learning goals
  - Instrument(s)
- [ ] Parent dashboard for child accounts
- [ ] Profile image upload with processing
- [ ] User search and discovery

#### Frontend Tasks:

**Week 3-4: Auth UI**
- [ ] Design system setup (Tailwind + Shadcn/ui)
- [ ] Landing page
- [ ] Login/signup forms with validation
- [ ] Email verification UI
- [ ] Password reset flow
- [ ] Age gate for COPPA
- [ ] Parental consent form

**Week 5-6: User Dashboards**
- [ ] Student dashboard layout
- [ ] Teacher dashboard layout
- [ ] Admin panel foundation
- [ ] Profile edit forms
- [ ] Responsive navigation
- [ ] Avatar upload component
- [ ] Theme system (light/dark mode)

**Testing:**
- [ ] Unit tests for auth services (>80% coverage)
- [ ] Integration tests for auth endpoints
- [ ] E2E tests for signup/login flows
- [ ] COPPA compliance testing

**Deliverables:**
- ✅ Complete authentication system
- ✅ COPPA-compliant user registration
- ✅ User dashboards for all roles
- ✅ OAuth social login
- ✅ Comprehensive test coverage

---

### Phase 2: Course & Curriculum Management (Week 7-10)

#### Goals:
- Build comprehensive course creation system
- Implement curriculum management aligned with standards
- Create content upload and management
- Develop course discovery and enrollment

#### Backend Tasks:

**Week 7: Course Foundation**
- [ ] Course model and schema
- [ ] Course CRUD operations
- [ ] Curriculum builder
  - Lesson structure
  - Learning objectives
  - Standards alignment
- [ ] Content upload system
  - Video upload to MinIO
  - Video transcoding queue (BullMQ)
  - HLS adaptive streaming generation
- [ ] Course categories and tagging

**Week 8: Standards & Pathways**
- [ ] Learning standards database
  - National Music Standards seeding
  - Standards API
- [ ] Course-to-standards mapping
- [ ] Learning pathway system
  - Pathway builder
  - Course prerequisites
  - Progress tracking
- [ ] Difficulty assessment algorithm

**Week 9: Enrollment & Progress**
- [ ] Course enrollment system
- [ ] Progress tracking
  - Lesson completion
  - Time spent
  - Engagement metrics
- [ ] Course analytics for teachers
- [ ] Student transcript generation

**Week 10: Music Notation Integration**
- [ ] Sheet music model
- [ ] VexFlow integration
- [ ] MusicXML import/export
- [ ] Notation editor basics
- [ ] PDF sheet music upload
- [ ] Synchronization with audio playback

#### Frontend Tasks:

**Week 7-8: Course Builder UI**
- [ ] Course creation wizard
- [ ] Rich text editor for descriptions
- [ ] Video upload component with progress
- [ ] Curriculum editor
  - Drag-and-drop lesson ordering
  - Nested module structure
- [ ] Standards selector
- [ ] Course preview

**Week 9-10: Student Experience**
- [ ] Course catalog with filters
  - Instrument
  - Level
  - Rating
  - Price
- [ ] Course detail page
  - Video preview
  - Curriculum outline
  - Teacher info
  - Reviews
- [ ] Enrollment flow
- [ ] My Courses dashboard
- [ ] Video player with controls
- [ ] Sheet music viewer (VexFlow)
- [ ] Progress indicators

**Testing:**
- [ ] Course CRUD integration tests
- [ ] Video upload and processing tests
- [ ] Standards mapping validation
- [ ] E2E course creation flow
- [ ] Sheet music rendering tests

**Deliverables:**
- ✅ Teachers can create comprehensive courses
- ✅ Students can browse and enroll
- ✅ Video content with adaptive streaming
- ✅ Standards-aligned curriculum
- ✅ Music notation display system

---

### Phase 3: Scheduling & Lessons (Week 11-14)

#### Goals:
- Implement scheduling system with conflict prevention
- Build calendar interface
- Integrate basic video calling (Daily.co as MVP)
- Create lesson management workflow

#### Backend Tasks:

**Week 11: Scheduling Core**
- [ ] Teacher availability system
  - Recurring availability
  - Timezone handling
  - Special dates (holidays, blocked)
- [ ] Booking engine
  - Availability calculation
  - Double-booking prevention (DB constraints)
  - Multi-timezone support
- [ ] Calendar event creation
- [ ] Booking confirmation emails

**Week 12: Session Management**
- [ ] Session lifecycle management
  - Scheduled → In Progress → Completed
  - Cancellation policy
  - Rescheduling logic
- [ ] Session reminders (24hr, 1hr before)
- [ ] No-show tracking
- [ ] Session notes and feedback

**Week 13-14: Video Integration (MVP)**
- [ ] Daily.co API integration
  - Room creation
  - Token generation
  - Recording management
- [ ] WebRTC signaling server setup
- [ ] Session join/leave events
- [ ] Recording storage and playback
- [ ] Session duration tracking

#### Frontend Tasks:

**Week 11-12: Calendar UI**
- [ ] Teacher availability editor
  - Weekly recurring schedule
  - Exception dates
  - Timezone selector
- [ ] Student booking interface
  - Calendar view (month/week/day)
  - Available time slots
  - Booking confirmation
- [ ] My Schedule dashboard
- [ ] Upcoming lessons widget

**Week 13-14: Lesson Room**
- [ ] Video lesson interface
  - Daily.co embed
  - Camera/mic controls
  - Screen share
- [ ] In-lesson chat
- [ ] Shared whiteboard (basic)
- [ ] Lesson controls (start/end)
- [ ] Post-lesson feedback form

**Testing:**
- [ ] Scheduling conflict tests
- [ ] Timezone conversion tests
- [ ] Booking flow integration tests
- [ ] Video session E2E tests
- [ ] Load testing for concurrent sessions

**Deliverables:**
- ✅ Complete scheduling system
- ✅ Calendar with availability management
- ✅ Working video lessons (Daily.co)
- ✅ Session recording and playback
- ✅ Automated reminders

---

### Phase 4: Payment & Monetization (Week 15-18)

#### Goals:
- Implement Stripe payment integration
- Build escrow system for lesson payments
- Create subscription management
- Develop pricing and package system

#### Backend Tasks:

**Week 15: Stripe Integration**
- [ ] Stripe account setup
- [ ] Payment Intent creation
- [ ] Checkout session API
- [ ] Webhook handling
  - payment_intent.succeeded
  - payment_intent.failed
  - charge.refunded
- [ ] Payment record keeping
- [ ] Invoice generation

**Week 16: Escrow System**
- [ ] Escrow payment flow
  - Hold funds after booking
  - Release after lesson completion (24hr delay)
  - Dispute period (7 days)
- [ ] Teacher payout system
  - Minimum payout threshold
  - Payout schedule (weekly)
  - Stripe Connect for teacher accounts
- [ ] Platform commission calculation
- [ ] Refund handling

**Week 17: Subscription Management**
- [ ] Subscription plans model
- [ ] Stripe subscription integration
  - Plan creation
  - Customer portal
  - Upgrade/downgrade
  - Cancellation
- [ ] Usage tracking for tiered plans
- [ ] Subscription lifecycle webhooks

**Week 18: Packages & Promotions**
- [ ] Lesson package system (5-pack, 10-pack)
- [ ] Discount codes
- [ ] Free trial implementation
- [ ] Gift card system
- [ ] Referral program foundation

#### Frontend Tasks:

**Week 15-16: Payment UI**
- [ ] Stripe Elements integration
- [ ] Checkout flow
  - Payment method selection
  - Billing info
  - Order summary
- [ ] Payment confirmation page
- [ ] Invoice display
- [ ] Payment history

**Week 17-18: Subscription & Teacher Earnings**
- [ ] Subscription plan selection
- [ ] Subscription management dashboard
- [ ] Teacher earnings dashboard
  - Pending payments
  - Payment history
  - Payout schedule
- [ ] Package purchase flow
- [ ] Promo code entry

**Testing:**
- [ ] Stripe webhook testing
- [ ] Escrow release automation tests
- [ ] Subscription lifecycle tests
- [ ] Refund flow tests
- [ ] Commission calculation validation

**Deliverables:**
- ✅ Complete payment processing
- ✅ Escrow system protecting both parties
- ✅ Subscription management
- ✅ Teacher payout automation
- ✅ Flexible pricing options

---

### Phase 5: Practice Tools & AI Analysis (Week 19-24)

#### Goals:
- Build in-browser practice tools
- Implement AI-powered feedback
- Create practice logging and analytics
- Develop assignment system

#### Backend Tasks:

**Week 19-20: Practice Tools Backend**
- [ ] Practice session logging API
- [ ] Audio recording upload
- [ ] Practice analytics calculation
  - Total practice time
  - Session frequency
  - Streak tracking
- [ ] Assignment system
  - Assignment creation
  - Submission tracking
  - Grading workflow

**Week 21-22: AI Analysis Integration**
- [ ] TensorFlow.js SPICE model integration
  - Pitch detection service
  - Accuracy calculation (cents deviation)
- [ ] Essentia.js for rhythm analysis
  - Tempo detection
  - Timing accuracy
  - Rush/drag detection
- [ ] AI feedback generation
  - Practice report creation
  - Improvement suggestions
- [ ] Model optimization for performance

**Week 23-24: Assessment System**
- [ ] Rubric builder
- [ ] Rubric-based grading
- [ ] Assessment templates
- [ ] Progress reports
- [ ] Skill tracking
- [ ] Certification generation

#### Frontend Tasks:

**Week 19-20: Practice Tools UI**
- [ ] Metronome
  - BPM control (40-300)
  - Time signature selector
  - Sound customization
  - Visual beat indicator
- [ ] Tuner
  - Pitch detection display
  - Note accuracy indicator
  - Reference frequency adjustment
- [ ] Drone generator
  - Instrument selection
  - Key/scale selector
- [ ] Audio recorder
  - Recording controls
  - Waveform visualization
  - Playback
- [ ] Practice log interface

**Week 21-22: AI Feedback UI**
- [ ] Audio analysis visualization
  - Pitch over time graph
  - Timing accuracy chart
  - Tone quality meter
- [ ] AI feedback display
  - Strengths/weaknesses
  - Specific recommendations
  - Progress comparison
- [ ] Practice analytics dashboard
  - Time spent charts
  - Accuracy trends
  - Goal tracking

**Week 23-24: Assignments**
- [ ] Assignment creation form
- [ ] Assignment submission interface
- [ ] Rubric display
- [ ] Grading interface for teachers
- [ ] Student progress tracker
- [ ] Achievement badges

**Testing:**
- [ ] Audio processing pipeline tests
- [ ] AI model accuracy validation
- [ ] Practice analytics calculation tests
- [ ] Assignment workflow E2E tests
- [ ] Performance tests for audio processing

**Deliverables:**
- ✅ Complete practice tool suite
- ✅ AI-powered feedback system
- ✅ Practice analytics
- ✅ Assignment and grading system
- ✅ Skill progression tracking

---

### Phase 6: Custom WebRTC & Real-time Features (Week 25-30)

#### Goals:
- Replace Daily.co with custom WebRTC solution
- Optimize audio quality for music
- Implement group lessons
- Build collaborative features

#### Backend Tasks:

**Week 25-26: Mediasoup SFU Setup**
- [ ] Mediasoup server deployment
- [ ] Room management API
- [ ] Producer/Consumer handling
- [ ] Recording infrastructure
  - Multi-track recording
  - Audio-only recording option
- [ ] TURN/STUN server (Coturn) configuration

**Week 27-28: Music-Optimized Audio**
- [ ] Custom audio constraints configuration
  - 48kHz sample rate
  - Stereo channels
  - Disabled audio processing
  - Opus codec at 128kbps
- [ ] Adaptive bitrate implementation
- [ ] Audio-only mode for low bandwidth
- [ ] JackTrip-style data channel option for premium
- [ ] Latency monitoring and optimization

**Week 29-30: Advanced Features**
- [ ] Group lesson support (up to 10 participants)
- [ ] Breakout rooms
- [ ] Screen sharing with audio
- [ ] Virtual backgrounds
- [ ] Noise suppression toggle
- [ ] Recording download and sharing

#### Frontend Tasks:

**Week 25-26: Custom WebRTC Client**
- [ ] Mediasoup client integration
- [ ] Device selection UI
- [ ] Audio/video toggle controls
- [ ] Connection quality indicator
- [ ] Reconnection handling

**Week 27-28: Audio Quality UI**
- [ ] Audio quality settings
  - Quality presets (Good/Better/Best)
  - Bandwidth selector
  - Latency mode
- [ ] Audio level meters
- [ ] Echo test utility
- [ ] Audio/video device testing

**Week 29-30: Collaboration Features**
- [ ] Participant grid layout
- [ ] Screen share display
- [ ] Collaborative whiteboard (Excalidraw integration)
- [ ] Shared notation editor
- [ ] Real-time cursor tracking
- [ ] Gesture reactions

**Testing:**
- [ ] WebRTC connection reliability tests
- [ ] Audio quality measurements
- [ ] Multi-party session tests
- [ ] Network condition simulation
- [ ] Load testing for media servers

**Deliverables:**
- ✅ Custom WebRTC infrastructure
- ✅ Music-optimized audio quality
- ✅ Group lesson capability
- ✅ Collaborative tools
- ✅ Professional recording quality

---

### Phase 7: Community & Marketplace (Week 31-36)

#### Goals:
- Build teacher marketplace
- Create community features
- Implement review and rating system
- Develop teacher marketing tools

#### Backend Tasks:

**Week 31-32: Marketplace**
- [ ] Teacher discovery algorithm
  - Filtering (instrument, style, level, price)
  - Sorting (rating, experience, popularity)
  - Recommendation engine
- [ ] Teacher profile enhancement
  - Verification badges
  - Featured teacher system
  - Portfolio showcase
- [ ] Course marketplace
  - Browse courses independent of teachers
  - Course bundles
  - Best sellers

**Week 33-34: Reviews & Ratings**
- [ ] Review submission system
- [ ] Rating aggregation
- [ ] Review verification (enrolled students only)
- [ ] Helpful votes on reviews
- [ ] Featured reviews curation
- [ ] Review moderation tools
- [ ] Teacher response to reviews

**Week 35-36: Community Features**
- [ ] Forum system
  - Categories by instrument/topic
  - Threaded discussions
  - Rich text posts
  - File attachments
- [ ] Direct messaging
  - Teacher-student messaging
  - File sharing
  - Message read receipts
- [ ] Student showcases
  - Performance uploads
  - Peer comments
  - Likes and shares

#### Frontend Tasks:

**Week 31-32: Discovery UI**
- [ ] Teacher marketplace page
  - Advanced filters
  - Search with autocomplete
  - Teacher cards with key info
- [ ] Teacher profile page
  - Video introduction
  - Course listings
  - Reviews section
  - Calendar availability
- [ ] Course marketplace
- [ ] Recommendation widgets

**Week 33-34: Reviews & Social**
- [ ] Review submission form
- [ ] Star rating display
- [ ] Review listing with filters
- [ ] Teacher profile rating summary
- [ ] Social sharing features

**Week 35-36: Community UI**
- [ ] Forum interface
  - Category browsing
  - Thread view
  - Rich text editor
  - Markdown support
- [ ] Messaging interface
  - Inbox/sent/archive
  - Conversation threads
  - Typing indicators
- [ ] Showcase gallery
  - Video/audio player
  - Comment section
  - Like button

**Testing:**
- [ ] Search and filter tests
- [ ] Rating calculation validation
- [ ] Forum posting E2E tests
- [ ] Messaging delivery tests
- [ ] Content moderation tests

**Deliverables:**
- ✅ Teacher discovery marketplace
- ✅ Comprehensive review system
- ✅ Active community forums
- ✅ Student showcases
- ✅ Direct messaging

---

### Phase 8: Analytics & Optimization (Week 37-40)

#### Goals:
- Implement comprehensive analytics
- Build reporting dashboards
- Optimize performance
- Add advanced admin tools

#### Backend Tasks:

**Week 37-38: Analytics Infrastructure**
- [ ] ClickHouse setup for time-series data
- [ ] Event tracking system
  - User events
  - Business metrics
  - Performance metrics
- [ ] Data aggregation pipelines
- [ ] Report generation service
- [ ] Export functionality (CSV, PDF)

**Week 39: Performance Optimization**
- [ ] Database query optimization
  - EXPLAIN ANALYZE audit
  - Index optimization
  - Query caching
- [ ] API response time optimization
  - N+1 query elimination
  - DataLoader implementation
  - GraphQL query complexity limits
- [ ] Caching strategy enhancement
  - Multi-layer caching
  - Cache invalidation strategy
- [ ] CDN integration for static assets

**Week 40: Admin Tools**
- [ ] Advanced admin dashboard
  - User management
  - Content moderation queue
  - Payment monitoring
  - System health
- [ ] Bulk operations
- [ ] Announcement system
- [ ] Feature flags
- [ ] A/B testing framework

#### Frontend Tasks:

**Week 37-38: Analytics Dashboards**
- [ ] Teacher analytics
  - Revenue metrics
  - Student retention
  - Lesson completion rates
  - Rating trends
- [ ] Student analytics
  - Practice time
  - Progress over time
  - Skill development
  - Goals vs actuals
- [ ] Admin analytics
  - Platform growth
  - Revenue reporting
  - User engagement
  - Top teachers/courses

**Week 39-40: Performance & Polish**
- [ ] Image optimization
  - Next.js Image component
  - Lazy loading
  - WebP format
- [ ] Code splitting optimization
- [ ] Skeleton loaders
- [ ] Infinite scroll for lists
- [ ] Accessibility audit (WCAG 2.1 AA)
- [ ] SEO optimization
  - Meta tags
  - Sitemap
  - Schema.org markup
  - Open Graph

**Testing:**
- [ ] Analytics accuracy validation
- [ ] Performance benchmarking
- [ ] Load testing (k6)
- [ ] Accessibility testing
- [ ] SEO validation

**Deliverables:**
- ✅ Comprehensive analytics system
- ✅ Performance optimizations
- ✅ Advanced admin panel
- ✅ SEO and accessibility compliance

---

### Phase 9: Mobile & Progressive Web App (Week 41-44)

#### Goals:
- Convert to Progressive Web App
- Optimize for mobile devices
- Add offline capabilities
- Implement push notifications

#### Tasks:

**Week 41-42: PWA Implementation**
- [ ] Service worker setup
  - Caching strategy
  - Offline fallback
  - Background sync
- [ ] Web app manifest
- [ ] Install prompts
- [ ] Offline mode for:
  - Downloaded lessons
  - Practice tools
  - Course materials
- [ ] IndexedDB for local storage

**Week 43-44: Mobile Optimization**
- [ ] Mobile-responsive layouts
- [ ] Touch gesture support
- [ ] Mobile video player
- [ ] Reduced data mode
- [ ] Push notification system
  - Web Push API
  - Notification preferences
  - Action buttons
- [ ] App-like navigation (bottom tabs)

**Testing:**
- [ ] PWA audit (Lighthouse)
- [ ] Mobile device testing
- [ ] Offline functionality tests
- [ ] Push notification delivery

**Deliverables:**
- ✅ Full PWA capability
- ✅ Mobile-optimized experience
- ✅ Offline mode
- ✅ Push notifications

---

### Phase 10: Launch Preparation & Scaling (Week 45-48)

#### Goals:
- Production deployment
- Security hardening
- Performance optimization
- Documentation and training

#### Tasks:

**Week 45: Security Hardening**
- [ ] Security audit
  - Penetration testing
  - Dependency scanning
  - OWASP Top 10 compliance
- [ ] Rate limiting refinement
- [ ] DDoS protection (Cloudflare)
- [ ] Data encryption audit
- [ ] GDPR compliance verification
- [ ] COPPA compliance audit

**Week 46: Kubernetes Deployment**
- [ ] K8s cluster setup
- [ ] Helm charts creation
- [ ] Auto-scaling configuration
- [ ] Load balancer setup
- [ ] SSL/TLS certificates
- [ ] Backup and disaster recovery
- [ ] Monitoring and alerting

**Week 47: Documentation**
- [ ] API documentation (Swagger)
- [ ] User guides
  - Student onboarding
  - Teacher onboarding
  - Parent guides
- [ ] Video tutorials
- [ ] FAQ system
- [ ] Help center
- [ ] Developer documentation

**Week 48: Launch**
- [ ] Beta testing with select users
- [ ] Bug fixes and polish
- [ ] Marketing site
- [ ] Launch announcement
- [ ] Post-launch monitoring
- [ ] Incident response plan

**Deliverables:**
- ✅ Production-ready platform
- ✅ Comprehensive documentation
- ✅ Scalable infrastructure
- ✅ Security compliance
- ✅ Launch readiness

---

## 5. Technology Deep Dives

### 5.1 WebRTC Audio Pipeline for Music

#### Architecture:

```
┌─────────────────────────────────────────────────────────┐
│                    Student Browser                       │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Audio Input (Microphone/Interface)            │    │
│  └────────────────┬───────────────────────────────┘    │
│                   │                                      │
│  ┌────────────────▼───────────────────────────────┐    │
│  │  Web Audio API Processing                      │    │
│  │  - Gain Control                                │    │
│  │  - Analyser (visualization)                    │    │
│  │  - Optional: Noise Gate                        │    │
│  └────────────────┬───────────────────────────────┘    │
│                   │                                      │
│  ┌────────────────▼───────────────────────────────┐    │
│  │  getUserMedia with Music Constraints           │    │
│  │  {                                              │    │
│  │    audio: {                                     │    │
│  │      channelCount: 2,                           │    │
│  │      echoCancellation: false,                   │    │
│  │      noiseSuppression: false,                   │    │
│  │      autoGainControl: false,                    │    │
│  │      sampleRate: 48000,                         │    │
│  │      latency: 0                                 │    │
│  │    }                                            │    │
│  │  }                                              │    │
│  └────────────────┬───────────────────────────────┘    │
│                   │                                      │
│  ┌────────────────▼───────────────────────────────┐    │
│  │  RTCPeerConnection                              │    │
│  │  - Opus Codec (128kbps)                         │    │
│  │  - Stereo (maxaveragebitrate: 510000)          │    │
│  │  - DTX disabled (maintain quality)              │    │
│  └────────────────┬───────────────────────────────┘    │
└────────────────────┼────────────────────────────────────┘
                     │
                     │ WebRTC over UDP
                     │ (STUN/TURN for NAT)
                     │
┌────────────────────▼────────────────────────────────────┐
│              Mediasoup SFU Server                        │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Router                                         │    │
│  │  - Manages RTP streams                          │    │
│  │  - Selective forwarding                         │    │
│  └────────────────┬───────────────────────────────┘    │
│                   │                                      │
│  ┌────────────────▼───────────────────────────────┐    │
│  │  Producers (Incoming streams)                   │    │
│  │  - Audio track from student                     │    │
│  │  - Video track (optional)                       │    │
│  └────────────────┬───────────────────────────────┘    │
│                   │                                      │
│  ┌────────────────▼───────────────────────────────┐    │
│  │  Consumers (Outgoing streams)                   │    │
│  │  - Forward to teacher                           │    │
│  │  - Forward to recording service                 │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                     │
                     │
┌────────────────────▼────────────────────────────────────┐
│                 Teacher Browser                          │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  RTCPeerConnection (receive)                    │    │
│  └────────────────┬───────────────────────────────┘    │
│                   │                                      │
│  ┌────────────────▼───────────────────────────────┐    │
│  │  Audio Output                                   │    │
│  │  - Low-latency playback                         │    │
│  │  - Volume normalization                         │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

#### Implementation Code:

```typescript
// frontend/lib/webrtc/audio-config.ts

export const MusicAudioConstraints = {
  // Standard music quality (good for most lessons)
  standard: {
    echoCancellation: false,
    noiseSuppression: false,
    autoGainControl: false,
    channelCount: 2,
    sampleRate: 48000,
    latency: 0,
    // Opus will encode at ~64kbps stereo
  },

  // High quality (better for advanced students)
  high: {
    echoCancellation: false,
    noiseSuppression: false,
    autoGainControl: false,
    channelCount: 2,
    sampleRate: 48000,
    latency: 0,
    // Will be enhanced via SDP munging
  },

  // Studio quality (premium tier, uses data channel)
  studio: {
    echoCancellation: false,
    noiseSuppression: false,
    autoGainControl: false,
    channelCount: 2,
    sampleRate: 96000, // Higher sample rate
    latency: 0,
  }
};

// SDP munging to increase Opus bitrate
export function enhanceOpusInSDP(sdp: string): string {
  // Find Opus codec payload type
  const opusMatch = sdp.match(/a=rtpmap:(\d+) opus/);
  if (!opusMatch) return sdp;

  const payloadType = opusMatch[1];

  // Add/modify fmtp line for Opus
  const fmtpRegex = new RegExp(`a=fmtp:${payloadType}.*`, 'g');
  const newFmtp = `a=fmtp:${payloadType} minptime=10;useinbandfec=1;stereo=1;maxaveragebitrate=510000`;

  if (fmtpRegex.test(sdp)) {
    return sdp.replace(fmtpRegex, newFmtp);
  } else {
    // Insert after rtpmap line
    return sdp.replace(
      `a=rtpmap:${payloadType} opus/48000/2`,
      `a=rtpmap:${payloadType} opus/48000/2\r\n${newFmtp}`
    );
  }
}

// Audio quality selector component
export function useAudioQuality() {
  const [quality, setQuality] = useState<'standard' | 'high' | 'studio'>('standard');

  const getConstraints = () => {
    return {
      audio: MusicAudioConstraints[quality],
      video: true
    };
  };

  return { quality, setQuality, getConstraints };
}
```

```typescript
// backend/src/modules/media/mediasoup.service.ts

import * as mediasoup from 'mediasoup';
import { Worker, Router, WebRtcServer } from 'mediasoup/node/lib/types';

@Injectable()
export class MediasoupService {
  private workers: Worker[] = [];
  private nextWorkerIdx = 0;

  async onModuleInit() {
    // Create workers (1 per CPU core)
    const numWorkers = os.cpus().length;

    for (let i = 0; i < numWorkers; i++) {
      const worker = await mediasoup.createWorker({
        logLevel: 'warn',
        rtcMinPort: 40000,
        rtcMaxPort: 49999,
      });

      worker.on('died', () => {
        console.error('mediasoup worker died, exiting in 2 seconds...');
        setTimeout(() => process.exit(1), 2000);
      });

      this.workers.push(worker);
    }
  }

  async createRouter(): Promise<Router> {
    const worker = this.workers[this.nextWorkerIdx];
    this.nextWorkerIdx = (this.nextWorkerIdx + 1) % this.workers.length;

    return await worker.createRouter({
      mediaCodecs: [
        {
          kind: 'audio',
          mimeType: 'audio/opus',
          clockRate: 48000,
          channels: 2,
          parameters: {
            minptime: 10,
            useinbandfec: 1,
            stereo: 1,
            maxaveragebitrate: 510000, // High quality for music
          }
        },
        {
          kind: 'video',
          mimeType: 'video/VP8',
          clockRate: 90000,
          parameters: {}
        }
      ]
    });
  }
}
```

### 5.2 AI Music Analysis Pipeline

```typescript
// frontend/lib/ai/pitch-analyzer.ts

import * as tf from '@tensorflow/tfjs';

export class PitchAnalyzer {
  private model: tf.GraphModel;

  async loadModel() {
    // Load SPICE model from TensorFlow Hub
    this.model = await tf.loadGraphModel(
      'https://tfhub.dev/google/tfjs-model/spice/2/default/1',
      { fromTFHub: true }
    );
  }

  async analyzePitch(audioBuffer: Float32Array): Promise<PitchAnalysis> {
    // Resample to 16kHz (SPICE requirement)
    const resampled = this.resample(audioBuffer, 48000, 16000);

    // Create tensor
    const audioTensor = tf.tensor1d(resampled);

    // Run inference
    const [pitch, uncertainty] = await this.model.predict(audioTensor) as [tf.Tensor, tf.Tensor];

    // Get values
    const pitchValues = await pitch.data();
    const uncertaintyValues = await uncertainty.data();

    // Analyze results
    const analysis = this.processPitchData(pitchValues, uncertaintyValues);

    // Cleanup
    audioTensor.dispose();
    pitch.dispose();
    uncertainty.dispose();

    return analysis;
  }

  private processPitchData(
    pitchHz: Float32Array,
    uncertainty: Float32Array
  ): PitchAnalysis {
    const frames = [];

    for (let i = 0; i < pitchHz.length; i++) {
      if (uncertainty[i] < 0.2) { // Confident detection
        const note = this.frequencyToNote(pitchHz[i]);
        const cents = this.calculateCents(pitchHz[i], note.frequency);

        frames.push({
          time: i * 0.032, // 32ms per frame
          frequency: pitchHz[i],
          note: note.name,
          cents: cents,
          inTune: Math.abs(cents) < 10
        });
      }
    }

    // Calculate summary statistics
    const inTuneFrames = frames.filter(f => f.inTune).length;
    const accuracy = (inTuneFrames / frames.length) * 100;

    return {
      frames,
      accuracy,
      avgDeviation: this.calculateAvgDeviation(frames),
      recommendations: this.generateRecommendations(accuracy, frames)
    };
  }

  private frequencyToNote(freq: number): { name: string; frequency: number } {
    const A4 = 440;
    const noteNames = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];

    const halfStepsFromA4 = 12 * Math.log2(freq / A4);
    const noteIndex = Math.round(halfStepsFromA4) + 9; // A is index 9
    const octave = Math.floor(noteIndex / 12) + 4;
    const note = noteNames[((noteIndex % 12) + 12) % 12];

    const targetHalfSteps = Math.round(halfStepsFromA4);
    const targetFreq = A4 * Math.pow(2, targetHalfSteps / 12);

    return {
      name: `${note}${octave}`,
      frequency: targetFreq
    };
  }

  private calculateCents(actualFreq: number, targetFreq: number): number {
    return 1200 * Math.log2(actualFreq / targetFreq);
  }
}
```

```typescript
// backend/src/modules/practice/practice-analysis.service.ts

@Injectable()
export class PracticeAnalysisService {
  constructor(
    @InjectRepository(PracticeSession)
    private practiceRepo: Repository<PracticeSession>
  ) {}

  async analyzePracticeSubmission(
    studentId: string,
    audioUrl: string,
    targetNotes?: string[]
  ): Promise<PracticeFeedback> {
    // Download audio from storage
    const audioBuffer = await this.downloadAudio(audioUrl);

    // Run AI analysis
    const pitchAnalysis = await this.analyzePitch(audioBuffer);
    const rhythmAnalysis = await this.analyzeRhythm(audioBuffer);
    const toneAnalysis = await this.analyzeTone(audioBuffer);

    // Generate feedback
    const feedback = this.generateFeedback({
      pitch: pitchAnalysis,
      rhythm: rhythmAnalysis,
      tone: toneAnalysis,
      targetNotes
    });

    // Store analysis results
    await this.practiceRepo.save({
      student_id: studentId,
      recording_url: audioUrl,
      ai_feedback: feedback,
      created_at: new Date()
    });

    return feedback;
  }

  private generateFeedback(analysis: AnalysisResults): PracticeFeedback {
    const feedback: PracticeFeedback = {
      overall_score: 0,
      strengths: [],
      areas_to_improve: [],
      specific_recommendations: []
    };

    // Pitch feedback
    if (analysis.pitch.accuracy > 85) {
      feedback.strengths.push('Excellent pitch accuracy');
      feedback.overall_score += 30;
    } else if (analysis.pitch.accuracy > 70) {
      feedback.strengths.push('Good pitch control');
      feedback.overall_score += 20;
      feedback.specific_recommendations.push(
        'Focus on the notes where you tend to be sharp/flat'
      );
    } else {
      feedback.areas_to_improve.push('Pitch accuracy needs work');
      feedback.overall_score += 10;
      feedback.specific_recommendations.push(
        'Practice with a tuner to develop better pitch awareness',
        'Try singing/playing long tones to improve intonation'
      );
    }

    // Rhythm feedback
    if (analysis.rhythm.timingAccuracy > 90) {
      feedback.strengths.push('Solid rhythm and timing');
      feedback.overall_score += 35;
    } else if (analysis.rhythm.timingAccuracy > 75) {
      feedback.strengths.push('Good sense of rhythm');
      feedback.overall_score += 25;
      if (analysis.rhythm.tendency === 'rushing') {
        feedback.specific_recommendations.push(
          'You tend to rush - practice with a metronome at a slower tempo'
        );
      } else if (analysis.rhythm.tendency === 'dragging') {
        feedback.specific_recommendations.push(
          'You tend to drag - focus on feeling the beat ahead of time'
        );
      }
    } else {
      feedback.areas_to_improve.push('Rhythm consistency');
      feedback.overall_score += 15;
      feedback.specific_recommendations.push(
        'Use a metronome regularly in practice',
        'Start slow and gradually increase tempo',
        'Count out loud while playing'
      );
    }

    // Tone feedback
    if (analysis.tone.quality > 80) {
      feedback.strengths.push('Beautiful tone quality');
      feedback.overall_score += 35;
    } else if (analysis.tone.quality > 60) {
      feedback.strengths.push('Developing good tone');
      feedback.overall_score += 25;
      feedback.specific_recommendations.push(
        'Focus on breath support and embouchure for richer tone'
      );
    } else {
      feedback.areas_to_improve.push('Tone quality and consistency');
      feedback.overall_score += 10;
      feedback.specific_recommendations.push(
        'Work on long tones to develop consistent sound',
        'Record yourself to develop critical listening',
        'Consult your teacher on proper technique'
      );
    }

    return feedback;
  }
}
```

---

## 6. Risk Analysis & Mitigation

### 6.1 Technical Risks

#### Risk: WebRTC Audio Quality Issues
**Likelihood**: Medium | **Impact**: High

**Mitigation:**
- Start with Daily.co (proven solution) in Phase 1
- Extensive testing before custom WebRTC rollout
- Provide multiple quality tiers
- Fallback to Daily.co for problematic connections
- Clear documentation on audio interface requirements

#### Risk: AI Analysis Accuracy
**Likelihood**: Medium | **Impact**: Medium

**Mitigation:**
- Set correct expectations (AI assists, doesn't replace teacher)
- Allow students to request teacher review
- Continuous model improvement with feedback
- Display confidence scores with analysis
- Hybrid approach: AI + teacher verification

#### Risk: Scalability Bottlenecks
**Likelihood**: Medium | **Impact**: High

**Mitigation:**
- Start with monolith, measure before splitting
- Identify bottlenecks with monitoring
- Horizontal scaling strategy from day 1
- Database read replicas early
- CDN for static content
- Aggressive caching strategy

#### Risk: Payment Processing Issues
**Likelihood**: Low | **Impact**: Critical

**Mitigation:**
- Use proven Stripe integration
- Comprehensive webhook testing
- Idempotency keys for all payment operations
- Detailed audit logging
- Manual intervention tools for edge cases
- Clear refund policies

### 6.2 Business Risks

#### Risk: Teacher Adoption
**Likelihood**: Medium | **Impact**: High

**Mitigation:**
- Freemium model for teachers (free until first sale)
- Comprehensive onboarding and training
- Responsive teacher support
- Teacher community and best practices
- Marketing tools to help teachers succeed

#### Risk: Student Retention
**Likelihood**: Medium | **Impact**: High

**Mitigation:**
- Gamification and achievement system
- Progress visualization
- Social features (showcase, community)
- AI-powered practice recommendations
- Flexible pricing options

#### Risk: Competitive Differentiation
**Likelihood**: Medium | **Impact**: Medium

**Mitigation:**
- Focus on unique features (AI feedback, high-quality audio)
- Self-hosting option (unique in market)
- Open-source community building
- Standards-aligned curriculum
- Superior teacher tools

### 6.3 Compliance Risks

#### Risk: COPPA Violations
**Likelihood**: Low | **Impact**: Critical

**Mitigation:**
- Age gate from day 1
- Comprehensive parental consent system
- Limited data collection for children
- Regular compliance audits
- Legal review before launch
- Clear privacy policies

#### Risk: GDPR Compliance
**Likelihood**: Low | **Impact**: High

**Mitigation:**
- Data export functionality
- Right to deletion implementation
- Consent management
- Data processing agreements
- Privacy by design
- DPO designation if needed

---

## 7. Success Metrics

### 7.1 Technical KPIs

**Performance:**
- API response time p50 < 100ms
- API response time p95 < 500ms
- Page load time < 2s
- WebRTC connection success rate > 95%
- Audio latency < 100ms
- Uptime > 99.9%

**Quality:**
- Unit test coverage > 80%
- Integration test coverage > 70%
- E2E test coverage for critical paths
- Zero critical security vulnerabilities
- Accessibility score > 90

### 7.2 Business KPIs

**Growth:**
- Monthly Active Users (MAU)
- Teacher signups
- Student signups
- Lesson bookings per month
- Revenue growth MoM

**Engagement:**
- Lessons per student per month
- Practice session frequency
- Course completion rate
- Student retention (30/60/90 day)
- Teacher retention

**Quality:**
- Net Promoter Score (NPS)
- Average teacher rating
- Average course rating
- Support ticket resolution time
- Student satisfaction score

### 7.3 Educational KPIs

**Learning Outcomes:**
- Skill progression rate
- Assessment scores improvement
- Practice time correlation with progress
- Certification completion rate
- Student-reported learning outcomes

---

## 8. Conclusion & Next Steps

This comprehensive architecture analysis has identified significant enhancements to the original platform design, with particular focus on:

1. **Music-Optimized Technology**: WebRTC audio configuration specifically for music education, ensuring professional quality
2. **AI-Powered Learning**: TensorFlow.js integration for intelligent practice feedback
3. **Standards Alignment**: Curriculum framework aligned with National Music Education Standards
4. **COPPA Compliance**: Complete framework for child safety and parental controls
5. **Scalable Architecture**: Clear evolution path from monolith to microservices
6. **Comprehensive Monetization**: Multiple pricing models to maximize teacher and platform revenue

### Immediate Next Steps:

1. **Review and Approve**: Review this architecture and implementation plan
2. **Prioritization**: Confirm phase prioritization or adjust based on business goals
3. **Resource Planning**: Identify any external resources needed (design, legal review)
4. **Phase 0 Kickoff**: Begin project setup and infrastructure (Week 1-2)

### Recommended Approach:

Given the scope, I recommend:
- **Start with Phase 0-1** (Weeks 1-6): Foundation and authentication
- **Validate with Users**: Get early teacher feedback on the platform
- **Iterate Based on Learning**: Adjust phases 2-10 based on real usage data
- **Maintain Quality**: Don't rush - better to launch later with solid foundation

**This is a 48-week project (12 months)** to reach a comprehensive, production-ready platform. However, you can launch a viable MVP after Phase 4 (Week 18) with core features:
- User authentication
- Course creation and management
- Video lessons (Daily.co)
- Payment processing
- Basic practice tools

I'm ready to begin implementation whenever you are. What would you like to tackle first?
