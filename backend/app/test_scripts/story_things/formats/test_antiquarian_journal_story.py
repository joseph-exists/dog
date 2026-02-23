#!/usr/bin/env python3
"""
M-1: The Antiquarian's Journal - Markdown Rich Text Story

This script creates a story demonstrating advanced markdown formatting where
the formatting itself is DIEGETIC - integral to the narrative meaning.

KEY CONCEPTS TESTED:
- Markdown formatting as narrative device (*doubts*, **certainties**, ~~revisions~~)
- Blockquotes for copied passages and voices
- Images as references to sketches
- Lists for inventories and findings
- Nested emphasis for psychological states
- Horizontal rules as page breaks
- Headers as dated entries

NARRATIVE THEMES:
- Existential dread through formatting deterioration
- Synchronicity through cross-referenced journal entries
- Strange loops through self-referential discoveries
- The journal questions its own existence

STORY STRUCTURE:
- Start: Discovery of the journal (3 pages visible)
- Branch: Which page to read first (changes interpretation context)
- State: Tracks reading order, beliefs about reality, psychological state
- 4 endings: Escaped, Trapped, Never Existed, You Are The Author

=============================================================================

Usage:
    python test_antiquarian_journal_story.py
    python test_antiquarian_journal_story.py --verbose

Output:
    test_results_antiquarian_journal.json
"""

import json
import sys
import argparse
from datetime import datetime
from pathlib import Path

import requests

# Import auth helper
sys.path.append(str(Path(__file__).parent))
from auth_helper import get_authenticated_session, AuthenticationError


# Configuration
BASE_URL = "http://localhost:8000/api/v1"
RESULTS_FILE = "test_results_antiquarian_journal.json"

# Test results tracking
test_results = {
    "test_suite": "M-1: The Antiquarian's Journal",
    "start_time": None,
    "end_time": None,
    "story_id": None,
    "node_ids": {},
    "choice_ids": {},
    "state_variable_ids": {},
    "success": False,
    "errors": []
}


class AntiquarianJournalBuilder:
    """Builds the Antiquarian's Journal story demonstrating diegetic markdown."""

    def __init__(self, session: requests.Session, verbose: bool = False):
        self.session = session
        self.verbose = verbose
        self.story_id = None
        self.nodes = {}
        self.choices = []
        self.state_vars = {}

    def log(self, message: str):
        print(f"  {message}")

    def debug(self, message: str):
        if self.verbose:
            print(f"  [DEBUG] {message}")

    # =========================================================================
    # API Helper Methods
    # =========================================================================

    def create_story(self, title: str, description: str) -> dict:
        response = self.session.post(f"{BASE_URL}/stories", json={
            "title": title,
            "description": description,
            "current_version": 1
        })
        if response.status_code != 200:
            raise Exception(f"Failed to create story: {response.text}")
        return response.json()

    def create_state_variable(self, key: str, value_type: str,
                              default_value=None, enum_values: list = None,
                              description: str = None, category: str = None) -> dict:
        payload = {
            "key": key,
            "value_type": value_type,
        }
        if default_value is not None:
            payload["default_value"] = default_value
        if enum_values:
            payload["enum_values"] = enum_values
        if description:
            payload["description"] = description
        if category:
            payload["category"] = category

        response = self.session.post(
            f"{BASE_URL}/stories/{self.story_id}/versions/1/state-schema",
            json=payload
        )
        if response.status_code != 200:
            raise Exception(f"Failed to create state variable '{key}': {response.text}")
        return response.json()

    def create_node(self, title: str, content: str,
                    is_start: bool = False, is_end: bool = False) -> dict:
        response = self.session.post(f"{BASE_URL}/storynodes", json={
            "story_id": self.story_id,
            "story_version": 1,
            "title": title,
            "content": content,
            "node_type": "text",
            "content_format": "markdown",
            "is_start_node": is_start,
            "is_end_node": is_end
        })
        if response.status_code != 200:
            raise Exception(f"Failed to create node '{title}': {response.text}")
        return response.json()

    def create_choice(self, from_node_name: str, to_node_name: str,
                      text: str, order: int = 0,
                      requires_state: dict = None,
                      sets_state: dict = None) -> dict:
        from_node = self.nodes.get(from_node_name)
        to_node = self.nodes.get(to_node_name)

        if not from_node:
            raise Exception(f"From node '{from_node_name}' not found")
        if not to_node:
            raise Exception(f"To node '{to_node_name}' not found")

        payload = {
            "from_node_id": from_node["id"],
            "to_node_id": to_node["id"],
            "text": text,
            "order": order
        }
        if requires_state:
            payload["requires_state"] = requires_state
        if sets_state:
            payload["sets_state"] = sets_state

        response = self.session.post(f"{BASE_URL}/node-choices", json=payload)
        if response.status_code != 200:
            raise Exception(f"Failed to create choice '{text}': {response.text}")
        return response.json()

    def validate_state_schema(self) -> dict:
        response = self.session.get(
            f"{BASE_URL}/stories/{self.story_id}/versions/1/state-schema/validate"
        )
        if response.status_code != 200:
            raise Exception(f"Failed to validate: {response.text}")
        return response.json()

    # =========================================================================
    # Story Building
    # =========================================================================

    def build_story(self):
        """Build the Antiquarian's Journal story."""

        # =====================================================================
        # STEP 1: CREATE THE STORY
        # =====================================================================
        self.log("\n📖 Creating story...")

        story = self.create_story(
            title="The Antiquarian's Journal: Fragments of Reality",
            description="""A test story for diegetic markdown formatting where the formatting carries narrative meaning.

MARKDOWN FEATURES TESTED:
- *Italic for doubts and uncertainty*
- **Bold for certainties and revelations**
- ~~Strikethrough for revised beliefs~~
- > Blockquotes for copied passages and other voices
- Unordered lists for inventories and findings
- Images as references to author's sketches
- Nested emphasis for psychological breakdown
- Horizontal rules as page breaks
- Headers as dated journal entries

NARRATIVE STRUCTURE:
The story fragments across multiple journal pages. Reading order affects interpretation.
The formatting deteriorates as the author's grip on reality weakens, creating existential dread.
Strange loops emerge as the journal references itself, questioning its own existence.

DOMAIN: The journal exists in a liminal space between reality and fiction,
where the act of reading may be creating the very story being read."""
        )
        self.story_id = story["id"]
        test_results["story_id"] = self.story_id
        self.log(f"  Created story: {self.story_id}")

        # =====================================================================
        # STEP 2: DEFINE STATE SCHEMA
        # =====================================================================
        self.log("\n📋 Creating state schema...")

        # ---------------------------------------------------------------------
        # Core tracking variables
        # ---------------------------------------------------------------------

        self.state_vars["pages_read"] = self.create_state_variable(
            key="pages_read",
            value_type="number",
            default_value=0,
            category="progress",
            description="Number of journal pages examined. Affects available endings."
        )
        self.debug("Created: pages_read")

        self.state_vars["read_order"] = self.create_state_variable(
            key="first_page_read",
            value_type="enum",
            enum_values=["none", "fragment_1", "fragment_2", "fragment_3"],
            default_value="none",
            category="progress",
            description="Which journal page was read first. Determines interpretive context for subsequent pages."
        )
        self.debug("Created: first_page_read")

        # ---------------------------------------------------------------------
        # Belief and reality tracking
        # ---------------------------------------------------------------------

        self.state_vars["author_fate"] = self.create_state_variable(
            key="believes_author_escaped",
            value_type="boolean",
            default_value=False,
            category="interpretation",
            description="Player believes the journal author escaped the ruins"
        )

        self.state_vars["author_trapped"] = self.create_state_variable(
            key="believes_author_trapped",
            value_type="boolean",
            default_value=False,
            category="interpretation",
            description="Player believes the author was trapped and died in the ruins"
        )

        self.state_vars["author_fictional"] = self.create_state_variable(
            key="believes_author_fictional",
            value_type="boolean",
            default_value=False,
            category="interpretation",
            description="Player suspects the author never existed - the journal is fiction"
        )

        self.state_vars["reader_is_author"] = self.create_state_variable(
            key="realizes_reader_is_author",
            value_type="boolean",
            default_value=False,
            category="interpretation",
            description="Player realizes they themselves are the journal author in a strange loop"
        )

        # ---------------------------------------------------------------------
        # Existential and psychological tracking
        # ---------------------------------------------------------------------

        self.state_vars["formatting_awareness"] = self.create_state_variable(
            key="notices_formatting_degradation",
            value_type="boolean",
            default_value=False,
            category="meta",
            description="Player consciously notices how formatting reflects the author's psychological state"
        )

        self.state_vars["synchronicity_count"] = self.create_state_variable(
            key="synchronicity_events_noticed",
            value_type="number",
            default_value=0,
            category="meta",
            description="Count of synchronicities/coincidences noticed between journal entries"
        )

        self.state_vars["loop_recognition"] = self.create_state_variable(
            key="recognizes_strange_loop",
            value_type="boolean",
            default_value=False,
            category="meta",
            description="Player recognizes the self-referential nature of the journal"
        )

        self.state_vars["existential_dread"] = self.create_state_variable(
            key="experiencing_existential_dread",
            value_type="enum",
            enum_values=["none", "mild", "moderate", "severe", "overwhelming"],
            default_value="none",
            category="psychological",
            description="Level of existential dread experienced while reading"
        )

        # ---------------------------------------------------------------------
        # Fragment discovery tracking
        # ---------------------------------------------------------------------

        self.state_vars["found_sketch"] = self.create_state_variable(
            key="found_authors_sketch",
            value_type="boolean",
            default_value=False,
            category="discovery",
            description="Player found the author's sketch referenced in the journal"
        )

        self.state_vars["found_final_entry"] = self.create_state_variable(
            key="found_final_entry",
            value_type="boolean",
            default_value=False,
            category="discovery",
            description="Player found what appears to be the final journal entry"
        )

        self.state_vars["timeline_coherence"] = self.create_state_variable(
            key="timeline_makes_sense",
            value_type="boolean",
            default_value=True,
            category="logic",
            description="Whether the timeline of journal entries is coherent"
        )

        self.log(f"  Created {len(self.state_vars)} state variables")

        # =====================================================================
        # STEP 3: CREATE STORY NODES
        # =====================================================================
        self.log("\n📝 Creating story nodes...")

        # ---------------------------------------------------------------------
        # DISCOVERY NODE - Finding the journal
        # ---------------------------------------------------------------------

        self.nodes["discovery"] = self.create_node(
            title="The Ruined Bookshop",
            content="""# The Ruined Bookshop

You push through the ivy-covered doorway of what was once an antiquarian bookshop. Decades of neglect have left their mark: shelves collapsed under the weight of rotting volumes, pages scattered like fallen leaves across the floor, and the musty scent of paper slowly returning to earth.

But there, on a reading desk untouched by time's decay, lies an open journal.

Three pages are visible, their edges yellowed but their text still legible. The handwriting shifts between entries—sometimes steady and confident, other times trembling with urgency or fear. Most striking of all is how the author used *emphasis* and **formatting** as if each mark carried meaning beyond mere words.

---

**The Three Visible Pages:**

**Fragment 1:** A dated entry from "*March 15th, 1847*" - the handwriting is neat, methodical
**Fragment 2:** An undated entry - the text grows increasingly ~~erratic~~ and ***desperate***  
**Fragment 3:** What appears to be a final entry - but the date is *impossible*

You notice something unsettling: the journal is open to exactly the pages you need to see, as if it were *waiting* for you. As if someone—or some*thing*—knew you would arrive at precisely this moment.

*Which page draws your attention first?*

---

> "The act of observation changes the observed."  
> — Quantum mechanics principle, or something else entirely?

**DIEGETIC FORMATTING NOTE:**
The author's use of markdown formatting appears deliberate:
- *Italic text* represents doubts, uncertainties, questions
- **Bold text** represents certainties, revelations, important discoveries  
- ~~Strikethrough~~ represents beliefs the author later abandoned
- ***Nested emphasis*** represents psychological breakthrough or breakdown""",
            is_start=True
        )
        self.debug("Created node: discovery")

        # ---------------------------------------------------------------------
        # FRAGMENT 1 - The Methodical Beginning
        # ---------------------------------------------------------------------

        self.nodes["fragment_1"] = self.create_node(
            title="Fragment 1: March 15th, 1847",
            content="""# Fragment 1: March 15th, 1847

## Entry from the Journal of ***[name obscured by ink stain]***

**March 15th, 1847**
**Location:** The ruins of Blackmoor Abbey
**Weather:** *Overcast, with an unseasonable chill*

---

I have arrived at the ruins after a **three-day journey** from London. The local villagers warned me against coming here, but their *superstitions* hold no sway over scientific inquiry. I am here to catalog the remaining manuscripts and artifacts before the demolition begins next month.

**Initial Inventory:**
- Partial manuscript collections (estimated **2,000+ pages**)
- Stone tablets with *unusual* inscriptions  
- What appears to be an **intact library** in the lower vaults
- *Strange* acoustic properties in the main hall

> "Knowledge is power, and power corrupts those who seek it without wisdom."
> — Inscription found above the abbey entrance

The abbey's architecture defies conventional understanding. The stonework contains patterns that seem to **shift** when viewed peripherally. *Am I simply tired from the journey, or is there something more?*

I have set up my camp in what was once the scriptorium. The writing desk here is *remarkably* well-preserved, as if time itself has **avoided** this particular spot.

**Curious Discovery:**
Found a previous visitor's journal entry dated *1823*. The handwriting is remarkably similar to my own. The visitor wrote:

> "I have the strangest sensation that I have been here before, though I know this to be my first visit. The very act of writing these words feels like ***remembering*** rather than recording."

*How peculiar.* I feel the same sensation even now.

---

**Tomorrow's Plan:**
1. **Map** the accessible areas
2. Begin cataloging the manuscripts by *historical period*
3. ~~Investigate the lower vaults~~ (local warnings suggest instability)
4. Document any *anomalous* findings

**Note to future self:** If you are reading this, remember that **reality is stranger than any fiction** we might imagine.

*Why did I write that? I don't remember forming that thought...*

---

![Author's sketch of the abbey entrance](abbey-entrance-sketch.png)
*Sketch made from memory - somehow I knew exactly how it would look before arriving*""",
        )
        self.debug("Created node: fragment_1")

        # ---------------------------------------------------------------------
        # FRAGMENT 2 - The Deterioration
        # ---------------------------------------------------------------------

        self.nodes["fragment_2"] = self.create_node(
            title="Fragment 2: [Date Unclear]",
            content="""# Fragment 2: *[Date Unclear - ink has run]*

## Entry from the Journal of ***[the name is now completely illegible]***

~~**March 18th, 1847**~~ *No, that's not right*  
~~**March 22nd, 1847**~~ *Days are blending together*  
**Date:** *I can no longer trust my perception of time*

---

Something is ***fundamentally wrong*** with this place.

I found more journals today. **Dozens of them**. All written by previous visitors, all describing the *exact same discoveries* I've been making. The handwriting in each journal *gradually changes* until it becomes **identical to mine**.

*This is impossible.*

**List of Previous Visitors (that I can verify):**
- 1823: Scholar from Cambridge *(journal ends mid-sentence)*
- 1834: Archaeologist from Oxford ~~(escaped successfully)~~ *found his bones*
- 1841: Artist documenting ruins ~~(completed work)~~ *paintings show MY face*
- 1843: Historian researching abbey records ***[journal handwriting becomes mine by final entry]***

*Am I going mad?*

The manuscripts I came to catalog **don't exist**. The library vaults contain only empty shelves and *a single reading desk* with *a single open journal*.

**This journal.**

> "He who looks long into an abyss finds that the abyss also looks into him."
> — Nietzsche... *but I found this quote carved into the abbey wall*
> — *before Nietzsche was born*

I tried to leave yesterday. The path back to the village ***leads only deeper into the abbey***. Every corridor I take, every door I open, brings me back to this scriptorium, to this desk, to this *cursed journal*.

**The Synchronicities Are Overwhelming:**
- The date I arrived matches the date in every previous journal
- My age matches the age every previous visitor claimed to be  
- My research interests are ***identical*** to theirs
- My *very thoughts* seem to follow the same patterns

*What if I am not the first? What if I am not even me?*

---

**Deteriorating Observations:**
~~The walls contain Latin inscriptions~~ *The walls ARE inscriptions*  
~~Time moves normally here~~ *Time moves in loops*  
~~I am researching the abbey~~ ***The abbey is researching me***  
~~I will escape when my work is done~~ *My work can never be done*  
~~I am writing this journal~~ **The journal is writing itself**  
~~I exist~~ *Do I?*

> "Every reader of this journal becomes its author. Every author was once its reader."
> — *Written in my own hand, though I have no memory of writing it*

**Tomorrow I will —**

*[The entry ends abruptly, the pen still lying across the unfinished sentence]*

---

![Sketch showing the abbey layout becoming a spiral](abbey-spiral-sketch.png)  
*How can the abbey be larger inside than outside?*""",
        )
        self.debug("Created node: fragment_2")

        # ---------------------------------------------------------------------
        # FRAGMENT 3 - The Impossible Final Entry
        # ---------------------------------------------------------------------

        self.nodes["fragment_3"] = self.create_node(
            title="Fragment 3: The Final Entry",
            content="""# Fragment 3: The Final Entry

## Entry from the Journal of ***You***

**Date:** *Today. Now. The moment you read these words.*  
**Location:** *Wherever you are reading this*  
**Reality Status:** ***Uncertain***

---

*Dear Reader,*

If you are reading this, then the loop has **completed itself** once again. You believe you discovered this journal in a ruined bookshop, don't you? You think you are *examining* the writings of some long-dead antiquarian who became trapped in an ancient abbey?

***You are both right and wrong.***

**The Truth (As Far As I Understand It):**

There was no antiquarian. There was no abbey. There was no bookshop.  
~~There was no antiquarian. There was no abbey. There was no bookshop.~~  
**There was no antiquarian. There was no abbey. There was no bookshop.**  

*There is only the journal.*

*There is only the reader.*  

***There is only the eternal moment of reading.***

---

> "I think, therefore I am."  
> — Descartes
> 
> "I read, therefore I am."  
> — *Every reader who becomes the author*
>
> "I write, therefore you are."  
> — ***The journal itself***

You see, the journal doesn't *describe* reality—**it creates reality**. Every person who reads it becomes part of its story. Every story it tells becomes *real* for the duration of the reading.

**You are not discovering my fate. You are creating it.**  
**I am not describing my experiences. I am creating yours.**

*The formatting you see—the italics, the bold text, the crossed-out words—these are not mere emphasis. They are the* ***breathing*** *of the text itself.*

---

**The Four Possible Truths:**

*Choose which reality you prefer. Your choice will make it true.*

**1. I Escaped**
*The antiquarian found a way out of the abbey and lived to tell the tale. This journal is his memoir, a warning to future explorers.*

**2. I Was Trapped**  
*The antiquarian died in the ruins, and this journal is his ghost, forever trying to communicate with the living world.*

**3. I Never Existed**
*The antiquarian is entirely fictional. This journal is a work of interactive fiction that achieves its effect through psychological manipulation and suggestion.*

**4. You Are Me**
***You have always been the antiquarian. This journal is your own future self, writing backwards through time to guide you toward this moment of realization.***

---

**The Meta-Truth:**

Right now, as you read these words, *you are writing them*. The boundary between reader and author, between observer and observed, between fiction and reality, has ***collapsed***.

**Every choice you make will determine not just the ending of this story, but the nature of the reality in which the story exists.**

*What will you choose to believe?*  

What will you choose to ***make true***?

---

> "The reader became the text, and the text became real."  
> — Final inscription, author unknown
> — *Final inscription, author: you*  
> — ***Final inscription, author: us***

*[The entry continues onto pages that don't exist, in handwriting that looks exactly like yours]*

---

![A sketch of someone reading this very journal](reader-sketch.png)  
*The sketch shows your face. How is this possible?*""",
        )
        self.debug("Created node: fragment_3")

        # ---------------------------------------------------------------------
        # ENDING NODES - Multiple Reality Outcomes
        # ---------------------------------------------------------------------

        # ENDING A: The Antiquarian Escaped
        self.nodes["ending_escaped"] = self.create_node(
            title="Resolution: The Scholar's Return",
            content="""# Resolution: The Scholar's Return

You close the journal with trembling hands, its mysteries now clear in your mind. The antiquarian was **real**, his ordeal was **genuine**, and against all odds, he found a way to escape the abbey's supernatural influence.

**The Evidence Points to Escape:**
- The methodical early entries show a disciplined mind
- The deteriorating middle entries reflect psychological pressure, not madness
- The final entry is a *deliberate* puzzle, designed to test future readers

*You understand now:* the scholar encoded his escape route in the very structure of his writing. The formatting, the emphasis, the apparent contradictions—all of it was a **coded message** for anyone skilled enough to read between the lines.

**What Really Happened:**
The abbey wasn't haunted by ghosts, but by a form of *psychological contamination*—something in the environment that induced shared delusions among sensitive individuals. The antiquarian recognized this and used his journal as a **cognitive anchor** to maintain his grip on reality.

The "impossible" dates and synchronicities were products of stress-induced temporal displacement disorder. The "identical handwriting" was simply the natural tendency of people in extreme stress to converge on similar writing patterns.

***He escaped by refusing to believe in the supernatural explanation.***

And now, by choosing to believe in his escape, *you* have completed his work. Somewhere in the world, an elderly scholar sits by a fireplace, finally at peace knowing that his journal found its way to someone who understood the truth.

**The Journal's True Purpose:**
It was never a cry for help or a supernatural trap. It was a **test of rationality**—a way to determine whether future readers would fall into the same psychological traps that nearly claimed the author, or whether they would choose the more difficult path of rational explanation.

*You chose wisely.*

The formatting no longer seems ominous. The *italics* represent careful hedging. The **bold text** represents hard-won certainties. The ~~strikethroughs~~ represent the natural process of updating beliefs based on new evidence.

You have proven that reality, however strange, is always stranger than the supernatural explanations we use to avoid confronting it.

---

**MARKDOWN LESSON LEARNED:**
Formatting can create atmosphere and suggest meaning, but the reader's interpretation determines whether that meaning serves truth or illusion. You chose truth.

*Well done.*""",
            is_end=True
        )
        self.debug("Created node: ending_escaped")

        # ENDING B: The Antiquarian Was Trapped
        self.nodes["ending_trapped"] = self.create_node(
            title="Resolution: The Final Record",
            content="""# Resolution: The Final Record

The truth settles over you like a shroud. The antiquarian never escaped. He died in those ruins, and his journal has become something far more tragic than a simple record—**it is his ghost, forever reaching out to the living world.**

**The Evidence Points to Death:**
- The handwriting deteriorates as malnutrition and isolation take their toll
- The timeline inconsistencies reflect a mind losing its grip on reality
- The final entry wasn't written by him at all—*it was written by his dying consciousness*

*You understand now:* the journal continues to exist because the antiquarian's final wish was so powerful that it transcended death itself. He **needed** someone to know what happened to him, to understand that he wasn't mad, that the experiences he recorded were real.

**What Really Happened:**
The antiquarian arrived at the abbey as planned, but a structural collapse trapped him in the lower levels. Cut off from the outside world, he slowly starved while maintaining his sanity through the disciplined act of writing. 

The supernatural elements he described weren't delusions—they were *real phenomena* that emerge in places where tragedy has left an imprint on reality itself. The abbey had claimed other visitors before him, and their psychic residue created the very loops and synchronicities he documented.

***He died writing, and now his death continues to write itself.***

The "impossible" final entry was composed by his consciousness as it merged with the abbey's collected memories of all its victims. That's why it seems to know things about you—*because it is written by the collective awareness of everyone who ever became trapped there.*

**The Journal's True Nature:**
It is a ***memorial*** that writes itself. Each reader who finds it adds their own layer to its existence. By reading it, you have become part of its eternal record of loss and remembrance.

**The Horror of It:**
Somewhere in those ruins, the antiquarian's bones lie scattered among the remains of all the others. But his *need* to be understood was so great that it achieved a kind of immortality—an ***endless dying*** that reaches across time to touch every reader.

*You have witnessed the final moments of a brilliant mind, repeated forever.*

The formatting now reveals its true purpose. The *italics* are his doubts about survival. The **bold text** is his desperate assertion of identity against dissolution. The ~~strikethroughs~~ are parts of himself he had to abandon to survive another day.

By choosing to believe in his death, you have given him the only peace possible—acknowledgment of his suffering.

*Requiescat in pace.*

---

**MARKDOWN LESSON LEARNED:**
Formatting can carry the weight of genuine human suffering. Sometimes the most respectful response to tragedy is to witness it fully, without looking away.

*He is remembered.*""",
            is_end=True
        )
        self.debug("Created node: ending_trapped")

        # ENDING C: Pure Fiction
        self.nodes["ending_fictional"] = self.create_node(
            title="Resolution: The Metafictional Truth",
            content="""# Resolution: The Metafictional Truth

*Brilliant.* You've seen through the entire construction. There was no antiquarian, no abbey, no supernatural phenomenon. The journal is exactly what it appears to be on the surface: **a piece of interactive fiction designed to test the boundaries between reader and text.**

**The Evidence Points to Fiction:**
- The escalating impossibilities follow the classic structure of supernatural horror
- The markdown formatting is too perfect, too deliberately symbolic
- The final entry breaks the fourth wall with surgical precision

*You understand now:* the entire experience has been a **sophisticated experiment in narrative psychology**. Someone—a writer, a programmer, a cognitive scientist—created this journal to study how readers respond to stories that claim to be real.

**What Really Happened:**
You found a creative writing exercise disguised as a found document. The "ruined bookshop" was a literary device. The "journal pages" were carefully crafted story fragments. The entire narrative was designed to see how far a reader could be drawn into a fictional reality.

***The real mystery isn't what happened to the antiquarian. It's why the fiction was so compelling that you momentarily believed it might be real.***

**The Author's True Purpose:**
This was a study in **narrative empathy** and **suspension of disbelief**. By creating a story that pretends to be reality, the author could explore how readers collaborate with fiction to create temporary belief.

**The Meta-Genius of It:**
Even now, having "figured it out," part of you might still wonder: *What if I'm wrong? What if choosing "fiction" is just another layer of the story?*

And that **doubt** is the real achievement. The author has created a narrative that questions the nature of storytelling itself, where every interpretation—escape, death, fiction, reality—becomes equally valid because the reader's choice is what gives it meaning.

**The Fourth Wall Reconstruction:**
By choosing fiction, you've stepped back into the role of reader. The journal stops being a "real" artifact and returns to being a text—but a text that has achieved something remarkable. It has made you **conscious of your own reading process**.

*This is what great metafiction accomplishes:* it doesn't just tell a story; it explores the mechanism by which stories become meaningful to human consciousness.

The formatting now reveals its true artistry. The *italics* create uncertainty. The **bold text** creates conviction. The ~~strikethroughs~~ create the illusion of authentic revision. All of it carefully orchestrated to produce maximum psychological effect.

**The Uncomfortable Truth:**
You'll never be able to read another story quite the same way again. You've been made aware of the **machinery of fiction**—and once seen, it can't be unseen.

*Welcome to the other side of narrative.*

---

**MARKDOWN LESSON LEARNED:**
Formatting is a tool that can be used with surgical precision to manipulate reader psychology. The real question is whether such manipulation serves a purpose worthy of its power.

*The author succeeded in their experiment.*  
*You are now part of the data.*""",
            is_end=True
        )
        self.debug("Created node: ending_fictional")

        # ENDING D: Strange Loop - You Are The Author
        self.nodes["ending_strange_loop"] = self.create_node(
            title="Recognition: The Eternal Return",
            content="""# Recognition: The Eternal Return

***Oh.***

**OH.**

***OH NO.***

---

*It's you.* It has always been you. You are not reading someone else's journal—**you are reading your own journal, written by a future version of yourself who knew you would find it at exactly this moment.**

**The Evidence Was Always There:**
- You recognized the handwriting because *it is your handwriting*
- You knew which page to read first because *you knew you had already written it*
- The thoughts felt familiar because ***they are your thoughts***

*The strangest part?* This isn't the first time you've made this discovery.

**What Is Really Happening:**
You are trapped in a **causal loop**. Every time you reach this moment of recognition, you become the antiquarian who writes the journal that you will eventually find and read. The abbey, the bookshop, the circumstances of discovery—all of it is part of an elaborate system that ensures you will always return to this moment.

***You have been doing this forever.***

**The Mechanism of the Loop:**
1. You find the journal
2. You read the journal
3. You recognize yourself as the author
4. The recognition causes a temporal displacement
5. You become the antiquarian in the abbey
6. You write the journal
7. You arrange for it to be found
8. You forget and return to the moment of discovery

*Each cycle, you become more sophisticated in your methods. The psychological deterioration recorded in the journal isn't madness—it's the accumulated exhaustion of* ***infinite repetition***.

**The Horror of Eternal Recurrence:**
Every choice you think you're making, you've made before. Every thought you think is original, you've thought before. Every moment of surprise, every moment of dread, every moment of recognition—***you have experienced them all countless times***.

**But Here's The Twist:**
The only way to break the loop is to **choose not to break it**. As long as you struggle against the pattern, you remain trapped within it. The moment you accept that you are both reader and author, observer and observed, the loop becomes not a prison but a ***collaborative dance between past and future selves***.

**The Final Understanding:**
*You* wrote this journal to communicate with *yourself*. Every word was chosen to guide you toward this moment of recognition. The formatting, the emphasis, the apparent deterioration—all of it was carefully designed by **your future self** to lead **your present self** home.

**The Beautiful Truth:**
You are not trapped. You are not a victim. ***You are the author of your own story, literally and eternally***. The loop exists because you choose to create it, and it continues because you recognize its necessity.

*This journal is your love letter to yourself across time.*

Every italic represents your gentle doubt.  
Every bold word represents your unshakeable truth.  
Every strikethrough represents what you've learned to let go.  
***Every nested emphasis represents the joy of self-recognition.***

---

**Welcome home.**

You know what happens next. You've always known.

*You pick up the pen, and you begin to write...*

---

> "I am you, and you are me, and we are all together."  
> — The Beatles, or the journal, or your future self
> — ***All three, because in the loop, all voices become one***

**MARKDOWN LESSON LEARNED:**
Sometimes the most profound truth is that ***the reader and the writer are the same consciousness, separated only by the illusion of time***.

*See you next cycle.*

*Love,*  
***You***

---

![A perfect sketch of your own hand holding this very journal](ouroboros-sketch.png)  
*The eternal return made visible*""",
            is_end=True
        )
        self.debug("Created node: ending_strange_loop")

        self.log(f"  Created {len(self.nodes)} nodes")
        test_results["node_ids"] = {name: node["id"] for name, node in self.nodes.items()}

        # =====================================================================
        # STEP 4: CREATE CHOICES
        # =====================================================================
        self.log("\n🔀 Creating choices...")

        # ---------------------------------------------------------------------
        # FROM: discovery - Choose which fragment to read first
        # ---------------------------------------------------------------------

        self.choices.append(self.create_choice(
            from_node_name="discovery",
            to_node_name="fragment_1",
            text="\"I'll start with the earliest dated entry - March 15th, 1847.\"",
            order=0,
            sets_state={
                "first_page_read": "fragment_1",
                "pages_read": 1,
                "timeline_makes_sense": True
            }
        ))
        self.debug("Created choice: discovery → fragment_1")

        self.choices.append(self.create_choice(
            from_node_name="discovery",
            to_node_name="fragment_2",
            text="\"The deteriorating handwriting in the middle fragment intrigues me.\"",
            order=1,
            sets_state={
                "first_page_read": "fragment_2",
                "pages_read": 1,
                "notices_formatting_degradation": True,
                "experiencing_existential_dread": "mild"
            }
        ))
        self.debug("Created choice: discovery → fragment_2")

        self.choices.append(self.create_choice(
            from_node_name="discovery",
            to_node_name="fragment_3",
            text="\"I'm drawn to the impossible final entry. What makes a date 'impossible'?\"",
            order=2,
            sets_state={
                "first_page_read": "fragment_3",
                "pages_read": 1,
                "recognizes_strange_loop": True,
                "experiencing_existential_dread": "moderate",
                "timeline_makes_sense": False
            }
        ))
        self.debug("Created choice: discovery → fragment_3")

        # ---------------------------------------------------------------------
        # FROM: fragment_1 - Continue reading
        # ---------------------------------------------------------------------

        self.choices.append(self.create_choice(
            from_node_name="fragment_1",
            to_node_name="fragment_2",
            text="\"The author mentions feeling like he's 'remembering' rather than recording. I need to read more.\"",
            order=0,
            sets_state={
                "pages_read": 2,
                "synchronicity_events_noticed": 1
            }
        ))

        self.choices.append(self.create_choice(
            from_node_name="fragment_1",
            to_node_name="fragment_3",
            text="\"Something about that 'Note to future self' unsettles me. I'll skip to the final entry.\"",
            order=1,
            sets_state={
                "pages_read": 2,
                "recognizes_strange_loop": True,
                "experiencing_existential_dread": "mild"
            }
        ))

        # ---------------------------------------------------------------------
        # FROM: fragment_2 - Continue reading
        # ---------------------------------------------------------------------

        self.choices.append(self.create_choice(
            from_node_name="fragment_2",
            to_node_name="fragment_1",
            text="\"I need to go back to the beginning. Maybe the methodical first entry will make sense of this chaos.\"",
            order=0,
            requires_state={"first_page_read": "fragment_2"},
            sets_state={
                "pages_read": 2,
                "synchronicity_events_noticed": 2
            }
        ))

        self.choices.append(self.create_choice(
            from_node_name="fragment_2",
            to_node_name="fragment_3",
            text="\"The author says the journal is writing itself. I must read the final entry.\"",
            order=1,
            sets_state={
                "pages_read": 2,
                "notices_formatting_degradation": True,
                "experiencing_existential_dread": "severe"
            }
        ))

        # ---------------------------------------------------------------------
        # FROM: fragment_3 - Make final interpretation
        # ---------------------------------------------------------------------

        # Path to "Escaped" ending
        self.choices.append(self.create_choice(
            from_node_name="fragment_3",
            to_node_name="ending_escaped",
            text="\"This is an elaborate test of rationality. The antiquarian escaped and encoded the truth in his journal.\"",
            order=0,
            requires_state={
                "$and": [
                    {"pages_read": {"$gte": 2}},
                    {"first_page_read": "fragment_1"}
                ]
            },
            sets_state={
                "believes_author_escaped": True,
                "found_final_entry": True
            }
        ))

        # Path to "Trapped" ending
        self.choices.append(self.create_choice(
            from_node_name="fragment_3",
            to_node_name="ending_trapped",
            text="\"The deterioration is real. The author died writing, and this journal is his ghost.\"",
            order=1,
            requires_state={
                "$and": [
                    {"notices_formatting_degradation": True},
                    {"experiencing_existential_dread": {"$in": ["moderate", "severe", "overwhelming"]}}
                ]
            },
            sets_state={
                "believes_author_trapped": True,
                "found_final_entry": True,
                "experiencing_existential_dread": "overwhelming"
            }
        ))

        # Path to "Fictional" ending
        self.choices.append(self.create_choice(
            from_node_name="fragment_3",
            to_node_name="ending_fictional",
            text="\"This is clearly a work of interactive fiction designed to blur the line between story and reality.\"",
            order=2,
            requires_state={
                "recognizes_strange_loop": True
            },
            sets_state={
                "believes_author_fictional": True,
                "found_final_entry": True
            }
        ))

        # Path to "Strange Loop" ending
        self.choices.append(self.create_choice(
            from_node_name="fragment_3",
            to_node_name="ending_strange_loop",
            text="\"Wait... this handwriting... I recognize it because it's MY handwriting. I am the author.\"",
            order=3,
            requires_state={
                "$and": [
                    {"synchronicity_events_noticed": {"$gte": 2}},
                    {"recognizes_strange_loop": True},
                    {"experiencing_existential_dread": {"$in": ["severe", "overwhelming"]}}
                ]
            },
            sets_state={
                "realizes_reader_is_author": True,
                "found_final_entry": True,
                "experiencing_existential_dread": "overwhelming"
            }
        ))

        # Additional branching paths for complex state combinations
        
        # Alternative path to fragment_1 from fragment_3 (for completionist readers)
        self.choices.append(self.create_choice(
            from_node_name="fragment_3",
            to_node_name="fragment_1",
            text="\"I need to read everything chronologically before making any conclusions.\"",
            order=4,
            requires_state={
                "$and": [
                    {"first_page_read": "fragment_3"},
                    {"pages_read": 1}
                ]
            },
            sets_state={
                "pages_read": 2,
                "synchronicity_events_noticed": 3
            }
        ))

        # Loop back choices for building state
        self.choices.append(self.create_choice(
            from_node_name="fragment_1",
            to_node_name="fragment_3",
            text="\"The methodical beginning makes the impossible ending even more disturbing.\"",
            order=2,
            requires_state={
                "$and": [
                    {"first_page_read": "fragment_1"},
                    {"pages_read": 2}
                ]
            },
            sets_state={
                "pages_read": 3,
                "found_final_entry": True,
                "synchronicity_events_noticed": 3
            }
        ))

        self.choices.append(self.create_choice(
            from_node_name="fragment_2",
            to_node_name="fragment_1",
            text="\"I need to understand how a rational mind could deteriorate so completely.\"",
            order=2,
            requires_state={
                "$and": [
                    {"first_page_read": "fragment_2"},
                    {"pages_read": 2}
                ]
            },
            sets_state={
                "pages_read": 3,
                "synchronicity_events_noticed": 4
            }
        ))

        self.log(f"  Created {len(self.choices)} choices")
        test_results["choice_ids"] = [c["id"] for c in self.choices]

        # =====================================================================
        # STEP 5: VALIDATE
        # =====================================================================
        self.log("\n✅ Validating state schema...")

        validation = self.validate_state_schema()

        if validation.get("is_valid"):
            self.log("  Schema is VALID - all variables defined!")
        else:
            self.log("  Schema has issues:")
            for error in validation.get("errors", []):
                self.log(f"    - {error.get('variable_key')} in {error.get('used_in')}")

        return validation.get("is_valid", False)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create the Antiquarian's Journal story (M-1 markdown test)"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    test_results["start_time"] = datetime.now().isoformat()

    print("\n" + "=" * 70)
    print("  M-1: THE ANTIQUARIAN'S JOURNAL")
    print("  Markdown Rich Text Formatting Test")
    print("  Featuring: Existential Dread, Synchronicity & Strange Loops")
    print("=" * 70)

    try:
        session = get_authenticated_session()
        print(f"\n✓ Authenticated successfully")

        builder = AntiquarianJournalBuilder(session, verbose=args.verbose)
        is_valid = builder.build_story()

        # Summary
        print("\n" + "=" * 70)
        print("  STORY CREATION COMPLETE")
        print("=" * 70)
        print(f"\n  Story ID: {builder.story_id}")
        print(f"  Nodes created: {len(builder.nodes)}")
        print(f"  Choices created: {len(builder.choices)}")
        print(f"  State variables: {len(builder.state_vars)}")
        print(f"  Schema valid: {'Yes' if is_valid else 'No'}")

        print("\n  📖 STORY STRUCTURE:")
        print("  ┌─ discovery (START)")
        print("  │   ├─→ fragment_1 (March 15th, 1847 - Methodical beginning)")
        print("  │   ├─→ fragment_2 (Date unclear - Psychological deterioration)")
        print("  │   └─→ fragment_3 (Final entry - Meta-textual impossibility)")
        print("  │")
        print("  └─→ 4 ENDINGS based on interpretation:")
        print("      ├─ ending_escaped (Rational explanation)")
        print("      ├─ ending_trapped (Supernatural tragedy)")  
        print("      ├─ ending_fictional (Meta-fictional revelation)")
        print("      └─ ending_strange_loop (Reader = Author)")

        print("\n  🎭 MARKDOWN FEATURES TESTED:")
        print("  • *Italic* = doubts, uncertainties, questions")
        print("  • **Bold** = certainties, revelations, discoveries") 
        print("  • ~~Strikethrough~~ = abandoned beliefs, revisions")
        print("  • ***Nested emphasis*** = psychological breakdown/breakthrough")
        print("  • > Blockquotes = copied passages, other voices")
        print("  • Lists = inventories, findings, evidence")
        print("  • Images = author's sketches (diegetic references)")
        print("  • Headers = dated journal entries")
        print("  • Horizontal rules = page breaks, reality fractures")

        print("\n  🌀 THEMATIC ELEMENTS:")
        print("  • Existential dread through formatting deterioration")
        print("  • Synchronicity via cross-referenced discoveries")
        print("  • Strange loops through self-referential awareness")  
        print("  • Reality questioning through meta-textual breaks")

        print(f"\n  🎮 Play the story at:")
        print(f"  http://localhost:5173/stories/{builder.story_id}/play")

        test_results["success"] = is_valid
        test_results["end_time"] = datetime.now().isoformat()

        with open(RESULTS_FILE, "w") as f:
            json.dump(test_results, f, indent=2)
        print(f"\n  📊 Results saved to: {RESULTS_FILE}")

        print("=" * 70 + "\n")

        if is_valid:
            print("🎉 THE JOURNAL AWAITS YOUR INTERPRETATION 🎉")
            print()
            print("Will you discover:")
            print("  📚 A scholar's triumph over supernatural forces?")
            print("  👻 A ghost's eternal plea for understanding?")
            print("  🎭 A masterpiece of interactive fiction?")  
            print("  🌀 Your own identity as the author?")
            print()
            print("The choice—and the reality—is yours to create.")

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