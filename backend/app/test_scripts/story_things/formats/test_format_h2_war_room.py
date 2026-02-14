#!/usr/bin/env python3
"""
H-2: The War Room — HTML Data and Layout Format Test

This script creates a story that exercises complex HTML features as node
content: tables with spanning cells, data attributes, CSS classes, nested
divs, entity encoding, and inline SVG.

NARRATIVE:
    The player is an intelligence analyst called into a crisis situation.
    Intercepted communications suggest an imminent threat, but the data is
    noisy. The player must analyze signals intelligence, human intelligence,
    and satellite imagery to produce a correct threat assessment.

HTML FEATURES EXERCISED:
    - Tables with <thead>, <tbody>, <tfoot>, colspan, rowspan
    - CSS classes on elements (for downstream rendering/theming)
    - Data attributes (data-classification, data-priority, data-source)
    - Nested divs with structural meaning (org charts, hierarchy displays)
    - Entity encoding (&amp; &lt; &mdash; numeric entities)
    - Inline SVG (simple map with positioned elements)
    - Mixed content: prose paragraphs interspersed with tables and data

STORY STRUCTURE:
    - Start: Receive intelligence briefing (large table of intercepted comms)
    - Branch: Focus on SIGINT, HUMINT, or SATINT
    - Each branch presents data in different HTML structures
    - Player interprets data and flags significant patterns
    - 3 endings: correct assessment, missed threat, false alarm

Usage:
    python test_format_h2_war_room.py
    python test_format_h2_war_room.py --verbose

Output:
    test_results_format_h2_war_room.json
"""

import json
import sys
import argparse
from datetime import datetime
from pathlib import Path

import requests

sys.path.append(str(Path(__file__).parent.parent))
from auth_helper import get_authenticated_session, AuthenticationError

BASE_URL = "http://localhost:8000/api/v1"
RESULTS_FILE = "test_results_format_h2_war_room.json"

test_results = {
    "test_suite": "Format Test H-2: The War Room (HTML Data & Layout)",
    "start_time": None,
    "end_time": None,
    "story_id": None,
    "node_ids": {},
    "choice_ids": {},
    "state_variable_ids": {},
    "success": False,
    "errors": [],
}


class WarRoomStoryBuilder:
    """Builds the War Room story exercising complex HTML content formats."""

    def __init__(self, session: requests.Session, verbose: bool = False):
        self.session = session
        self.verbose = verbose
        self.story_id = None
        self.nodes: dict[str, dict] = {}
        self.choices: list[dict] = []
        self.state_vars: dict[str, dict] = {}

    def log(self, message: str):
        print(f"  {message}")

    def debug(self, message: str):
        if self.verbose:
            print(f"  [DEBUG] {message}")

    # =========================================================================
    # API helpers
    # =========================================================================

    def create_story(self, title: str, description: str) -> dict:
        r = self.session.post(
            f"{BASE_URL}/stories",
            json={"title": title, "description": description, "current_version": 1},
        )
        if r.status_code != 200:
            raise Exception(f"Failed to create story: {r.text}")
        return r.json()

    def create_state_variable(
        self,
        key: str,
        value_type: str,
        default_value=None,
        enum_values: list | None = None,
        description: str | None = None,
        category: str | None = None,
    ) -> dict:
        payload: dict = {"key": key, "value_type": value_type}
        if default_value is not None:
            payload["default_value"] = default_value
        if enum_values:
            payload["enum_values"] = enum_values
        if description:
            payload["description"] = description
        if category:
            payload["category"] = category

        r = self.session.post(
            f"{BASE_URL}/stories/{self.story_id}/versions/1/state-schema",
            json=payload,
        )
        if r.status_code != 200:
            raise Exception(f"Failed to create state variable '{key}': {r.text}")
        return r.json()

    def create_node(
        self,
        title: str,
        content: str,
        content_format: str = "html",
        is_start: bool = False,
        is_end: bool = False,
    ) -> dict:
        r = self.session.post(
            f"{BASE_URL}/storynodes",
            json={
                "story_id": self.story_id,
                "story_version": 1,
                "title": title,
                "content": content,
                "node_type": "text",
                "content_format": content_format,
                "is_start_node": is_start,
                "is_end_node": is_end,
            },
        )
        if r.status_code != 200:
            raise Exception(f"Failed to create node '{title}': {r.text}")
        return r.json()

    def create_choice(
        self,
        from_node_name: str,
        to_node_name: str,
        text: str,
        order: int = 0,
        requires_state: dict | None = None,
        sets_state: dict | None = None,
    ) -> dict:
        from_node = self.nodes.get(from_node_name)
        to_node = self.nodes.get(to_node_name)
        if not from_node:
            raise Exception(f"From node '{from_node_name}' not found")
        if not to_node:
            raise Exception(f"To node '{to_node_name}' not found")

        payload: dict = {
            "from_node_id": from_node["id"],
            "to_node_id": to_node["id"],
            "text": text,
            "order": order,
        }
        if requires_state:
            payload["requires_state"] = requires_state
        if sets_state:
            payload["sets_state"] = sets_state

        r = self.session.post(f"{BASE_URL}/node-choices", json=payload)
        if r.status_code != 200:
            raise Exception(f"Failed to create choice '{text}': {r.text}")
        return r.json()

    def validate_state_schema(self) -> dict:
        r = self.session.get(
            f"{BASE_URL}/stories/{self.story_id}/versions/1/state-schema/validate"
        )
        if r.status_code != 200:
            raise Exception(f"Failed to validate: {r.text}")
        return r.json()

    # =========================================================================
    # Node content builders — each returns an HTML string
    # =========================================================================

    @staticmethod
    def _briefing_room_html() -> str:
        """Start node. Large intercept table with thead/tbody/tfoot, colspan,
        data-attributes, CSS classes, and entity-encoded content."""

        return """\
<article class="briefing-document" data-classification="top-secret" data-priority="flash">

<header>
  <h1>SITUATION BRIEFING &mdash; OPERATION QUIET THUNDER</h1>
  <p class="classification-banner" style="color:#c00;font-weight:bold;text-transform:uppercase;">
    TOP SECRET // NOFORN // ORCON
  </p>
  <p>Prepared: 0347Z 14&nbsp;FEB&nbsp;2026 &bull; Briefing Officer: COL&nbsp;Hargrove</p>
</header>

<section class="situation-summary">
  <h2>1. Situation Overview</h2>
  <p>
    Over the past 72&nbsp;hours, National Technical Means have detected anomalous
    activity across three collection disciplines. Signals intercepts show a
    surge in encrypted traffic on frequencies associated with the
    <strong>GRANITE</strong> network&mdash;a previously dormant command
    &amp; control infrastructure linked to state actor <em>CERULEAN</em>.
    Concurrently, HUMINT assets report unusual personnel movements, and
    satellite imagery reveals changes at two facilities of interest.
  </p>
  <p>
    Your task: analyze the available intelligence and produce a threat
    assessment before the 0600Z briefing to the National Security Council.
  </p>
</section>

<section class="intercept-log">
  <h2>2. Intercepted Communications Summary</h2>
  <table class="intercept-table" data-source="SIGINT-COLLECTION-4471">
    <thead>
      <tr>
        <th rowspan="2" style="vertical-align:bottom;">Intercept&nbsp;ID</th>
        <th rowspan="2" style="vertical-align:bottom;">Timestamp&nbsp;(Z)</th>
        <th colspan="2" style="text-align:center;border-bottom:1px solid #666;">Origin</th>
        <th colspan="2" style="text-align:center;border-bottom:1px solid #666;">Destination</th>
        <th rowspan="2" style="vertical-align:bottom;">Duration</th>
        <th rowspan="2" style="vertical-align:bottom;">Assessment</th>
      </tr>
      <tr>
        <th>Callsign</th>
        <th>Grid</th>
        <th>Callsign</th>
        <th>Grid</th>
      </tr>
    </thead>
    <tbody>
      <tr data-priority="critical" class="row-critical">
        <td>INT-4471-001</td>
        <td>11FEB 2231Z</td>
        <td>GRANITE-APEX</td>
        <td>BQ4418</td>
        <td>GRANITE-STONE-7</td>
        <td>CK8803</td>
        <td>4m&nbsp;12s</td>
        <td><span style="color:#c00;font-weight:bold;">&#9888; CRITICAL</span></td>
      </tr>
      <tr data-priority="high" class="row-high">
        <td>INT-4471-002</td>
        <td>11FEB 2258Z</td>
        <td>GRANITE-APEX</td>
        <td>BQ4418</td>
        <td>GRANITE-IRON-3</td>
        <td>DJ1172</td>
        <td>2m&nbsp;41s</td>
        <td><span style="color:#e80;">HIGH</span></td>
      </tr>
      <tr data-priority="routine">
        <td>INT-4471-003</td>
        <td>12FEB 0015Z</td>
        <td>UNKNOWN-1</td>
        <td>AL9920</td>
        <td>GRANITE-STONE-7</td>
        <td>CK8803</td>
        <td>0m&nbsp;48s</td>
        <td>ROUTINE</td>
      </tr>
      <tr data-priority="high" class="row-high">
        <td>INT-4471-004</td>
        <td>12FEB 0142Z</td>
        <td>GRANITE-APEX</td>
        <td>BQ4418</td>
        <td>GRANITE-LANCE-1</td>
        <td>FN3347</td>
        <td>6m&nbsp;03s</td>
        <td><span style="color:#e80;">HIGH</span></td>
      </tr>
      <tr data-priority="critical" class="row-critical">
        <td>INT-4471-005</td>
        <td>12FEB 0310Z</td>
        <td>GRANITE-LANCE-1</td>
        <td>FN3347</td>
        <td>GRANITE-STONE-7</td>
        <td>CK8803</td>
        <td>8m&nbsp;55s</td>
        <td><span style="color:#c00;font-weight:bold;">&#9888; CRITICAL</span></td>
      </tr>
      <tr data-priority="low">
        <td>INT-4471-006</td>
        <td>12FEB 0322Z</td>
        <td>CIVILIAN-FM</td>
        <td>BQ4400</td>
        <td>CIVILIAN-FM</td>
        <td>BQ4401</td>
        <td>1m&nbsp;10s</td>
        <td>LOW / DISCARD</td>
      </tr>
    </tbody>
    <tfoot>
      <tr>
        <td colspan="6" style="text-align:right;font-weight:bold;">
          Total intercepts (filtered): 6 of 214
        </td>
        <td colspan="2" style="font-style:italic;">
          2 CRITICAL &middot; 2 HIGH
        </td>
      </tr>
    </tfoot>
  </table>
</section>

<section class="key-observations">
  <h2>3. Initial Observations</h2>
  <div class="observation-cards" style="display:flex;gap:1em;flex-wrap:wrap;">
    <div class="card" style="border:1px solid #999;padding:0.75em;flex:1;min-width:200px;"
         data-category="pattern">
      <h3 style="margin-top:0;">Hub &amp; Spoke Pattern</h3>
      <p>GRANITE-APEX (grid BQ4418) initiated 3&nbsp;of&nbsp;6 intercepts,
      contacting three distinct subordinate nodes. This is consistent with
      a <em>command activation sequence</em>.</p>
    </div>
    <div class="card" style="border:1px solid #999;padding:0.75em;flex:1;min-width:200px;"
         data-category="anomaly">
      <h3 style="margin-top:0;">Lateral Communication</h3>
      <p>INT-4471-005 shows LANCE-1 contacting STONE-7 directly&mdash;a
      lateral link not previously observed. Duration (8m&nbsp;55s) is
      abnormally long for this network.</p>
    </div>
    <div class="card" style="border:1px solid #999;padding:0.75em;flex:1;min-width:200px;"
         data-category="noise">
      <h3 style="margin-top:0;">Civilian Traffic</h3>
      <p>INT-4471-006 is almost certainly civilian FM radio bleed.
      Grid proximity to APEX is coincidental (BQ44xx range is a
      populated area). Recommend discard.</p>
    </div>
  </div>
</section>

<footer style="margin-top:2em;border-top:1px solid #ccc;padding-top:0.5em;">
  <p><small>DISTRIBUTION: EYES ONLY &mdash; NSC PRINCIPALS</small></p>
  <p><small>Derived from: NSA/CSS Report 2026-0214-SIGINT, CIA PDB Supplement,
  NGA Imagery Assessment IA-2026-0412</small></p>
</footer>

</article>"""

    @staticmethod
    def _sigint_analysis_html() -> str:
        """SIGINT branch. Complex table with rowspan grouping, entity encoding,
        and a frequency-analysis SVG chart."""

        return """\
<article class="analysis-report" data-classification="top-secret"
         data-discipline="SIGINT" data-analyst="ANALYST-7">

<h1>SIGNALS INTELLIGENCE &mdash; DEEP ANALYSIS</h1>
<p class="classification-banner" style="color:#c00;font-weight:bold;">
  TOP SECRET // SI // NOFORN
</p>

<section>
  <h2>Frequency Activity &mdash; GRANITE Network (72h)</h2>

  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 220"
       style="max-width:600px;width:100%;border:1px solid #ccc;background:#fafafa;">
    <!-- Axes -->
    <line x1="60" y1="10" x2="60" y2="180" stroke="#333" stroke-width="1.5"/>
    <line x1="60" y1="180" x2="580" y2="180" stroke="#333" stroke-width="1.5"/>
    <!-- Y-axis labels -->
    <text x="55" y="15" text-anchor="end" font-size="10" fill="#555">50</text>
    <text x="55" y="55" text-anchor="end" font-size="10" fill="#555">40</text>
    <text x="55" y="95" text-anchor="end" font-size="10" fill="#555">30</text>
    <text x="55" y="135" text-anchor="end" font-size="10" fill="#555">20</text>
    <text x="55" y="175" text-anchor="end" font-size="10" fill="#555">10</text>
    <text x="30" y="100" text-anchor="middle" font-size="11" fill="#333"
          transform="rotate(-90,30,100)">Transmissions</text>
    <!-- X-axis labels (hours) -->
    <text x="60"  y="195" text-anchor="middle" font-size="10" fill="#555">-72h</text>
    <text x="147" y="195" text-anchor="middle" font-size="10" fill="#555">-60h</text>
    <text x="233" y="195" text-anchor="middle" font-size="10" fill="#555">-48h</text>
    <text x="320" y="195" text-anchor="middle" font-size="10" fill="#555">-36h</text>
    <text x="407" y="195" text-anchor="middle" font-size="10" fill="#555">-24h</text>
    <text x="493" y="195" text-anchor="middle" font-size="10" fill="#555">-12h</text>
    <text x="580" y="195" text-anchor="middle" font-size="10" fill="#555">Now</text>
    <!-- Baseline (dormant period) -->
    <polyline fill="none" stroke="#07a" stroke-width="2"
              points="60,173 147,176 233,173 320,170 360,173"/>
    <!-- Spike onset at ~30h ago -->
    <polyline fill="none" stroke="#c00" stroke-width="2.5"
              points="360,173 380,140 407,65 440,38 470,28 493,18 530,15 560,22 580,25"/>
    <!-- Threshold line -->
    <line x1="60" y1="135" x2="580" y2="135" stroke="#e80" stroke-dasharray="6,4"
          stroke-width="1"/>
    <text x="585" y="138" font-size="9" fill="#e80">ALERT THRESHOLD</text>
    <!-- Annotation -->
    <rect x="350" y="200" width="230" height="18" rx="3" fill="#fee" stroke="#c00"/>
    <text x="465" y="213" text-anchor="middle" font-size="10" fill="#c00"
          font-weight="bold">&#9888; Exponential increase from -30h</text>
  </svg>
</section>

<section>
  <h2>Encryption Analysis</h2>
  <table data-source="NSA-CRYPTO-ASSESSMENT">
    <thead>
      <tr>
        <th>Intercept&nbsp;ID</th>
        <th>Cipher&nbsp;Suite</th>
        <th>Key&nbsp;Exchange</th>
        <th>Assessment</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td rowspan="3" style="vertical-align:top;font-weight:bold;">
          INT-4471-001<br>INT-4471-002<br>INT-4471-004
        </td>
        <td>AES-256-GCM</td>
        <td>ECDH (P-384)</td>
        <td>Standard GRANITE encryption. Key rotation at expected interval.</td>
      </tr>
      <tr>
        <td colspan="3" style="background:#fff8e0;padding:0.5em;">
          <strong>Note:</strong> All three APEX-originated messages used the
          <em>same session key</em>&mdash;unusual. Normally GRANITE rotates
          per-message. Suggests messages were <strong>pre-staged</strong>
          &amp;&nbsp;transmitted in rapid sequence.
        </td>
      </tr>
      <tr>
        <td colspan="3" style="font-size:0.9em;color:#666;">
          Confidence: HIGH &middot; Analyst: NSA/CSS TAO Division
        </td>
      </tr>
      <tr>
        <td>INT-4471-005</td>
        <td>ChaCha20-Poly1305</td>
        <td>X25519</td>
        <td style="color:#c00;font-weight:bold;">
          &#9888; Different cipher suite from rest of GRANITE network.
          LANCE-1 &amp; STONE-7 may be using an <em>out-of-band</em> channel
          not controlled by APEX.
        </td>
      </tr>
      <tr>
        <td>INT-4471-003</td>
        <td>Unknown</td>
        <td>Unknown</td>
        <td>
          Insufficient sample. 48-second duration too short for reliable
          crypto&nbsp;analysis. Origin callsign unresolved&mdash;possibly
          a&nbsp;new node or spoofed identity.
        </td>
      </tr>
    </tbody>
  </table>
</section>

<section>
  <h2>Pattern Assessment</h2>
  <p>
    The SIGINT picture shows two distinct patterns requiring attention:
  </p>
  <ol>
    <li>
      <strong>Command activation sequence</strong> &mdash; APEX pre-staged
      three messages to subordinate nodes within 3&nbsp;hours. This matches
      the profile of a <em>coordinated tasking order</em>, not routine
      communications. The shared session key is the strongest indicator:
      it suggests the messages were composed together before transmission.
    </li>
    <li>
      <strong>Anomalous lateral link</strong> &mdash; LANCE-1 &rArr; STONE-7
      using a different cipher suite is concerning. If these nodes are
      coordinating outside APEX&rsquo;s control, it could indicate either
      (a)&nbsp;operational compartmentalization or (b)&nbsp;a rogue element
      within the GRANITE network.
    </li>
  </ol>
  <p>
    <strong>Key question:</strong> Is APEX aware of the LANCE&ndash;STONE
    lateral link? The answer changes the threat model significantly.
  </p>
</section>

</article>"""

    @staticmethod
    def _humint_analysis_html() -> str:
        """HUMINT branch. Org chart using nested divs with CSS classes and
        data-attributes. Mixed content with blockquotes."""

        return """\
<article class="analysis-report" data-classification="top-secret"
         data-discipline="HUMINT" data-analyst="ANALYST-12">

<h1>HUMAN INTELLIGENCE &mdash; SOURCE REPORTING</h1>
<p class="classification-banner" style="color:#c00;font-weight:bold;">
  TOP SECRET // HCS // NOFORN
</p>

<section>
  <h2>CERULEAN Command Structure (Assessed)</h2>
  <p>
    The following organizational chart is derived from two corroborated
    HUMINT sources (JADE FALCON and AMBER LIGHT) reporting over the past
    18&nbsp;months. Nodes marked with &#9733; have been confirmed by
    secondary collection. Nodes marked with &#63; remain single-source.
  </p>

  <div class="org-chart" style="text-align:center;" data-source="CIA/DO">
    <!-- Level 0: Supreme Command -->
    <div class="org-node" data-role="command" data-confidence="confirmed"
         style="display:inline-block;border:2px solid #333;padding:0.5em 1.5em;
                background:#e8e8e8;font-weight:bold;">
      CERULEAN SUPREME COMMAND &#9733;
      <div style="font-size:0.8em;font-weight:normal;color:#555;">
        Callsign: GRANITE-APEX &middot; Grid: BQ4418
      </div>
    </div>
    <div style="text-align:center;font-size:1.5em;line-height:1;">&#9474;</div>

    <!-- Level 1: Three directorates -->
    <div style="display:flex;justify-content:center;gap:2em;flex-wrap:wrap;">
      <div class="org-node" data-role="directorate" data-confidence="confirmed"
           style="border:2px solid #07a;padding:0.5em 1em;min-width:160px;">
        <strong>MILITARY OPS &#9733;</strong>
        <div style="font-size:0.8em;color:#555;">
          Callsign: GRANITE-LANCE-1<br>Grid: FN3347
        </div>
        <div style="text-align:center;font-size:1.2em;">&#9474;</div>
        <div style="display:flex;gap:0.5em;justify-content:center;">
          <div class="org-node" data-role="unit" data-confidence="single-source"
               style="border:1px dashed #999;padding:0.3em;font-size:0.85em;">
            Unit LANCE-2 &#63;<br>
            <span style="font-size:0.8em;color:#888;">Grid: FN3350</span>
          </div>
          <div class="org-node" data-role="unit" data-confidence="single-source"
               style="border:1px dashed #999;padding:0.3em;font-size:0.85em;">
            Unit LANCE-3 &#63;<br>
            <span style="font-size:0.8em;color:#888;">Grid: FN3342</span>
          </div>
        </div>
      </div>

      <div class="org-node" data-role="directorate" data-confidence="confirmed"
           style="border:2px solid #07a;padding:0.5em 1em;min-width:160px;">
        <strong>LOGISTICS &#9733;</strong>
        <div style="font-size:0.8em;color:#555;">
          Callsign: GRANITE-STONE-7<br>Grid: CK8803
        </div>
        <div style="text-align:center;font-size:1.2em;">&#9474;</div>
        <div class="org-node" data-role="unit" data-confidence="confirmed"
             style="border:1px solid #999;padding:0.3em;font-size:0.85em;">
          Supply Depot STONE-8 &#9733;<br>
          <span style="font-size:0.8em;color:#888;">Grid: CK8810</span>
        </div>
      </div>

      <div class="org-node" data-role="directorate" data-confidence="single-source"
           style="border:2px dashed #e80;padding:0.5em 1em;min-width:160px;">
        <strong>INTEL / CI &#63;</strong>
        <div style="font-size:0.8em;color:#555;">
          Callsign: GRANITE-MIRROR<br>Grid: Unknown
        </div>
        <div style="font-size:0.75em;color:#c00;margin-top:0.3em;">
          Single-source (AMBER LIGHT only).<br>
          Counter-intelligence directorate&mdash;may be aware of our sources.
        </div>
      </div>
    </div>
  </div>
</section>

<section>
  <h2>Source Reporting &mdash; Key Excerpts</h2>

  <h3>Source: JADE FALCON (Reliability: B &middot; Credibility: 2)</h3>
  <blockquote cite="CIA-HUMINT-JF-2026-0211"
              style="border-left:3px solid #07a;padding-left:1em;margin:1em 0;">
    <p>
      &ldquo;LANCE-1 has recalled all field personnel to garrison as of
      48&nbsp;hours ago. Training exercises have been suspended. The official
      explanation is &lsquo;equipment maintenance&rsquo; but junior officers
      are being told to prepare personal affairs. This is not consistent with
      maintenance.&rdquo;
    </p>
    <footer style="font-size:0.85em;color:#666;">
      &mdash; Report JF-2026-0211, dated 12&nbsp;FEB&nbsp;2026
    </footer>
  </blockquote>

  <h3>Source: AMBER LIGHT (Reliability: C &middot; Credibility: 3)</h3>
  <blockquote cite="CIA-HUMINT-AL-2026-0212"
              style="border-left:3px solid #e80;padding-left:1em;margin:1em 0;">
    <p>
      &ldquo;STONE-7 received three large shipments in the past week&mdash;fuel,
      rations, and what source believes were ammunition containers marked with
      the CERULEAN logistics code for &#8216;priority materiel.&#8217; Shipments
      arrived at night. Depot personnel were restricted from leave.&rdquo;
    </p>
    <footer style="font-size:0.85em;color:#666;">
      &mdash; Report AL-2026-0212, dated 13&nbsp;FEB&nbsp;2026
    </footer>
  </blockquote>
  <blockquote cite="CIA-HUMINT-AL-2026-0212-ADDENDUM"
              style="border-left:3px solid #c00;padding-left:1em;margin:1em 0;">
    <p>
      &ldquo;Source additionally reports a rumor&mdash;unconfirmed&mdash;that
      GRANITE-MIRROR has been conducting internal security sweeps. If true,
      our collection window may be closing.&rdquo;
    </p>
    <footer style="font-size:0.85em;color:#666;">
      &mdash; Addendum to AL-2026-0212 (source-initiated, unscheduled contact)
    </footer>
  </blockquote>
</section>

<section>
  <h2>Assessment</h2>
  <p>
    HUMINT reporting corroborates the SIGINT picture: CERULEAN is
    <strong>mobilizing</strong>. The combination of personnel recall (LANCE),
    logistics surge (STONE), and the anomalous LANCE&ndash;STONE lateral
    communication suggests coordinated preparation for an operation.
  </p>
  <p>
    The GRANITE-MIRROR intelligence is concerning but single-source.
    If CERULEAN&rsquo;s counter-intelligence arm is active, our sources
    may be compromised&mdash;or may be feeding us what CERULEAN wants
    us to see.
  </p>
</section>

</article>"""

    @staticmethod
    def _satint_analysis_html() -> str:
        """Satellite imagery branch. SVG map with facility positions, plus a
        comparison table using data attributes."""

        return """\
<article class="analysis-report" data-classification="top-secret"
         data-discipline="IMINT" data-analyst="ANALYST-3">

<h1>SATELLITE IMAGERY &mdash; FACILITY ASSESSMENT</h1>
<p class="classification-banner" style="color:#c00;font-weight:bold;">
  TOP SECRET // TK // NOFORN
</p>

<section>
  <h2>Area of Interest &mdash; Operational Map</h2>
  <p>
    Three facilities of interest identified within the CERULEAN operational
    area. Imagery from NGA commercial &amp; national assets, 11&ndash;13
    FEB 2026.
  </p>

  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 400"
       style="max-width:500px;width:100%;border:1px solid #999;background:#e8eee8;">
    <!-- Terrain grid -->
    <defs>
      <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
        <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#cdc" stroke-width="0.5"/>
      </pattern>
    </defs>
    <rect width="500" height="400" fill="url(#grid)"/>
    <!-- Scale bar -->
    <line x1="20" y1="380" x2="120" y2="380" stroke="#333" stroke-width="2"/>
    <text x="70" y="375" text-anchor="middle" font-size="10" fill="#333">50 km</text>
    <!-- Facility: APEX HQ (BQ4418) -->
    <rect x="195" y="90" width="16" height="16" fill="#c00" stroke="#800" stroke-width="1.5"/>
    <text x="220" y="103" font-size="11" fill="#333" font-weight="bold">APEX HQ</text>
    <text x="220" y="115" font-size="9" fill="#666">BQ4418 &middot; Command</text>
    <!-- Facility: LANCE garrison (FN3347) -->
    <circle cx="380" cy="170" r="9" fill="#07a" stroke="#046" stroke-width="1.5"/>
    <text x="398" y="168" font-size="11" fill="#333" font-weight="bold">LANCE-1</text>
    <text x="398" y="180" font-size="9" fill="#666">FN3347 &middot; Military</text>
    <!-- Facility: STONE depot (CK8803) -->
    <polygon points="110,275 120,258 130,275" fill="#e80" stroke="#a60" stroke-width="1.5"/>
    <text x="140" y="268" font-size="11" fill="#333" font-weight="bold">STONE-7</text>
    <text x="140" y="280" font-size="9" fill="#666">CK8803 &middot; Logistics</text>
    <!-- Communication lines -->
    <line x1="203" y1="106" x2="371" y2="170" stroke="#333"
          stroke-width="1" stroke-dasharray="5,3"/>
    <line x1="203" y1="106" x2="120" y2="265" stroke="#333"
          stroke-width="1" stroke-dasharray="5,3"/>
    <!-- Anomalous lateral link (highlighted) -->
    <line x1="371" y1="179" x2="130" y2="270" stroke="#c00"
          stroke-width="2" stroke-dasharray="3,2"/>
    <text x="250" y="240" font-size="10" fill="#c00" font-weight="bold"
          text-anchor="middle">ANOMALOUS LINK</text>
    <!-- Legend -->
    <rect x="340" y="310" width="150" height="80" rx="4" fill="#fff" stroke="#999"/>
    <text x="415" y="327" text-anchor="middle" font-size="10" font-weight="bold"
          fill="#333">LEGEND</text>
    <rect x="350" y="335" width="10" height="10" fill="#c00"/>
    <text x="367" y="344" font-size="9" fill="#333">Command</text>
    <circle cx="355" cy="358" r="5" fill="#07a"/>
    <text x="367" y="362" font-size="9" fill="#333">Military</text>
    <polygon points="350,378 355,368 360,378" fill="#e80"/>
    <text x="367" y="378" font-size="9" fill="#333">Logistics</text>
  </svg>
</section>

<section>
  <h2>Change Detection &mdash; Facility Comparison</h2>
  <table data-source="NGA-IMINT-2026-0412">
    <thead>
      <tr>
        <th>Facility</th>
        <th>Observation (7&nbsp;FEB)</th>
        <th>Observation (13&nbsp;FEB)</th>
        <th>Change Assessment</th>
      </tr>
    </thead>
    <tbody>
      <tr data-facility="apex">
        <td><strong>APEX HQ</strong><br><small>BQ4418</small></td>
        <td>
          4 vehicles in compound.<br>
          Normal antenna configuration.<br>
          No unusual thermal signature.
        </td>
        <td>
          12 vehicles in compound (&#43;8).<br>
          Additional antenna array erected on east building.<br>
          Thermal signature consistent with 24/7 operations.
        </td>
        <td style="color:#c00;">
          <strong>SIGNIFICANT.</strong> Vehicle surge &amp; new antenna
          suggest expanded C2 operations.
        </td>
      </tr>
      <tr data-facility="lance">
        <td><strong>LANCE-1</strong><br><small>FN3347</small></td>
        <td>
          Garrison at ~40% vehicle capacity.<br>
          Training range active (track marks).<br>
          Standard dispersal pattern.
        </td>
        <td>
          Garrison at ~95% vehicle capacity (&#43;55%).<br>
          Training range inactive (no new tracks).<br>
          Vehicles in <em>road march</em> formation, not dispersed.
        </td>
        <td style="color:#c00;">
          <strong>SIGNIFICANT.</strong> Full recall with road-march staging.
          Consistent with deployment preparation, <em>not</em> exercises.
        </td>
      </tr>
      <tr data-facility="stone">
        <td><strong>STONE-7</strong><br><small>CK8803</small></td>
        <td>
          2 cargo trucks at loading dock.<br>
          Warehouse doors closed.<br>
          Perimeter security: 1 guard post active.
        </td>
        <td>
          8 cargo trucks at loading dock (&#43;6).<br>
          Warehouse doors open; crates visible on pallets.<br>
          Perimeter security: 4 guard posts active (&#43;3).<br>
          <em>New: camouflage netting over south lot.</em>
        </td>
        <td style="color:#e80;">
          <strong>NOTABLE.</strong> Logistics surge confirmed. Camouflage
          netting suggests awareness of overhead surveillance.
        </td>
      </tr>
    </tbody>
  </table>
</section>

<section>
  <h2>Imagery Assessment</h2>
  <p>
    Satellite imagery confirms large-scale activity at all three CERULEAN
    facilities. The pattern&mdash;vehicle recall, logistics surge, enhanced
    security, camouflage&mdash;is consistent with <strong>pre-operational
    preparation</strong>.
  </p>
  <p>
    The camouflage netting at STONE-7 is particularly concerning: it
    indicates CERULEAN is aware of (or assumes) overhead surveillance and
    is attempting to deny us further collection. Combined with the
    GRANITE-MIRROR counter-intelligence reporting, this suggests a
    <em>denial &amp; deception</em> posture.
  </p>
</section>

</article>"""

    @staticmethod
    def _synthesis_html() -> str:
        """Synthesis node. Consolidation table, data attributes, entity
        encoding, decision framing."""

        return """\
<article class="synthesis-report" data-classification="top-secret" data-priority="flash">

<h1>INTELLIGENCE SYNTHESIS &mdash; ALL SOURCES</h1>
<p class="classification-banner" style="color:#c00;font-weight:bold;">
  TOP SECRET // SI // HCS // TK // NOFORN
</p>

<section>
  <h2>Consolidated Indicator Matrix</h2>
  <table class="indicator-matrix" data-source="MULTI-INT">
    <thead>
      <tr>
        <th rowspan="2">Indicator</th>
        <th colspan="3" style="text-align:center;border-bottom:1px solid #666;">
          Collection Discipline
        </th>
        <th rowspan="2">Confidence</th>
      </tr>
      <tr>
        <th>SIGINT</th>
        <th>HUMINT</th>
        <th>IMINT</th>
      </tr>
    </thead>
    <tbody>
      <tr data-indicator="command-activation">
        <td>Command activation sequence</td>
        <td style="text-align:center;">&#9679;</td>
        <td style="text-align:center;">&mdash;</td>
        <td style="text-align:center;">&#9679;</td>
        <td><strong>HIGH</strong> (2 sources)</td>
      </tr>
      <tr data-indicator="personnel-recall">
        <td>Personnel recall to garrison</td>
        <td style="text-align:center;">&mdash;</td>
        <td style="text-align:center;">&#9679;</td>
        <td style="text-align:center;">&#9679;</td>
        <td><strong>HIGH</strong> (2 sources)</td>
      </tr>
      <tr data-indicator="logistics-surge">
        <td>Logistics surge at STONE-7</td>
        <td style="text-align:center;">&#9679;</td>
        <td style="text-align:center;">&#9679;</td>
        <td style="text-align:center;">&#9679;</td>
        <td><strong>VERY HIGH</strong> (3 sources)</td>
      </tr>
      <tr data-indicator="lateral-comms">
        <td>Anomalous LANCE&ndash;STONE lateral link</td>
        <td style="text-align:center;">&#9679;</td>
        <td style="text-align:center;">&mdash;</td>
        <td style="text-align:center;">&mdash;</td>
        <td>MODERATE (single discipline)</td>
      </tr>
      <tr data-indicator="counter-intel">
        <td>Counter-intelligence activity (MIRROR)</td>
        <td style="text-align:center;">&mdash;</td>
        <td style="text-align:center;">&#9675;</td>
        <td style="text-align:center;">&#9675;</td>
        <td>LOW (single-source, indirect)</td>
      </tr>
      <tr data-indicator="camouflage">
        <td>Camouflage &amp; denial measures</td>
        <td style="text-align:center;">&mdash;</td>
        <td style="text-align:center;">&mdash;</td>
        <td style="text-align:center;">&#9679;</td>
        <td>MODERATE (imagery only)</td>
      </tr>
    </tbody>
    <tfoot>
      <tr>
        <td colspan="5" style="font-style:italic;font-size:0.9em;">
          &#9679; = confirmed &middot; &#9675; = partial/circumstantial &middot;
          &mdash; = not observed in this discipline
        </td>
      </tr>
    </tfoot>
  </table>
</section>

<section>
  <h2>Analytical Judgments</h2>
  <p>
    Three of six indicators are corroborated by multiple collection
    disciplines. The convergence of SIGINT, HUMINT, and IMINT on
    a <em>logistics surge</em> is the strongest signal: it is confirmed
    at the highest confidence level.
  </p>
  <p>
    The overall pattern&mdash;command activation, personnel recall,
    logistics buildup, road-march staging, denial &amp; deception&mdash;is
    consistent with <strong>preparation for a military operation within
    7&ndash;14&nbsp;days</strong>.
  </p>
  <p>
    However, two alternative explanations must be considered:
  </p>
  <ol>
    <li>
      <strong>Large-scale exercise:</strong> CERULEAN has conducted major
      exercises before. The differentiator is the <em>camouflage netting</em>
      and the <em>pre-staged encrypted messages</em>&mdash;neither is
      consistent with exercises designed to be visible.
    </li>
    <li>
      <strong>Deception operation:</strong> If GRANITE-MIRROR knows about
      our sources and collection, CERULEAN could be staging a false
      mobilization to test our response or to mask the <em>real</em>
      operation elsewhere. The single-source MIRROR intelligence makes
      this hard to evaluate.
    </li>
  </ol>

  <h2>Your Assessment Required</h2>
  <p>
    Based on the available intelligence, select the threat level for
    the 0600Z NSC briefing:
  </p>
</section>

</article>"""

    @staticmethod
    def _ending_correct_html() -> str:
        """Correct assessment ending."""

        return """\
<article class="assessment-result" data-classification="top-secret"
         data-outcome="correct">

<h1>NSC BRIEFING &mdash; ASSESSMENT: <span style="color:#c00;">HIGH THREAT</span></h1>

<section>
  <h2>Outcome</h2>
  <p>
    Your assessment was <strong>confirmed within 72&nbsp;hours</strong>.
  </p>
  <p>
    CERULEAN launched a limited military operation against a border outpost
    exactly as the intelligence indicators predicted. Because your HIGH threat
    assessment reached the NSC in time, defensive measures were activated and
    the attack was blunted. Casualties were minimal on our side.
  </p>

  <h2>After-Action Notes</h2>
  <dl>
    <dt>SIGINT contribution</dt>
    <dd>The pre-staged encryption keys were the earliest warning sign. This
    indicator alone&mdash;identified 30&nbsp;hours before the attack&mdash;provided
    the critical decision-making window.</dd>

    <dt>HUMINT contribution</dt>
    <dd>JADE FALCON&rsquo;s reporting on personnel recall was accurate and
    timely. AMBER LIGHT&rsquo;s logistics reporting was corroborated by imagery.</dd>

    <dt>IMINT contribution</dt>
    <dd>Road-march formation at LANCE-1 was the most unambiguous indicator
    of offensive intent versus exercise activity.</dd>

    <dt>MIRROR assessment</dt>
    <dd>Post-operation analysis confirmed GRANITE-MIRROR exists but had
    <em>not</em> yet identified our sources at the time of the attack.
    The security sweeps were routine, not targeted. Source safety confirmed.</dd>
  </dl>
</section>

</article>"""

    @staticmethod
    def _ending_missed_html() -> str:
        """Missed threat ending."""

        return """\
<article class="assessment-result" data-classification="top-secret"
         data-outcome="missed-threat">

<h1>NSC BRIEFING &mdash; ASSESSMENT: <span style="color:#07a;">LOW THREAT</span></h1>

<section>
  <h2>Outcome</h2>
  <p>
    Your assessment was <strong style="color:#c00;">tragically incorrect</strong>.
  </p>
  <p>
    CERULEAN launched a military operation 5&nbsp;days later. Because the NSC
    received a LOW threat assessment, defensive posture was not elevated.
    The attack achieved tactical surprise. Significant casualties resulted.
  </p>

  <h2>Post-Mortem</h2>
  <p>
    The review board identified that all necessary indicators were present
    in the intelligence you received. The failure was in <em>interpretation</em>,
    not <em>collection</em>.
  </p>
  <table>
    <thead>
      <tr>
        <th>Indicator</th>
        <th>What It Meant</th>
        <th>How It Was Read</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Pre-staged encryption keys</td>
        <td>Coordinated command orders</td>
        <td>Dismissed as technical anomaly</td>
      </tr>
      <tr>
        <td>Personnel recall + road-march staging</td>
        <td>Deployment preparation</td>
        <td>Assessed as routine exercise</td>
      </tr>
      <tr>
        <td>Logistics surge + camouflage</td>
        <td>Operational security for real operation</td>
        <td>Insufficient weight given to camouflage indicator</td>
      </tr>
    </tbody>
  </table>
  <p>
    The lesson: when multiple intelligence disciplines converge on the same
    conclusion, the default should be to take the threat seriously&mdash;even
    when alternative explanations exist.
  </p>
</section>

</article>"""

    @staticmethod
    def _ending_false_alarm_html() -> str:
        """False alarm / overcorrection ending."""

        return """\
<article class="assessment-result" data-classification="top-secret"
         data-outcome="false-alarm">

<h1>NSC BRIEFING &mdash; ASSESSMENT: <span style="color:#c00;">CRITICAL THREAT</span></h1>

<section>
  <h2>Outcome</h2>
  <p>
    Your CRITICAL assessment triggered an <strong>immediate military
    response</strong>&mdash;which turned out to be a significant
    <em>overcorrection</em>.
  </p>
  <p>
    While CERULEAN was indeed preparing a limited border operation, the
    CRITICAL designation implied an imminent, large-scale attack. Our
    response&mdash;full force mobilization and diplomatic escalation&mdash;was
    disproportionate. The resulting tensions took months to de-escalate.
  </p>

  <h2>Where the Analysis Went Wrong</h2>
  <dl>
    <dt>The MIRROR intelligence</dt>
    <dd>
      You weighted the counter-intelligence reporting (GRANITE-MIRROR
      security sweeps) too heavily. This was single-source, low-confidence
      intelligence from AMBER LIGHT. Treating it as confirmed led to an
      inflated threat picture&mdash;a &ldquo;deception within a
      deception&rdquo; theory that the evidence did not support.
    </dd>

    <dt>Proportionality</dt>
    <dd>
      The indicators supported HIGH threat (imminent limited operation),
      not CRITICAL (large-scale attack). The difference matters: CRITICAL
      triggers automatic responses that remove decision-making time from
      policymakers.
    </dd>

    <dt>The false positive cost</dt>
    <dd>
      False alarms at the CRITICAL level erode trust in intelligence
      assessments. Future genuine CRITICAL warnings may be discounted.
      This is the &ldquo;cry wolf&rdquo; problem in intelligence analysis.
    </dd>
  </dl>
</section>

</article>"""

    # =========================================================================
    # Build the story
    # =========================================================================

    def build_story(self) -> bool:
        """Construct the full War Room story."""

        # =================================================================
        # STEP 1: CREATE STORY
        # =================================================================
        self.log("\n📖 Creating story...")

        story = self.create_story(
            title="The War Room: Operation Quiet Thunder",
            description=(
                "An intelligence analysis exercise testing the player's ability "
                "to synthesize SIGINT, HUMINT, and satellite imagery into a "
                "coherent threat assessment. All node content is HTML, exercising "
                "complex tables, inline SVG, data attributes, entity encoding, "
                "CSS classes, nested divs, and semantic structure."
            ),
        )
        self.story_id = story["id"]
        test_results["story_id"] = self.story_id
        self.log(f"  Created story: {self.story_id}")

        # =================================================================
        # STEP 2: STATE SCHEMA
        # =================================================================
        self.log("\n📋 Creating state schema...")

        self.state_vars["signals_analyzed"] = self.create_state_variable(
            key="signals_analyzed",
            value_type="boolean",
            default_value=False,
            category="analysis",
            description="Player completed SIGINT analysis branch",
        )

        self.state_vars["humint_analyzed"] = self.create_state_variable(
            key="humint_analyzed",
            value_type="boolean",
            default_value=False,
            category="analysis",
            description="Player completed HUMINT analysis branch",
        )

        self.state_vars["satellite_analyzed"] = self.create_state_variable(
            key="satellite_analyzed",
            value_type="boolean",
            default_value=False,
            category="analysis",
            description="Player completed satellite imagery analysis branch",
        )

        self.state_vars["identified_primary_threat"] = self.create_state_variable(
            key="identified_primary_threat",
            value_type="boolean",
            default_value=False,
            category="analysis",
            description="Player identified the logistics surge as the primary indicator",
        )

        self.state_vars["false_positive_count"] = self.create_state_variable(
            key="false_positive_count",
            value_type="number",
            default_value=0,
            category="analysis",
            description="Number of false-positive flags raised by the player",
        )

        self.state_vars["disciplines_completed"] = self.create_state_variable(
            key="disciplines_completed",
            value_type="number",
            default_value=0,
            category="progress",
            description="Number of intelligence disciplines analyzed (0-3)",
        )

        self.state_vars["threat_assessment"] = self.create_state_variable(
            key="threat_assessment",
            value_type="enum",
            enum_values=["unknown", "low", "moderate", "high", "critical"],
            default_value="unknown",
            category="conclusions",
            description="Player's final threat assessment for the NSC briefing",
        )

        self.state_vars["correct_assessment"] = self.create_state_variable(
            key="correct_assessment",
            value_type="boolean",
            default_value=False,
            category="conclusions",
            description="Whether the player's assessment was correct (HIGH)",
        )

        self.state_vars["weighted_mirror"] = self.create_state_variable(
            key="weighted_mirror_intel",
            value_type="boolean",
            default_value=False,
            category="analysis",
            description="Player gave significant weight to the single-source MIRROR intel",
        )

        test_results["state_variable_ids"] = {
            k: v.get("id") for k, v in self.state_vars.items()
        }
        self.log(f"  Created {len(self.state_vars)} state variables")

        # =================================================================
        # STEP 3: NODES
        # =================================================================
        self.log("\n📝 Creating story nodes...")

        self.nodes["briefing"] = self.create_node(
            title="The Briefing Room",
            content=self._briefing_room_html(),
            content_format="html",
            is_start=True,
        )
        self.debug("Created node: briefing (START)")

        self.nodes["sigint"] = self.create_node(
            title="Signals Intelligence Analysis",
            content=self._sigint_analysis_html(),
            content_format="html",
        )
        self.debug("Created node: sigint")

        self.nodes["humint"] = self.create_node(
            title="Human Intelligence Analysis",
            content=self._humint_analysis_html(),
            content_format="html",
        )
        self.debug("Created node: humint")

        self.nodes["satint"] = self.create_node(
            title="Satellite Imagery Analysis",
            content=self._satint_analysis_html(),
            content_format="html",
        )
        self.debug("Created node: satint")

        self.nodes["synthesis"] = self.create_node(
            title="Intelligence Synthesis",
            content=self._synthesis_html(),
            content_format="html",
        )
        self.debug("Created node: synthesis")

        self.nodes["ending_correct"] = self.create_node(
            title="Correct Assessment: HIGH Threat",
            content=self._ending_correct_html(),
            content_format="html",
            is_end=True,
        )
        self.debug("Created node: ending_correct (END)")

        self.nodes["ending_missed"] = self.create_node(
            title="Missed Threat: LOW Assessment",
            content=self._ending_missed_html(),
            content_format="html",
            is_end=True,
        )
        self.debug("Created node: ending_missed (END)")

        self.nodes["ending_false_alarm"] = self.create_node(
            title="Overcorrection: CRITICAL Assessment",
            content=self._ending_false_alarm_html(),
            content_format="html",
            is_end=True,
        )
        self.debug("Created node: ending_false_alarm (END)")

        test_results["node_ids"] = {
            name: node["id"] for name, node in self.nodes.items()
        }
        self.log(f"  Created {len(self.nodes)} nodes")

        # =================================================================
        # STEP 4: CHOICES
        # =================================================================
        self.log("\n🔀 Creating choices...")

        # --- FROM: briefing → three analysis branches ---

        self.choices.append(
            self.create_choice(
                from_node_name="briefing",
                to_node_name="sigint",
                text="Focus on Signals Intelligence — analyze the encrypted traffic patterns",
                order=0,
            )
        )
        self.debug("Created choice: briefing → sigint")

        self.choices.append(
            self.create_choice(
                from_node_name="briefing",
                to_node_name="humint",
                text="Focus on Human Intelligence — review source reporting",
                order=1,
            )
        )
        self.debug("Created choice: briefing → humint")

        self.choices.append(
            self.create_choice(
                from_node_name="briefing",
                to_node_name="satint",
                text="Focus on Satellite Imagery — examine the facilities",
                order=2,
            )
        )
        self.debug("Created choice: briefing → satint")

        # --- FROM: sigint → synthesis or other branches ---

        self.choices.append(
            self.create_choice(
                from_node_name="sigint",
                to_node_name="synthesis",
                text="Proceed to synthesis — I've seen enough to form an assessment",
                order=0,
                sets_state={
                    "signals_analyzed": True,
                    "disciplines_completed": 1,
                },
            )
        )

        self.choices.append(
            self.create_choice(
                from_node_name="sigint",
                to_node_name="humint",
                text="Cross-reference with Human Intelligence before concluding",
                order=1,
                sets_state={
                    "signals_analyzed": True,
                },
            )
        )

        self.choices.append(
            self.create_choice(
                from_node_name="sigint",
                to_node_name="satint",
                text="Cross-reference with Satellite Imagery before concluding",
                order=2,
                sets_state={
                    "signals_analyzed": True,
                },
            )
        )

        # --- FROM: humint → synthesis or other branches ---

        self.choices.append(
            self.create_choice(
                from_node_name="humint",
                to_node_name="synthesis",
                text="Proceed to synthesis — I've seen enough to form an assessment",
                order=0,
                sets_state={
                    "humint_analyzed": True,
                    "disciplines_completed": 1,
                },
            )
        )

        self.choices.append(
            self.create_choice(
                from_node_name="humint",
                to_node_name="sigint",
                text="Cross-reference with Signals Intelligence before concluding",
                order=1,
                sets_state={
                    "humint_analyzed": True,
                },
            )
        )

        self.choices.append(
            self.create_choice(
                from_node_name="humint",
                to_node_name="satint",
                text="Cross-reference with Satellite Imagery before concluding",
                order=2,
                sets_state={
                    "humint_analyzed": True,
                },
            )
        )

        # --- FROM: satint → synthesis or other branches ---

        self.choices.append(
            self.create_choice(
                from_node_name="satint",
                to_node_name="synthesis",
                text="Proceed to synthesis — I've seen enough to form an assessment",
                order=0,
                sets_state={
                    "satellite_analyzed": True,
                    "disciplines_completed": 1,
                },
            )
        )

        self.choices.append(
            self.create_choice(
                from_node_name="satint",
                to_node_name="sigint",
                text="Cross-reference with Signals Intelligence before concluding",
                order=1,
                sets_state={
                    "satellite_analyzed": True,
                },
            )
        )

        self.choices.append(
            self.create_choice(
                from_node_name="satint",
                to_node_name="humint",
                text="Cross-reference with Human Intelligence before concluding",
                order=2,
                sets_state={
                    "satellite_analyzed": True,
                },
            )
        )

        # --- FROM: synthesis → three endings ---

        self.choices.append(
            self.create_choice(
                from_node_name="synthesis",
                to_node_name="ending_correct",
                text="Assess as HIGH — imminent limited military operation",
                order=0,
                sets_state={
                    "threat_assessment": "high",
                    "correct_assessment": True,
                    "identified_primary_threat": True,
                },
            )
        )
        self.debug("Created choice: synthesis → ending_correct (HIGH)")

        self.choices.append(
            self.create_choice(
                from_node_name="synthesis",
                to_node_name="ending_missed",
                text="Assess as LOW — likely a routine exercise, not a real threat",
                order=1,
                sets_state={
                    "threat_assessment": "low",
                    "correct_assessment": False,
                    "false_positive_count": 0,
                },
            )
        )
        self.debug("Created choice: synthesis → ending_missed (LOW)")

        self.choices.append(
            self.create_choice(
                from_node_name="synthesis",
                to_node_name="ending_false_alarm",
                text=(
                    "Assess as CRITICAL — possible deception operation "
                    "masking large-scale attack"
                ),
                order=2,
                sets_state={
                    "threat_assessment": "critical",
                    "correct_assessment": False,
                    "weighted_mirror_intel": True,
                    "false_positive_count": 1,
                },
            )
        )
        self.debug("Created choice: synthesis → ending_false_alarm (CRITICAL)")

        test_results["choice_ids"] = [c["id"] for c in self.choices]
        self.log(f"  Created {len(self.choices)} choices")

        # =================================================================
        # STEP 5: VALIDATE
        # =================================================================
        self.log("\n✅ Validating state schema...")

        validation = self.validate_state_schema()
        if validation.get("is_valid"):
            self.log("  Schema is VALID — all variables defined!")
        else:
            self.log("  Schema has issues:")
            for error in validation.get("errors", []):
                self.log(
                    f"    - {error.get('variable_key')} in {error.get('used_in')}"
                )

        return validation.get("is_valid", False)


def main():
    parser = argparse.ArgumentParser(
        description="Create the War Room HTML format test story"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    test_results["start_time"] = datetime.now().isoformat()

    print("\n" + "=" * 70)
    print("  FORMAT TEST H-2: THE WAR ROOM")
    print("  HTML Data & Layout — Complex Tables, SVG, Data Attributes")
    print("=" * 70)

    try:
        session = get_authenticated_session()
        print("\n✓ Authenticated successfully")

        builder = WarRoomStoryBuilder(session, verbose=args.verbose)
        is_valid = builder.build_story()

        print("\n" + "=" * 70)
        print("  STORY CREATION COMPLETE")
        print("=" * 70)
        print(f"\n  Story ID: {builder.story_id}")
        print(f"  Nodes created: {len(builder.nodes)}")
        print(f"  Choices created: {len(builder.choices)}")
        print(f"  State variables: {len(builder.state_vars)}")
        print(f"  Schema valid: {'Yes' if is_valid else 'No'}")

        print("\n  Node Structure:")
        print("  ┌─ briefing (START) [HTML: complex table, data-attrs, entity encoding]")
        print("  │   ├─→ sigint [HTML: SVG chart, rowspan table, encryption analysis]")
        print("  │   ├─→ humint [HTML: nested div org-chart, blockquotes w/ citation]")
        print("  │   └─→ satint [HTML: SVG map, change-detection table, data-attrs]")
        print("  │         (each branch can cross-link to the others)")
        print("  │")
        print("  └─→ synthesis [HTML: indicator matrix, colspan/rowspan, tfoot]")
        print("        ├─→ ending_correct (HIGH) ✓  [HTML: definition lists]")
        print("        ├─→ ending_missed (LOW) ✗    [HTML: post-mortem table]")
        print("        └─→ ending_false_alarm (CRITICAL) ✗ [HTML: definition lists]")

        print(f"\n  HTML Features Exercised:")
        print(f"    ✓ Tables: thead/tbody/tfoot, colspan, rowspan")
        print(f"    ✓ CSS classes: briefing-document, row-critical, org-chart, etc.")
        print(f"    ✓ Data attributes: data-classification, data-priority, data-source, etc.")
        print(f"    ✓ Nested divs: org chart with 3 levels, observation cards")
        print(f"    ✓ Entity encoding: &amp; &mdash; &bull; &ldquo; &#9888; &#9679; etc.")
        print(f"    ✓ Inline SVG: frequency chart (polyline, annotations) + facility map")
        print(f"    ✓ Semantic elements: article, section, header, footer, blockquote")
        print(f"    ✓ Definition lists: dl/dt/dd in after-action notes")
        print(f"    ✓ Inline styles: color, font-weight, flex layout")
        print(f"    ✓ Long-form content: briefing node ~4000+ characters")

        print(f"\n  Play the story at:")
        print(f"  http://localhost:5173/stories/{builder.story_id}/play")

        test_results["success"] = is_valid
        test_results["end_time"] = datetime.now().isoformat()

        with open(RESULTS_FILE, "w") as f:
            json.dump(test_results, f, indent=2)
        print(f"\n  Results saved to: {RESULTS_FILE}")

        print("=" * 70 + "\n")
        return 0 if is_valid else 1

    except AuthenticationError as e:
        print(f"\n❌ Authentication failed: {e}")
        test_results["errors"].append(str(e))
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        test_results["errors"].append(str(e))
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
