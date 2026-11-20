"""
Streamlit UI for Lenny-RAG: a landing page with the ask box built in, and a focused results view.

Usage:
  streamlit run app.py
"""

import html
import re
import threading

import streamlit as st
import streamlit.components.v1 as components
from rag import retrieve, generate

NOT_COVERED = "The transcripts don't cover this topic."
EXCERPT_CHARS = 420

EXAMPLES = [
    "How should a PM decide what not to build?",
    "How would you diagnose weak day-7 retention for Glance?",
    "How do I know if we have product-market fit?",
]

# (framework, guest, one-line description, question it asks). Each was checked against the transcripts.
FRAMEWORKS = [
    ("LNO framework", "Shreyas Doshi", "Sort tasks by leverage so your best effort goes where it compounds.",
     "What is Shreyas Doshi's LNO framework?"),
    ("The Sean Ellis test", "Sean Ellis", "The “very disappointed” survey that measures product-market fit.",
     "How does the Sean Ellis test measure product-market fit?"),
    ("7 Powers", "Hamilton Helmer", "Seven sources of competitive advantage that stay durable.",
     "What are Hamilton Helmer's 7 Powers?"),
    ("Positioning", "April Dunford", "Pick the market frame that makes your strengths obvious.",
     "What is April Dunford's process for product positioning?"),
    ("Shape Up", "Ryan Singer", "Fix the time you're willing to spend, then shape the scope to fit.",
     "How does Shape Up's idea of appetite work?"),
    ("Opportunity solution tree", "Teresa Torres", "Connect outcomes to opportunities to experiments.",
     "How does an opportunity solution tree work for continuous discovery?"),
    ("Radical Candor", "Kim Scott", "Care personally and challenge directly at the same time.",
     "How do I give my team direct critical feedback without coming across as a jerk?"),
    ("Working backwards", "Bill Carr", "Write the press release before you build the product.",
     "How does Amazon's working backwards PR/FAQ process work?"),
]

GUESTS = [
    "Shreyas Doshi", "Brian Chesky", "Marty Cagan", "April Dunford", "Julie Zhuo", "Tobi Lutke",
    "Elena Verna", "Dylan Field", "Teresa Torres", "Hamilton Helmer", "Kim Scott", "Annie Duke",
    "Stewart Butterfield", "Melanie Perkins", "Ben Horowitz", "Sean Ellis", "Rahul Vohra",
    "Geoffrey Moore", "Roger Martin", "Seth Godin", "Ryan Singer", "Bill Carr", "Kevin Weil",
    "Drew Houston", "Nir Eyal", "Ronny Kohavi", "Sarah Tavel", "Gokul Rajaram", "Lane Shackleton",
    "Richard Rumelt",
]

STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Inter:wght@400;500;600&display=swap');

:root { --ink: #1f1d1a; --muted: #6b665e; --rule: #e4e0d8; --paper: #fbfaf7; --card: #ffffff;
        --tint: #f1eee8; --accent: #c2410c; --accent-ink: #9a3412; }

html, body, [data-testid="stAppViewContainer"] { font-family: 'Inter', -apple-system, sans-serif; }
[data-testid="stMainBlockContainer"] { max-width: 1120px; padding: 1.25rem 1.5rem 3rem; }
header[data-testid="stHeader"] { background: transparent; height: 0; }
[data-testid="InputInstructions"] { display: none; }

.display { font-family: 'Fraunces', Georgia, serif; font-weight: 600; letter-spacing: -0.02em; color: var(--ink); }
.eyebrow { color: var(--accent); font-size: 0.75rem; font-weight: 600; letter-spacing: 0.1em;
           text-transform: uppercase; margin: 0 0 0.75rem; }
.muted { color: var(--muted); }

/* Nav */
.nav { display: flex; align-items: center; justify-content: space-between; padding: 0.25rem 0 1.25rem; }
.brand { display: flex; align-items: center; gap: 0.55rem; font-weight: 600; font-size: 1rem; color: var(--ink); }
.mark { width: 28px; height: 28px; border-radius: 8px; background: var(--accent); color: #fff;
        display: grid; place-items: center; font-family: 'Fraunces', serif; font-size: 1rem; }
.nav-meta { color: var(--muted); font-size: 0.85rem; }

/* Hero */
.st-key-hero { position: relative; overflow: hidden; border: 1px solid var(--rule); border-radius: 28px;
  padding: 3.25rem 3rem; background:
    radial-gradient(600px 320px at 92% 8%, rgba(251, 146, 60, 0.22), transparent 70%),
    radial-gradient(520px 300px at 0% 100%, rgba(194, 65, 12, 0.10), transparent 70%), var(--paper); }
.hero-title { font-size: 3.4rem; line-height: 1.04; margin: 0 0 1rem; }
.hero-title em { font-style: italic; color: var(--accent); }
.hero-sub { font-size: 1.1rem; line-height: 1.55; color: var(--muted); margin: 0 0 1.5rem; max-width: 34rem; }
.st-key-hero [data-testid="stForm"] { background: var(--card); border: 1px solid var(--rule);
  border-radius: 16px; padding: 0.4rem; box-shadow: 0 8px 30px rgba(31, 29, 26, 0.07); }
.st-key-hero [data-testid="stTextInput"] input { background: transparent; font-size: 1rem; }
.st-key-hero [data-testid="stTextInputRootElement"],
.st-key-hero [data-baseweb="input"], .st-key-hero [data-baseweb="base-input"] { border: none; background: transparent; }
[class*="st-key-chip_"] button { border-radius: 999px; background: rgba(255, 255, 255, 0.7);
  border: 1px solid var(--rule); font-size: 0.82rem; padding: 0.15rem 0.85rem; min-height: 0; }
[class*="st-key-chip_"] button:hover { border-color: var(--accent); color: var(--accent-ink); }

/* Sample answer card */
.sample { background: var(--card); border: 1px solid var(--rule); border-radius: 20px; padding: 1.4rem 1.5rem;
  box-shadow: 0 24px 60px rgba(31, 29, 26, 0.12); transform: rotate(1.2deg); }
.sample-q { font-family: 'Fraunces', serif; font-size: 1.15rem; margin: 0.2rem 0 0.9rem; }
.sample ul { padding-left: 1.1rem; margin: 0 0 0.9rem; }
.sample li { font-size: 0.9rem; line-height: 1.5; margin-bottom: 0.45rem; color: var(--ink); }
.sample-foot { border-top: 1px solid var(--rule); padding-top: 0.7rem; font-size: 0.78rem; color: var(--muted); }
.cite { display: inline-block; background: var(--tint); color: var(--accent-ink); border-radius: 999px;
  padding: 0 0.55em; font-size: 0.8em; font-weight: 500; white-space: nowrap; }

/* Stats */
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin: 2.25rem 0 1.75rem; }
.stat { padding: 0 0.25rem; border-left: 2px solid var(--rule); padding-left: 1rem; }
.stat b { display: block; font-family: 'Fraunces', serif; font-size: 2rem; font-weight: 600; line-height: 1.1; }
.stat span { color: var(--muted); font-size: 0.85rem; }

/* Guest marquee */
.marquee { overflow: hidden; margin: 0 0 3.5rem;
  -webkit-mask-image: linear-gradient(90deg, transparent, #000 8%, #000 92%, transparent);
          mask-image: linear-gradient(90deg, transparent, #000 8%, #000 92%, transparent); }
.track { display: flex; gap: 0.6rem; width: max-content; animation: scroll 80s linear infinite; }
.guest { display: flex; align-items: center; gap: 0.5rem; background: var(--card); border: 1px solid var(--rule);
  border-radius: 999px; padding: 0.3rem 0.9rem 0.3rem 0.3rem; font-size: 0.85rem; white-space: nowrap; }
.avatar { width: 26px; height: 26px; border-radius: 50%; display: grid; place-items: center;
  font-size: 0.65rem; font-weight: 600; color: #fff; }
@keyframes scroll { to { transform: translateX(-50%); } }
@media (prefers-reduced-motion: reduce) { .track { animation: none; } }

/* Sections */
.section-title { font-size: 2.1rem; line-height: 1.15; margin: 0 0 0.4rem; }
.section-sub { color: var(--muted); margin: 0 0 1.5rem; }
[class*="st-key-fw_"] { background: var(--card); border: 1px solid var(--rule); border-radius: 18px;
  padding: 1.15rem 1.15rem 0.6rem; height: 100%; transition: transform 0.15s, box-shadow 0.15s; }
[class*="st-key-fw_"]:hover { transform: translateY(-2px); box-shadow: 0 12px 30px rgba(31, 29, 26, 0.08); }
.fw-name { font-family: 'Fraunces', serif; font-size: 1.15rem; font-weight: 600; margin: 0 0 0.15rem; }
.fw-guest { color: var(--accent-ink); font-size: 0.8rem; font-weight: 500; margin: 0 0 0.6rem; }
.fw-desc { color: var(--muted); font-size: 0.88rem; line-height: 1.45; margin: 0; min-height: 3.9em; }
[class*="st-key-fw_"] button { padding-left: 0; color: var(--accent); font-weight: 500; }

.steps { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 0 0 3rem; }
.step { background: var(--tint); border-radius: 18px; padding: 1.4rem; }
.step-n { width: 30px; height: 30px; border-radius: 50%; background: var(--ink); color: var(--paper);
  display: grid; place-items: center; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.9rem; }
.step h4 { font-family: 'Fraunces', serif; font-size: 1.15rem; margin: 0 0 0.35rem; padding: 0; }
.step p { color: var(--muted); font-size: 0.9rem; line-height: 1.5; margin: 0; }

.footer { border-top: 1px solid var(--rule); padding-top: 1.25rem; color: var(--muted); font-size: 0.82rem;
  display: flex; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem; }

/* Results view */
.st-key-reading { max-width: 760px; margin: 0 auto; }
.q-label { color: var(--muted); font-size: 0.75rem; font-weight: 600; letter-spacing: 0.1em;
  text-transform: uppercase; margin: 1.75rem 0 0.25rem; }
.q-text { font-family: 'Fraunces', serif; font-size: 2rem; line-height: 1.2; margin: 0 0 1.5rem; }
.st-key-answer { background: var(--card); border: 1px solid var(--rule); border-radius: 20px; padding: 1.75rem 2rem; }
/* Claude's answer brings its own headings; keep them below the question in the hierarchy */
.st-key-answer h1 { font-size: 1.35rem !important; padding-top: 0.25rem !important; }
.st-key-answer h2 { font-size: 1.15rem !important; padding-top: 0.75rem !important; }
.st-key-answer h3, .st-key-answer h4 { font-size: 1.02rem !important; }
.st-key-answer h1, .st-key-answer h2, .st-key-answer h3 { font-family: 'Fraunces', serif !important; }
.not-covered { background: var(--tint); border-left: 3px solid var(--accent); border-radius: 12px;
  padding: 1rem 1.25rem; margin-bottom: 1rem; }
.not-covered strong { display: block; margin-bottom: 0.15rem; }
.src-meta { color: var(--muted); font-size: 0.8rem; }
.st-key-back button { padding-left: 0; color: var(--muted); }
.st-key-scrolltop { display: none; }

@media (max-width: 760px) {
  .st-key-hero { padding: 2rem 1.25rem; border-radius: 20px; }
  .hero-title { font-size: 2.3rem; }
  .stats { grid-template-columns: repeat(2, 1fr); }
  .steps { grid-template-columns: 1fr; }
  .sample { transform: none; }
  .nav-meta { display: none; }
  .q-text { font-size: 1.5rem; }
  .st-key-answer { padding: 1.25rem; }
}
</style>
"""

AVATAR_COLORS = ["#c2410c", "#1f1d1a", "#b45309", "#6b665e", "#9a3412", "#57534e"]


def queue(question: str):
    st.session_state.pending = question


def submit_from(input_key: str):
    typed = st.session_state.get(input_key, "").strip()
    if typed:
        queue(typed)


def go_home():
    st.session_state.question = ""


def style_citations(answer: str) -> str:
    """Render [Episode Name] citations as small pills. '<' is escaped so model output can't inject HTML."""
    answer = answer.replace("<", "&lt;")
    # Skip markdown links like [text](url) — only bare bracketed citations become pills
    return re.sub(r"\[([^\]\n]{2,80})\](?!\()", r'<span class="cite">\1</span>', answer)


def excerpt(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= EXCERPT_CHARS else text[:EXCERPT_CHARS].rsplit(" ", 1)[0] + "…"


def html_block(markup: str):
    # Strip line indentation so Markdown doesn't mistake indented HTML for a code block
    st.markdown(" ".join(line.strip() for line in markup.splitlines()), unsafe_allow_html=True)


def nav():
    html_block("""
      <div class="nav">
        <div class="brand"><div class="mark">L</div>Ask the guests</div>
        <div class="nav-meta">Lenny's Podcast · 299 episodes · every answer cited</div>
      </div>""")


def ask_form(key: str, placeholder: str):
    # clear_on_submit empties the input after each question; Enter submits the form
    with st.form(key, clear_on_submit=True, border=False):
        col_input, col_button = st.columns([5, 1], vertical_alignment="center")
        col_input.text_input("Question", placeholder=placeholder, label_visibility="collapsed", key=f"{key}_q")
        col_button.form_submit_button("Ask", type="primary", width="stretch",
                                      on_click=submit_from, args=(f"{key}_q",))


def render_landing():
    nav()
    with st.container(key="hero"):
        left, right = st.columns([1.2, 1], gap="large", vertical_alignment="center")
        with left:
            html_block("""
              <p class="eyebrow">300 conversations with top product minds</p>
              <h1 class="display hero-title">The best product advice, <em>on demand.</em></h1>
              <p class="hero-sub">Ask anything about strategy, growth or leadership. Get an answer drawn
                from what Lenny's guests actually said, with every claim cited to its episode.</p>""")
            ask_form("ask_hero", "Ask a product question…")
            with st.container(horizontal=True, gap="small"):
                for i, q in enumerate(EXAMPLES):
                    st.button(q, key=f"chip_{i}", on_click=queue, args=(q,))
        with right:
            html_block("""
              <div class="sample">
                <p class="eyebrow">Example answer</p>
                <p class="sample-q">What is Shreyas Doshi's LNO framework?</p>
                <ul>
                  <li><b>Leverage tasks</b> return 10X–100X the effort you put in. <span class="cite">Shreyas Doshi</span></li>
                  <li><b>Neutral tasks</b> return roughly what you put in. <span class="cite">EOY Review</span></li>
                  <li><b>Overhead tasks</b> return far less, so do them quickly. <span class="cite">EOY Review</span></li>
                </ul>
                <div class="sample-foot">8 sources · 3 episodes · answered only from transcripts</div>
              </div>""")

    html_block("""
      <div class="stats">
        <div class="stat"><b>299</b><span>podcast episodes</span></div>
        <div class="stat"><b>13,204</b><span>searchable passages</span></div>
        <div class="stat"><b>8</b><span>cited sources per answer</span></div>
        <div class="stat"><b>30 → 8</b><span>passages reranked per question</span></div>
      </div>""")

    chips = "".join(
        f'<div class="guest"><div class="avatar" style="background:{AVATAR_COLORS[i % len(AVATAR_COLORS)]}">'
        f'{"".join(w[0] for w in g.split()[:2])}</div>{g}</div>'
        for i, g in enumerate(GUESTS)
    )
    # The list is rendered twice so the scroll animation loops seamlessly
    html_block(f'<div class="marquee" aria-label="Featured guests"><div class="track">{chips}{chips}</div></div>')

    html_block("""
      <p class="eyebrow">Start with a framework</p>
      <h2 class="display section-title">The ideas PMs keep coming back to</h2>
      <p class="section-sub">Pick one to see what the guest who coined it actually said.</p>""")
    for row in (FRAMEWORKS[:4], FRAMEWORKS[4:]):
        for col, (name, guest, desc, q) in zip(st.columns(4, gap="small"), row):
            slug = re.sub(r"\W+", "_", name.lower())
            with col, st.container(key=f"fw_{slug}"):
                html_block(f'<p class="fw-name">{name}</p><p class="fw-guest">{guest}</p><p class="fw-desc">{desc}</p>')
                st.button("Ask about this →", key=f"fwbtn_{slug}", type="tertiary", on_click=queue, args=(q,))

    html_block("""
      <p class="eyebrow" style="margin-top:3rem">How it works</p>
      <h2 class="display section-title">Answers with receipts</h2>
      <p class="section-sub">Built to say “I don't know” rather than make something up.</p>
      <div class="steps">
        <div class="step"><div class="step-n">1</div><h4>Search by meaning</h4>
          <p>Your question is matched against all 13,204 transcript passages by what it means, not just its keywords.</p></div>
        <div class="step"><div class="step-n">2</div><h4>Keep what answers it</h4>
          <p>A second model reads the 30 closest passages next to your question and keeps the 8 that actually answer it.</p></div>
        <div class="step"><div class="step-n">3</div><h4>Answer with citations</h4>
          <p>Claude writes only from those passages and cites the episode for every claim. If nothing fits, it says so.</p></div>
      </div>
      <div class="footer"><span>Built on Lenny's Podcast transcripts</span>
        <span>Search: Voyage embeddings + reranking · Answers: Claude</span></div>""")


def render_results():
    nav()
    with st.container(key="reading"):
        st.button("← Back to home", key="back", type="tertiary", on_click=go_home)
        ask_form("ask_results", "Ask another question…")

        answer, chunks = st.session_state.answer, st.session_state.chunks
        html_block(f'<p class="q-label">You asked</p><div class="q-text">{html.escape(st.session_state.question)}</div>')

        not_covered = answer.strip().startswith(NOT_COVERED)
        if not_covered:
            # A deliberate, calm state rather than an error: the label carries the meaning, not the colour
            html_block('<div class="not-covered"><strong>Not covered</strong>None of the episodes address this '
                       "question. Try rephrasing it, or ask about a product, growth or leadership topic.</div>")
        else:
            with st.container(key="answer"):
                st.markdown(style_citations(answer), unsafe_allow_html=True)

        episodes = list(dict.fromkeys(c["episode"] for c in chunks))
        sources_label = (
            "Closest passages found (not relevant enough to answer)"
            if not_covered
            else f"Sources · {len(chunks)} excerpts from {len(episodes)} episodes"
        )
        with st.expander(sources_label):
            for i, c in enumerate(chunks, 1):
                score = f" · relevance {c['score']:.2f}" if "score" in c else ""
                st.markdown(f"**{i}. {html.escape(c['episode'])}** <span class='src-meta'>{score}</span>",
                            unsafe_allow_html=True)
                st.caption(excerpt(c["text"]))


def start_job(question: str) -> dict:
    """Run retrieval + generation in a background thread so this script run can finish right away.

    Streamlit keeps the previous view on screen (dimmed) until a run ends, so doing the slow work
    inside the run left the landing page visible behind the progress message. The thread only
    touches this plain dict, never st.session_state, which isn't available outside the script thread.
    """
    job = {"question": question, "stage": "Finding the most relevant passages…", "done": False, "error": None}

    def work():
        try:
            chunks = retrieve(question)
            job["stage"] = f"Writing an answer from {len(chunks)} passages…"
            job["answer"], job["chunks"] = generate(question, chunks), chunks
        except Exception as e:  # surfaced in the UI rather than lost with the thread
            job["error"] = f"{type(e).__name__}: {e}"
        job["done"] = True

    threading.Thread(target=work, daemon=True).start()
    return job


def scroll_to_top():
    # Streamlit scrolls an inner container, which keeps the landing page's position when the view changes
    components.html(
        "<script>const d = window.parent.document;"
        "(d.querySelector('[data-testid=\"stMain\"]') || d.scrollingElement).scrollTo({top: 0});</script>",
        height=0,
    )


@st.fragment(run_every=0.5)
def job_progress():
    job = st.session_state.job
    if job["done"]:
        if job["error"]:
            st.session_state.error = job["error"]
        else:
            st.session_state.update(question=job["question"], answer=job["answer"], chunks=job["chunks"])
        st.session_state.job = None
        st.rerun()
    with st.status(job["stage"], expanded=False):
        pass


def render_job():
    nav()
    with st.container(key="reading"):
        html_block(f'<p class="q-label">You asked</p><div class="q-text">{html.escape(st.session_state.job["question"])}</div>')
        job_progress()
    with st.container(key="scrolltop"):
        scroll_to_top()


st.set_page_config(page_title="Ask the guests · Lenny RAG", page_icon="🎙️", layout="wide")
st.markdown(STYLE, unsafe_allow_html=True)

for key, default in [("question", ""), ("answer", ""), ("chunks", []), ("pending", ""), ("job", None), ("error", "")]:
    st.session_state.setdefault(key, default)

if st.session_state.pending:
    st.session_state.job = start_job(st.session_state.pending)
    st.session_state.pending = ""

if st.session_state.error:
    st.error(f"Something went wrong while answering: {st.session_state.error}", icon=":material/error:")
    st.session_state.error = ""

if st.session_state.job:
    render_job()
elif st.session_state.question:
    render_results()
else:
    render_landing()
