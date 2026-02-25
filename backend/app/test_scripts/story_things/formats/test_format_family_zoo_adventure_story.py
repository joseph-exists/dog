#!/usr/bin/env python3
"""
F-3: The Miller Family Zoo Adventure - Interactive Family Narrative

This script creates a story demonstrating family dynamics and choice consequences
in a zoo setting, with branching narratives based on which family member's
perspective drives each decision.

KEY CONCEPTS TESTED:
- Multiple character perspectives within a single story
- Choice consequences that affect family dynamics
- State accumulation based on family member interests
- Convergent branching where different paths meet at shared experiences
- Educational content integration within narrative choices

NARRATIVE THEMES:
- Family bonding through shared discovery
- Different learning styles and interests
- Balancing individual desires with group harmony
- The wonder of wildlife and conservation awareness
- Generational perspectives on nature and animals

STORY STRUCTURE:
- Start: Family arrives at zoo, chooses initial path
- Branch: Different family members suggest different animal areas
- State: Tracks family satisfaction, educational discoveries, time management
- Convergence: Lunch decision point where all paths meet
- 4 endings: Perfect day, compromise day, educational focus, chaos management

=============================================================================

Usage:
    python test_format_family_zoo_adventure_story.py
    python test_format_family_zoo_adventure_story.py --verbose

Output:
    test_results_format_family_zoo_adventure.json
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
RESULTS_FILE = "test_results_format_family_zoo_adventure.json"

# Test results tracking
test_results = {
    "test_suite": "F-3: Family Zoo Adventure Story",
    "start_time": None,
    "end_time": None,
    "story_id": None,
    "node_ids": {},
    "choice_ids": {},
    "state_variable_ids": {},
    "success": False,
    "errors": []
}


class FamilyZooAdventureBuilder:
    """Builds the Miller Family Zoo Adventure story demonstrating family dynamics."""

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
                    is_start: bool = False, is_end: bool = False,
                    content_format: str = "markdown") -> dict:
        response = self.session.post(f"{BASE_URL}/storynodes", json={
            "story_id": self.story_id,
            "story_version": 1,
            "title": title,
            "content": content,
            "node_type": "text",
            "content_format": content_format,
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
        """Build the Miller Family Zoo Adventure story."""

        # =====================================================================
        # STEP 1: CREATE THE STORY
        # =====================================================================
        self.log("\n🎪 Creating story...")

        story = self.create_story(
            title="The Miller Family Zoo Adventure",
            description="""A heartwarming story about the Miller family's day at the zoo, 
demonstrating how different family members' interests and personalities shape their shared experience.

FAMILY MEMBERS:
- Dad (Mark): Loves reading educational signs and teaching moments
- Mom (Sarah): Photography enthusiast, wants to capture perfect family memories  
- Emma (12): Animal lover fascinated by conservation and animal behavior
- Jake (8): Energetic, loves interactive experiences and playground areas
- Grandpa Joe: Enjoys peaceful observation and sharing stories about "back in his day"

STORY FEATURES:
- Multiple character perspectives driving choices
- Educational content woven into narrative
- Family dynamics affecting satisfaction levels
- Time management creating urgency and prioritization
- Conservation themes appropriate for all ages

This story tests complex state management where individual family member satisfaction
affects overall family harmony, and choices reflect realistic family decision-making."""
        )
        self.story_id = story["id"]
        test_results["story_id"] = self.story_id
        self.log(f"  Created story: {self.story_id}")

        # =====================================================================
        # STEP 2: DEFINE STATE SCHEMA
        # =====================================================================
        self.log("\n📋 Creating state schema...")

        # ---------------------------------------------------------------------
        # Family member satisfaction tracking
        # ---------------------------------------------------------------------

        self.state_vars["dad_satisfaction"] = self.create_state_variable(
            key="dad_satisfaction",
            value_type="number",
            default_value=5,
            category="family_dynamics",
            description="Dad's happiness level (0-10). Increases with educational opportunities."
        )

        self.state_vars["mom_satisfaction"] = self.create_state_variable(
            key="mom_satisfaction", 
            value_type="number",
            default_value=5,
            category="family_dynamics",
            description="Mom's happiness level (0-10). Increases with photo opportunities and family bonding."
        )

        self.state_vars["emma_satisfaction"] = self.create_state_variable(
            key="emma_satisfaction",
            value_type="number", 
            default_value=5,
            category="family_dynamics",
            description="Emma's happiness level (0-10). Increases with animal encounters and conservation learning."
        )

        self.state_vars["jake_satisfaction"] = self.create_state_variable(
            key="jake_satisfaction",
            value_type="number",
            default_value=5,
            category="family_dynamics", 
            description="Jake's happiness level (0-10). Increases with interactive activities and energy outlets."
        )

        self.state_vars["grandpa_satisfaction"] = self.create_state_variable(
            key="grandpa_satisfaction",
            value_type="number",
            default_value=5,
            category="family_dynamics",
            description="Grandpa's happiness level (0-10). Increases with peaceful observation and storytelling."
        )

        # ---------------------------------------------------------------------
        # Progress and choice tracking
        # ---------------------------------------------------------------------

        self.state_vars["areas_visited"] = self.create_state_variable(
            key="areas_visited",
            value_type="number",
            default_value=0,
            category="progress",
            description="Number of zoo areas the family has explored together."
        )

        self.state_vars["time_remaining"] = self.create_state_variable(
            key="hours_left",
            value_type="number",
            default_value=4,
            category="logistics",
            description="Hours remaining before zoo closes. Affects available activities."
        )

        self.state_vars["first_area"] = self.create_state_variable(
            key="first_area_choice",
            value_type="enum",
            enum_values=["none", "big_cats", "primates", "aquarium", "petting_zoo", "reptiles"],
            default_value="none",
            category="choice_tracking",
            description="Which animal area the family visited first."
        )

        # ---------------------------------------------------------------------
        # Discovery and learning tracking
        # ---------------------------------------------------------------------

        self.state_vars["educational_discoveries"] = self.create_state_variable(
            key="facts_learned",
            value_type="number",
            default_value=0,
            category="learning",
            description="Number of educational discoveries made by the family."
        )

        self.state_vars["photos_taken"] = self.create_state_variable(
            key="memorable_photos",
            value_type="number",
            default_value=0,
            category="memories",
            description="Number of special photo opportunities captured."
        )

        self.state_vars["conservation_awareness"] = self.create_state_variable(
            key="conservation_learning",
            value_type="enum",
            enum_values=["none", "basic", "engaged", "passionate"],
            default_value="none",
            category="learning",
            description="Family's level of engagement with conservation themes."
        )

        # ---------------------------------------------------------------------
        # Family dynamics
        # ---------------------------------------------------------------------

        self.state_vars["group_harmony"] = self.create_state_variable(
            key="family_harmony",
            value_type="enum",
            enum_values=["tense", "manageable", "good", "excellent"],
            default_value="good",
            category="family_dynamics",
            description="Overall family mood and cooperation level."
        )

        self.state_vars["decision_maker"] = self.create_state_variable(
            key="who_leads_decisions",
            value_type="enum", 
            enum_values=["parents", "kids", "grandpa", "democratic", "chaotic"],
            default_value="parents",
            category="family_dynamics",
            description="Who is primarily driving the family's choices."
        )

        self.log(f"  Created {len(self.state_vars)} state variables")

        # =====================================================================
        # STEP 3: CREATE STORY NODES
        # =====================================================================
        self.log("\n🎭 Creating story nodes...")

        # ---------------------------------------------------------------------
        # START NODE - Arrival at the zoo
        # ---------------------------------------------------------------------

        self.nodes["zoo_entrance"] = self.create_node(
            title="Welcome to Riverside Zoo!",
            content="""# The Miller Family Zoo Adventure Begins!

The morning sun sparkles through the trees as your family approaches the entrance to Riverside Zoo. **Grandpa Joe** adjusts his sun hat and chuckles at the excited chatter filling the air.

"*Well, would you look at that!*" he says, pointing at the colorful entrance arch decorated with painted animals. "*This place has certainly grown since I brought your dad here forty years ago.*"

**Emma** (12) bounces on her toes, clutching her new wildlife journal. "Did you know that zoos today are totally different from back then, Grandpa? They're like *conservation centers* now! They help save endangered species and teach people about protecting habitats!"

**Jake** (8) tugs on **Mom's** sleeve. "Can we see the lions first? Please please please? I heard they have a new baby lion!"

**Dad** pulls out the zoo map, his eyes lighting up with the prospect of planning an educational adventure. "Let's see... we have about four hours before they close. If we're strategic about this, we could hit all the major exhibits *and* catch the 2 PM sea lion show."

**Mom** (Sarah) adjusts her camera strap and smiles. "Whatever we do, I want to make sure we get some wonderful family photos. *This is Emma's first time being tall enough for the height requirements on some of the interactive exhibits!*"

The family stands before a large map showing different themed areas:

- **🦁 Big Cats Territory** - Lions, tigers, and leopards with a new habitat design
- **🐵 Primate Paradise** - Interactive monkey exhibits and orangutan conservation center  
- **🐠 Aquatic Adventures** - Aquarium tunnel and touch tanks with marine education
- **🐰 Barnyard Buddies** - Petting zoo with goats, sheep, and educational farm programs
- **🦎 Reptile Kingdom** - Climate-controlled habitats with rare species and feeding demonstrations

---

**The moment of decision arrives.** Five family members, five different interests, and a whole day of adventure ahead. *Which direction will capture everyone's imagination?*""",
            is_start=True
        )
        self.debug("Created node: zoo_entrance")

        # ---------------------------------------------------------------------
        # AREA NODES - Different first destinations
        # ---------------------------------------------------------------------

        self.nodes["big_cats_first"] = self.create_node(
            title="Roars and Wonder - Big Cats Territory",
            content="""# Into the Heart of Big Cats Territory

The family follows the winding path toward the thunderous sound that makes **Jake's** eyes go wide with excitement. As you round the corner, the magnificent **African Lion habitat** stretches before you—a carefully designed savanna with rocky outcrops, scattered acacia trees, and a sparkling watering hole.

"*Oh my goodness!*" **Mom** gasps, immediately raising her camera. The pride is lounging in the morning sun: a magnificent male with a full golden mane, two lionesses, and—just as Jake had hoped—**a tiny cub barely three months old**.

**Emma** opens her wildlife journal, reading aloud: "*African lions are considered vulnerable, with only about 20,000 left in the wild. Their populations have dropped by 75% in just the past century.*" Her voice carries a note of concern that makes **Grandpa Joe** nod approvingly.

"Smart girl," he says. "You know, when I was your age, we thought there were lions everywhere in Africa. *Times change, and now places like this zoo are helping make sure these beautiful creatures don't disappear forever.*"

**Dad** points to an educational display. "Look at this! They're part of the Species Survival Plan. The cub we're seeing might actually help save his entire species someday."

The young lion cub tumbles playfully near the viewing area, drawing delighted squeals from other visiting children. **Jake** presses his face against the protective glass.

"He's so fluffy!" Jake exclaims. "*I wonder if he likes to play fetch like our dog Max!*"

A nearby **zookeeper** overhears and approaches with a smile. "Actually, lion cubs do love to play! It's how they learn hunting skills they'll need as adults. Would your family like to hear about our cub adoption program?"

---

**The family gathers around as the zookeeper explains conservation efforts.** Everyone seems engaged, but you notice different reactions: *Emma is taking notes frantically, Dad is asking detailed questions about breeding programs, Mom is capturing candid shots of the family learning together, Jake is mimicking the cub's playful pouncing, and Grandpa is sharing a story about the first lion he ever saw.*

*Time is passing, and there's so much more to see. What draws the family's attention next?*""",
        )
        self.debug("Created node: big_cats_first")

        self.nodes["primates_first"] = self.create_node(
            title="Monkey Business - Primate Paradise", 
            content="""# Swinging into Primate Paradise

The family heads toward the chatter and whoops echoing from the **Primate Paradise** section. As you enter the area, **Jake** immediately breaks into giggles at the sight of a group of **spider monkeys** performing what looks like an elaborate acrobatic show in the treetops above.

"*Look at them go!*" he shouts, trying to mimic their arm-over-arm swinging. "I bet I could do that on the playground monkey bars!"

**Emma** is already absorbed in the educational signage. "Did you know that spider monkeys are like the *'gardeners of the rainforest'*? They spread seeds when they travel, helping new trees grow!" She looks up at the swinging primates with new appreciation.

**Mom** finds the perfect angle to capture the family's amazed faces with the monkey habitat in the background. "*This is definitely going in the family album,*" she murmurs, snapping several shots.

The centerpiece of the area is the **Orangutan Conservation Center**—a spacious, enriched habitat where a mother orangutan named **Sari** is teaching her young daughter **Kesi** how to use tools to extract treats from puzzle feeders.

**Grandpa Joe** leans on the railing, mesmerized. "Now *that's* something you don't see every day. Look how she's showing her little one exactly what to do. *Reminds me of teaching your dad how to fish—same patience, same gentle guidance.*"

**Dad** reads from the information plaque: "Orangutans share 97% of their DNA with humans, and they're one of our closest relatives in the animal kingdom. Unfortunately, they're critically endangered due to palm oil plantations destroying their rainforest homes."

A **conservation educator** approaches the family. "I couldn't help but notice your interest! Would you like to learn about our 'Adopt an Orangutan' program? Families can help support Sari and Kesi's care, plus conservation efforts in Borneo."

**Emma's** eyes light up. "Could we really help save orangutans? *That would be the best souvenir ever!*"

Meanwhile, **Jake** has discovered an interactive display where kids can test their problem-solving skills against orangutan intelligence. "*Hey, this puzzle is harder than I thought!*" he says, concentrated on figuring out how to retrieve a toy banana using wooden tools.

---

**The family is fully engaged—learning, playing, and bonding over these incredible primates.** Mom has gotten some wonderful action shots, Dad is deep in conversation with the educator about conservation funding, Emma is already planning how she'll present what she's learned to her class, Jake has mastered the puzzle and is challenging other kids, and Grandpa is sharing stories about intelligence in animals he's observed over the years.

*But the day is moving on, and there are more adventures waiting. What captures the family's interest next?*""",
        )
        self.debug("Created node: primates_first")

        self.nodes["aquarium_first"] = self.create_node(
            title="Under the Sea - Aquatic Adventures",
            content="""# Diving Deep into Aquatic Adventures

The family enters the cool, dimly lit **Aquatic Adventures** building, where the sound of flowing water and gentle music creates an immediately calming atmosphere. **Grandpa Joe** sighs with relief at the comfortable temperature.

"*Now this is nice,*" he says. "Sometimes the old bones appreciate a break from all that walking in the sun."

The first exhibit takes everyone's breath away: a **massive tunnel aquarium** where sharks, rays, and colorful tropical fish swim overhead and all around you. **Jake** spins in circles, trying to watch everything at once.

"It's like we're walking on the ocean floor!" he exclaims, then suddenly stops. "*Whoa, that shark is HUGE!*"

**Emma** immediately recognizes the species. "That's a sand tiger shark! They look scary but they're actually pretty gentle. *Did you know their fierce look helps them hunt, but they rarely attack humans?*"

**Dad** is fascinated by the engineering. "The construction of this tunnel must have been incredible. Look at the thickness of this acrylic—it's probably six inches thick to hold back all that water pressure."

**Mom** is in photographer heaven. The soft, blue lighting filtering through the water creates magical effects on everyone's faces. "*These photos are going to be stunning,*" she whispers, careful not to use her flash around the sensitive sea life.

At the **Interactive Touch Tank** area, a marine biologist named **Dr. Rodriguez** is leading a small group of visitors in gently touching sea stars, anemones, and hermit crabs.

"Would your family like to participate?" she asks. "These creatures are specially cared for and enjoy the gentle interaction. It helps people develop a connection to marine life."

**Jake** is the first to roll up his sleeves. "*Ooh, it feels all bumpy and squishy!*" he says, gently stroking a sea star. 

**Emma** asks thoughtful questions: "Do they mind being touched? How do you make sure they're not stressed?"

Dr. Rodriguez beams. "Excellent questions! We monitor their behavior constantly, and these animals actually show curious behaviors when visitors interact respectfully with them."

**Grandpa Joe** watches his grandchildren with obvious pride. "*You know, when I was young, we thought the ocean was so big it couldn't be hurt by anything humans did. These kids understand things we never even thought about.*"

In the **Conservation Theater**, a short documentary about coral reef restoration plays on a large screen. The family settles in to watch, mesmerized by underwater footage of scientists replanting coral and the vibrant ecosystem that results.

---

**The underwater world has cast its spell on the Miller family.** Jake is now an expert at identifying different fish species, Emma has filled three pages of her journal with marine conservation notes, Dad has struck up a fascinating conversation about water filtration systems with a staff member, Mom has captured some truly artistic shots of everyone interacting with sea life, and Grandpa is sharing stories about his Navy days and the different oceans he's seen.

*The peaceful aquarium environment has been a perfect respite, but adventure calls from other parts of the zoo. Where will the family explore next?*""",
        )
        self.debug("Created node: aquarium_first")

        # ---------------------------------------------------------------------
        # CONVERGENCE NODE - Lunch Decision Point
        # ---------------------------------------------------------------------

        self.nodes["lunch_decision"] = self.create_node(
            title="Midday Hunger and Happy Memories",
            content="""# Time for Lunch and Family Check-in

The morning's adventures have worked up quite an appetite! The family gathers near the **Central Plaza** where several dining options beckon: the **Safari Café** with its healthy wraps and salads, **Jake's Snack Shack** (which definitely caught Jake's attention with its name!), and the **Picnic Grove** where families can enjoy packed lunches at shaded tables.

**Mom** pulls out her phone to check the photos she's taken so far. "*Look at these wonderful shots!*" she says, showing everyone the gallery. "We've already made so many memories this morning."

**Dad** unfolds the zoo map on a nearby bench. "Okay, team meeting! We've got about two hours left, plus we still want to catch that sea lion show at 2 PM. What are our priorities for the afternoon?"

**Emma** flips through her wildlife journal, which is now filled with sketches, facts, and conservation notes. "*I really want to see the reptile area—did you know they have a Galápagos tortoise that's over 100 years old? And maybe we could visit the gift shop to see if they have books about the animals we've seen.*"

**Jake** bounces impatiently. "Can we please go to the playground area after lunch? And I heard there's a place where you can feed the goats! *I brought quarters specifically for the food dispensers!*"

**Grandpa Joe** sits down gratefully on the bench. "You know what sounds good to this old timer? Finding a nice shady spot, maybe watching those sea lions, and hearing about everything you kids have learned today. *These old legs have walked a lot of miles this morning.*"

The **family satisfaction levels** are clearly visible in everyone's faces and energy:

- **Dad** looks pleased with the educational aspects of the morning but is already planning the optimal route for the afternoon
- **Mom** is glowing from capturing beautiful family moments and seems energized by everyone's happiness  
- **Emma** is intellectually stimulated and eager to learn more, especially about conservation
- **Jake** is getting a bit restless and needs some physical activity to balance out all the observing
- **Grandpa Joe** is contentedly tired and would appreciate a more relaxed pace

---

**The lunch decision isn't just about food—it's about how the family wants to spend their remaining time together.** Each choice will set the tone for the afternoon and determine which family members get their most-desired experiences.

*How will the family balance everyone's needs and interests for the perfect conclusion to their zoo adventure?*""",
        )
        self.debug("Created node: lunch_decision")

        # ---------------------------------------------------------------------
        # ENDING NODES - Different family experience outcomes
        # ---------------------------------------------------------------------

        self.nodes["perfect_day_ending"] = self.create_node(
            title="A Perfect Day Together",
            content="""# The Perfect Family Zoo Adventure

As the zoo's closing announcement echoes across the grounds, the Miller family makes their way toward the exit, tired but glowing with satisfaction. **Everyone** got to experience their favorite parts of the zoo, and somehow, through careful planning and family cooperation, nobody felt left out.

**Mom** scrolls through her camera, showing off the day's highlights: "*Look at this one of Emma explaining animal conservation to those other kids! And this one of Jake successfully feeding the goats! Oh, and Grandpa, you look so peaceful watching the sea lions.*"

**Dad** beams with pride, not just at the family photos, but at how well everyone worked together. "I have to say, our family's getting pretty good at this democracy thing. *Everyone spoke up about what they wanted, and we found a way to make it all happen.*"

**Emma** clutches her new field guide purchased from the gift shop, along with her adoption certificate for **Kesi the orangutan**. "This was the *best* educational adventure ever! I can't wait to do my school presentation about conservation. And Mom, can we frame the photo of our whole family with the zoo map showing all the places we visited?"

**Jake** is exhausted but happy, carrying a plush sea lion and wearing his new "Future Marine Biologist" hat. "*My favorite part was feeding the goats, but the touch tank was really cool too. And Grandpa, I loved your story about the time you saw whales in the ocean!*"

**Grandpa Joe** walks slowly but contentedly, his arm linked with Emma's. "You know, I've been to this zoo three different times over forty years—first with your dad, then with you kids, and now watching you become the teachers. *Every generation sees something different, learns something new. That's the real magic.*"

As they reach the parking lot, **Dad** turns back for one last look at the zoo. "Same time next year?"

The unanimous family cheer of "*YES!*" startles a nearby peacock, who fans his tail feathers in what looks suspiciously like approval.

---

## The Miller Family Zoo Adventure: Mission Accomplished

**Family Satisfaction Summary:**
- 🎓 **Dad**: Delighted with educational opportunities and family cooperation (10/10)
- 📸 **Mom**: Thrilled with photos captured and family bonding witnessed (10/10)  
- 🦎 **Emma**: Inspired by conservation learning and animal encounters (10/10)
- 🎠 **Jake**: Energized by interactive experiences and new discoveries (10/10)
- 👴 **Grandpa**: Content with family time and sharing wisdom across generations (10/10)

**Memories Created**: Countless  
**Conservation Awareness**: Significantly increased  
**Family Bonding**: Strengthened  
**Plans for Next Visit**: Already in progress

*Sometimes the best family adventures happen when everyone's voice is heard, everyone's interests are valued, and everyone works together to make magic happen.*""",
            is_end=True
        )
        self.debug("Created node: perfect_day_ending")

        self.nodes["compromise_day_ending"] = self.create_node(
            title="The Art of Family Compromise",
            content="""# A Good Day Built on Give and Take

The Miller family walks toward the zoo exit as the late afternoon sun casts long shadows across the pathways. It wasn't a *perfect* day—there were a few moments of negotiation, some minor disappointments, and one small disagreement about timing—but it was **real family life**, and that made it special in its own way.

**Mom** reviews her photos while walking. "I didn't get quite as many shots as I hoped for, but look at this one of all of us laughing when Jake got splashed by that playful sea lion. *Sometimes the unplanned moments make the best memories.*"

**Dad** folds up the zoo map, slightly crumpled from being consulted frequently. "We didn't hit every exhibit I wanted to show you kids, but we definitely covered the highlights. *And I have to admit, letting Jake choose our lunch spot was a great call—that playground break helped everyone reset.*"

**Emma** closes her wildlife journal, which has several pages filled but not quite as many as she'd planned. "I wish we'd had more time at the reptile house, but learning about the orangutan adoption program was *amazing*. Maybe next time we can focus more on the conservation education center?"

**Jake** drags his feet a little, tired from all the walking but clutching his new stuffed animal. "*I really wanted to ride the carousel, but the goat feeding was pretty awesome. And I got to touch a stingray!*" He perks up at the memory.

**Grandpa Joe** moves slowly but steadily, occasionally chuckling at something he observed during the day. "You know, watching this family work through decisions reminds me that the best adventures aren't about getting everything you want—*they're about learning what matters most and figuring out how to share it.*"

As they reach the car, **Emma** suddenly speaks up: "Hey, can we make a family tradition? Like, every time we come here, we each pick *one* thing that's most important to us, and we make sure everyone gets their pick?"

**Dad** and **Mom** exchange a meaningful look—the kind that says they're proud of how their kids are learning about fairness and family cooperation.

"That," says **Dad**, "sounds like an excellent Miller family tradition."

---

## The Miller Family Zoo Adventure: A Balanced Success

**Family Satisfaction Summary:**
- 🎓 **Dad**: Pleased with learning opportunities, slightly rushed but educational (7/10)
- 📸 **Mom**: Happy with family bonding, would have liked more photo time (7/10)
- 🦎 **Emma**: Engaged with conservation themes, wants more depth next time (8/10)  
- 🎠 **Jake**: Had fun interactive experiences, missed some desired activities (7/10)
- 👴 **Grandpa**: Enjoyed family time, appreciated the pace variations (8/10)

**Life Lessons Learned**: Compromise, family cooperation, speaking up for your needs  
**Memories Created**: Plenty, with room for more next time  
**Planning Skills**: Improved for future family outings  
**Overall Assessment**: A successful family day that everyone can feel good about

*Real families don't have perfect days—they have days where everyone tries to care about each other's happiness, and that's even better.*""",
            is_end=True
        )
        self.debug("Created node: compromise_day_ending")

        self.nodes["educational_focus_ending"] = self.create_node(
            title="Learning Adventure Extraordinaire", 
            content="""# The Miller Family: Conservation Champions

As the zoo prepares to close, the Miller family reluctantly heads toward the exit, their minds buzzing with new knowledge and their hearts full of inspiration for wildlife conservation. What started as a simple family outing transformed into an **educational adventure** that will have lasting impact.

**Emma** can barely contain her excitement, her wildlife journal completely filled and several loose papers tucked inside with additional notes. "*Did you know we saw representatives from all seven major taxonomic groups today? And we learned about conservation efforts on four different continents!*"

**Dad** beams with pride, his own notebook filled with facts he plans to research further. "This was incredible! We talked to actual researchers, learned about Species Survival Plans, and Emma, your questions about genetic diversity were so sophisticated that the primatologist gave you his business card!"

**Mom** flips through her photos, which document not just family moments but also educational signage, conservation displays, and the kids engaged in deep learning. "*These photos tell the story of minds being opened. Look at Jake's face when he realized that touch tank was helping injured sea creatures recover!*"

**Jake** walks more slowly than usual, processing everything he's experienced. "I didn't know animals could be so *smart*. Like, that octopus solved puzzles better than I can! And the zookeeper said that touching the stingrays helps them feel less scared of people. *I helped them feel better just by being gentle!*"

**Grandpa Joe** shakes his head in wonder. "In my eighty-two years, I've never learned so much in a single day. These kids asked questions I never even thought to ask. *And seeing their faces light up when they understood how they could help endangered species—well, that's better than any souvenir.*"

The family makes one final stop at the **Conservation Action Center** near the exit, where **Emma** signs up for the zoo's junior conservationist program, **Jake** commits to participating in the next "Zoo Snooze" overnight educational program, and the whole family enrolls in the adopt-an-animal program.

**Dad** pulls out his phone to check the zoo's website for upcoming conservation lectures. "Look, they have a presentation next month about coral reef restoration. And Emma, there's a summer camp for kids interested in marine biology!"

**Mom** captures one last photo: the whole family gathered around the "Conservation Heroes" wall, where visitors can pledge to make environmentally conscious choices. *Everyone signs their names with enthusiasm.*

---

## The Miller Family Zoo Adventure: Education Mission Accomplished

**Family Satisfaction Summary:**
- 🎓 **Dad**: Thrilled with depth of learning opportunities and family engagement (10/10)
- 📸 **Mom**: Moved by witnessing family's intellectual growth and conservation commitment (9/10)
- 🦎 **Emma**: Completely inspired, already planning her conservation career path (10/10)
- 🎠 **Jake**: Surprised by how much he enjoyed learning, excited about future programs (8/10)
- 👴 **Grandpa**: Amazed by new perspectives and proud of family's values (9/10)

**Conservation Commitments Made**: Multiple ongoing  
**Educational Programs Joined**: 3  
**Future Zoo Visits Planned**: Seasonal membership purchased  
**Career Inspirations Sparked**: At least 2  
**Environmental Consciousness**: Significantly elevated

*The best family adventures aren't just about having fun—they're about growing together, learning together, and finding ways to make the world a better place together.*""",
            is_end=True
        )
        self.debug("Created node: educational_focus_ending")

        self.nodes["chaos_management_ending"] = self.create_node(
            title="Surviving the Zoo Adventure",
            content="""# The Miller Family: Masters of Creative Problem-Solving

As the zoo's closing announcement crackles over the loudspeakers, the Miller family trudges toward the exit looking like they've been through an adventure of epic proportions. **Clothes are rumpled, hair is disheveled, and everyone is thoroughly exhausted—but they're also laughing.**

**Mom** scrolls through her photos, shaking her head in amused disbelief. "Look at this progression: here we are looking fresh and organized at the entrance... here's Jake covered in goat food pellets... here's Emma frantically taking notes while standing in a puddle... *and here's all of us soaking wet from the sea lion show splash zone!*"

**Dad** wipes his forehead with a zoo map that somehow got torn in half during the Great Penguin Exhibit Navigation Crisis. "Well, we definitely didn't stick to the plan. Actually, I'm not sure we had a plan after the first hour. *But hey—we're all here, we're all in one piece, and everyone has stories to tell!*"

**Emma** clutches her wildlife journal, which now has a suspicious stain on the cover (probably from the spilled smoothie incident at lunch). "The day was *chaos*, but I actually learned a lot about animal behavior! Did you see how the monkeys reacted when Jake was making those weird noises? And when Grandpa got lost, those zoo staff members were like a coordinated rescue team!"

**Jake** bounces with residual energy despite being exhausted. "*Best. Day. Ever!* I got splashed by a sea lion, chased by a peacock, and I found Grandpa! Plus that zookeeper said my animal sound imitations were 'surprisingly accurate' for a human!"

**Grandpa Joe** limps slightly but grins widely, sporting a new zoo t-shirt (purchased after his original shirt became a casualty of the "Great Ice Cream Meltdown"). "You know, I may have gotten temporarily separated from you hooligans, but I ended up having a lovely conversation with that nice elderly couple from Toledo. *Sometimes the best adventures are the ones that go completely off the rails.*"

As they reach the parking lot, **Dad** pauses to look back at the zoo entrance. "So, everyone survived. We lost a shoe, found it again, made friends with three different zoo staff members, and I think we accidentally joined some kind of educational program..."

**Mom** laughs while checking that everyone has their belongings. "*And somehow, despite all the chaos, we actually did see most of the animals we wanted to see. It just happened in a completely different order than anyone expected.*"

**Emma** suddenly perks up. "You know what? This was like observing animal behavior, but we *were* the animals! We adapted to changing circumstances, we used problem-solving skills, and we worked together when challenges came up!"

**Jake** nods seriously. "Yeah! We're like a pack of wolves, but nicer and with better snacks!"

---

## The Miller Family Zoo Adventure: Chaos Successfully Managed

**Family Satisfaction Summary:**
- 🎓 **Dad**: Stressed but proud of family resilience and adaptability (6/10)
- 📸 **Mom**: Exhausted but amused by unexpected photo opportunities and family teamwork (7/10)
- 🦎 **Emma**: Overstimulated but delighted by real-world application of animal behavior concepts (8/10)
- 🎠 **Jake**: Tired but exhilarated by high-energy, unpredictable adventure (9/10)  
- 👴 **Grandpa**: Worn out but entertained by family dynamics and new friendships (7/10)

**Crises Successfully Navigated**: 5  
**Zoo Staff Members Befriended**: 3  
**Lost Items Eventually Found**: 2  
**Unexpected Learning Moments**: Countless  
**Family Bonding Through Adversity**: Strengthened  
**Likelihood of Returning**: High (but with better planning)

*Sometimes the most memorable family adventures are the ones where everything goes wrong, everyone pitches in to solve problems, and you all end up laughing about it later.*""",
            is_end=True
        )
        self.debug("Created node: chaos_management_ending")

        self.log(f"  Created {len(self.nodes)} nodes")
        test_results["node_ids"] = {name: node["id"] for name, node in self.nodes.items()}

        # =====================================================================
        # STEP 4: CREATE CHOICES
        # =====================================================================
        self.log("\n🔀 Creating choices...")

        # ---------------------------------------------------------------------
        # FROM: zoo_entrance - Initial area choice
        # ---------------------------------------------------------------------

        self.choices.append(self.create_choice(
            from_node_name="zoo_entrance",
            to_node_name="big_cats_first",
            text="\"Let's go see those lions first! Jake's been talking about the new cub all week.\"",
            order=0,
            sets_state={
                "first_area_choice": "big_cats",
                "areas_visited": 1,
                "hours_left": 3,
                "jake_satisfaction": 7,
                "family_harmony": "excellent"
            }
        ))

        self.choices.append(self.create_choice(
            from_node_name="zoo_entrance", 
            to_node_name="primates_first",
            text="\"The primate area has that new orangutan conservation center. Perfect for photos and learning!\"",
            order=1,
            sets_state={
                "first_area_choice": "primates",
                "areas_visited": 1,
                "hours_left": 3,
                "emma_satisfaction": 7,
                "mom_satisfaction": 7,
                "conservation_learning": "basic",
                "family_harmony": "excellent"
            }
        ))

        self.choices.append(self.create_choice(
            from_node_name="zoo_entrance",
            to_node_name="aquarium_first", 
            text="\"It's getting warm already. Let's start with the air-conditioned aquarium building.\"",
            order=2,
            sets_state={
                "first_area_choice": "aquarium",
                "areas_visited": 1, 
                "hours_left": 3,
                "grandpa_satisfaction": 7,
                "dad_satisfaction": 6,
                "family_harmony": "good",
                "facts_learned": 1
            }
        ))

        # ---------------------------------------------------------------------
        # FROM: All first area nodes - Converge to lunch decision
        # ---------------------------------------------------------------------

        self.choices.append(self.create_choice(
            from_node_name="big_cats_first",
            to_node_name="lunch_decision",
            text="\"That lion cub was amazing! Now I'm getting hungry. Where should we eat?\"",
            order=0,
            sets_state={
                "areas_visited": 2,
                "hours_left": 2,
                "facts_learned": 2,
                "memorable_photos": 1,
                "conservation_learning": "engaged"
            }
        ))

        self.choices.append(self.create_choice(
            from_node_name="primates_first",
            to_node_name="lunch_decision", 
            text="\"The orangutan program was incredible! Let's grab lunch and plan our afternoon.\"",
            order=0,
            sets_state={
                "areas_visited": 2,
                "hours_left": 2,
                "facts_learned": 3,
                "memorable_photos": 2,
                "conservation_learning": "passionate",
                "emma_satisfaction": 8
            }
        ))

        self.choices.append(self.create_choice(
            from_node_name="aquarium_first",
            to_node_name="lunch_decision",
            text="\"The touch tanks were so cool! I'm ready for lunch and more adventures.\"",
            order=0,
            sets_state={
                "areas_visited": 2,
                "hours_left": 2,
                "facts_learned": 2,
                "memorable_photos": 1,
                "jake_satisfaction": 6,
                "dad_satisfaction": 7
            }
        ))

        # ---------------------------------------------------------------------
        # FROM: lunch_decision - Different ending paths based on state
        # ---------------------------------------------------------------------

        # Perfect day ending - requires high satisfaction across family
        self.choices.append(self.create_choice(
            from_node_name="lunch_decision",
            to_node_name="perfect_day_ending",
            text="\"Let's make sure everyone gets their top choice this afternoon!\"",
            order=0,
            requires_state={
                "$and": [
                    {"areas_visited": {"$gte": 2}},
                    {"family_harmony": "excellent"},
                    {"$or": [
                        {"emma_satisfaction": {"$gte": 7}},
                        {"jake_satisfaction": {"$gte": 7}}
                    ]}
                ]
            },
            sets_state={
                "areas_visited": 4,
                "dad_satisfaction": 10,
                "mom_satisfaction": 10,
                "emma_satisfaction": 10,
                "jake_satisfaction": 10,
                "grandpa_satisfaction": 10,
                "family_harmony": "excellent",
                "who_leads_decisions": "democratic"
            }
        ))

        # Compromise ending - balanced satisfaction
        self.choices.append(self.create_choice(
            from_node_name="lunch_decision",
            to_node_name="compromise_day_ending",
            text="\"We can't do everything, but let's make sure nobody goes home disappointed.\"",
            order=1,
            requires_state={
                "areas_visited": {"$gte": 1}
            },
            sets_state={
                "areas_visited": 3,
                "dad_satisfaction": 7,
                "mom_satisfaction": 7, 
                "emma_satisfaction": 8,
                "jake_satisfaction": 7,
                "grandpa_satisfaction": 8,
                "family_harmony": "good",
                "who_leads_decisions": "democratic"
            }
        ))

        # Educational focus ending - high learning engagement
        self.choices.append(self.create_choice(
            from_node_name="lunch_decision",
            to_node_name="educational_focus_ending",
            text="\"This is such a great learning opportunity! Let's focus on the conservation programs.\"",
            order=2,
            requires_state={
                "$and": [
                    {"facts_learned": {"$gte": 2}},
                    {"conservation_learning": {"$in": ["engaged", "passionate"]}}
                ]
            },
            sets_state={
                "areas_visited": 3,
                "dad_satisfaction": 10,
                "mom_satisfaction": 9,
                "emma_satisfaction": 10,
                "jake_satisfaction": 8,
                "grandpa_satisfaction": 9,
                "facts_learned": 8,
                "conservation_learning": "passionate"
            }
        ))

        # Chaos management ending - things go awry but family adapts
        self.choices.append(self.create_choice(
            from_node_name="lunch_decision",
            to_node_name="chaos_management_ending",
            text="\"Let's just wing it and see what happens!\"", 
            order=3,
            requires_state={
                "$and": [
                    {"hours_left": {"$lte": 2}},
                    {"family_harmony": {"$in": ["good", "manageable"]}}
                ]
            },
            sets_state={
                "areas_visited": 4,
                "dad_satisfaction": 6,
                "mom_satisfaction": 7,
                "emma_satisfaction": 8,
                "jake_satisfaction": 9,
                "grandpa_satisfaction": 7,
                "who_leads_decisions": "chaotic",
                "family_harmony": "manageable"
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
        description="Create the Miller Family Zoo Adventure story"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    test_results["start_time"] = datetime.now().isoformat()

    print("\n" + "=" * 70)
    print("  F-3: THE MILLER FAMILY ZOO ADVENTURE")
    print("  Interactive Family Narrative with Branching Dynamics")
    print("=" * 70)

    try:
        session = get_authenticated_session()
        print(f"\n✓ Authenticated successfully")

        builder = FamilyZooAdventureBuilder(session, verbose=args.verbose)
        is_valid = builder.build_story()

        # Summary output
        print("\n" + "=" * 70)
        print("  STORY CREATION COMPLETE")
        print("=" * 70)
        print(f"\n  Story ID: {builder.story_id}")
        print(f"  Nodes created: {len(builder.nodes)}")
        print(f"  Choices created: {len(builder.choices)}")
        print(f"  State variables: {len(builder.state_vars)}")
        print(f"  Schema valid: {'Yes' if is_valid else 'No'}")

        # Visual story structure
        print("\n  🎪 STORY STRUCTURE:")
        print("  ┌─ zoo_entrance (START)")
        print("  │   ├─→ big_cats_first (Jake's excitement about lion cub)")
        print("  │   ├─→ primates_first (Conservation learning & photo ops)")
        print("  │   └─→ aquarium_first (Cool environment & educational)")
        print("  │")
        print("  └─→ lunch_decision (CONVERGENCE)")
        print("      ├─→ perfect_day_ending (Everyone satisfied)")
        print("      ├─→ compromise_day_ending (Balanced family needs)")
        print("      ├─→ educational_focus_ending (Conservation champions)")
        print("      └─→ chaos_management_ending (Adventure through adversity)")

        print("\n  👨‍👩‍👧‍👦 FAMILY DYNAMICS TESTED:")
        print("  • Individual satisfaction tracking (5 family members)")
        print("  • Decision-making processes (democratic vs chaotic)")
        print("  • Educational discovery vs entertainment balance")
        print("  • Time management and priority setting")
        print("  • Generational perspectives on experiences")

        print("\n  🎯 EDUCATIONAL THEMES:")
        print("  • Wildlife conservation awareness")
        print("  • Animal behavior and intelligence") 
        print("  • Family cooperation and compromise")
        print("  • Respecting different learning styles")
        print("  • Creating lasting memories together")

        print(f"\n  🎮 Play the story at:")
        print(f"  http://localhost:5173/story/{builder.story_id}")

        test_results["success"] = is_valid
        test_results["end_time"] = datetime.now().isoformat()

        with open(RESULTS_FILE, "w") as f:
            json.dump(test_results, f, indent=2)
        print(f"\n  📊 Results saved to: {RESULTS_FILE}")

        print("=" * 70 + "\n")

        if is_valid:
            print("🎉 THE MILLER FAMILY ZOO ADVENTURE AWAITS! 🎉")
            print()
            print("Will your family create:")
            print("  🦁 A perfectly balanced day where everyone's dreams come true?")
            print("  🤝 A compromise adventure teaching cooperation?")
            print("  📚 An educational journey inspiring conservation action?")
            print("  🎪 A chaotic but memorable bonding experience?")
            print()
            print("The choices—and the memories—are yours to make!")

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