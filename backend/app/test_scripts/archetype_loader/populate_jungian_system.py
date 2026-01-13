#!/usr/bin/env python3
"""
Populate TinyFoot with Jungian Archetype System

Creates a complete Jungian-inspired character system with:
- 12 Jungian archetypes
- 3 traits per archetype (36 total traits)
- 10 qualities
- 3 personas per archetype (36 total personas)
- Full relationship linking between all entities

Test Structure:
1. Authentication
2. Create Qualities (10)
3. Create Traits (36)
4. Create Archetypes (12)
5. Link Qualities to Traits
6. Create Personas from Archetypes (36) - automatically inherits traits
7. Link Personas to Qualities
8. Validate all relationships

Results saved to: test_results_jungian_system.json
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

# Add auth_helper to path
sys.path.append(str(Path(__file__).parent))
from auth_helper import get_authenticated_session, AuthenticationError

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
OUTPUT_FILE = "test_results_jungian_system.json"

# Test Data: 12 Jungian Archetypes
JUNGIAN_ARCHETYPES = [
    {
        "name": "The Innocent",
        "description": "Seeks safety, happiness, and simple joys. Optimistic and trusting.",
        "traits": [
            {"name": "Optimism", "description": "Sees the bright side and believes in positive outcomes"},
            {"name": "Trusting", "description": "Places faith in others and the world"},
            {"name": "Naive", "description": "Lacks awareness of danger or deception"}
        ],
        "personas": [
            {"name": "The Dreamer", "description": "Lives in hope and imagination"},
            {"name": "The Child", "description": "Embodies wonder and purity"},
            {"name": "The Idealist", "description": "Believes in a better world"}
        ]
    },
    {
        "name": "The Sage",
        "description": "Seeks truth, knowledge, and understanding. Values wisdom above all.",
        "traits": [
            {"name": "Analytical", "description": "Examines situations with logic and reason"},
            {"name": "Curious", "description": "Driven to understand and discover"},
            {"name": "Detached", "description": "Maintains emotional distance for objectivity"}
        ],
        "personas": [
            {"name": "The Philosopher", "description": "Contemplates deep existential questions"},
            {"name": "The Scholar", "description": "Accumulates and shares knowledge"},
            {"name": "The Mentor", "description": "Guides others toward understanding"}
        ]
    },
    {
        "name": "The Explorer",
        "description": "Seeks freedom, discovery, and authenticity. Values independence and new experiences.",
        "traits": [
            {"name": "Adventurous", "description": "Embraces new experiences and challenges"},
            {"name": "Independent", "description": "Values autonomy and self-reliance"},
            {"name": "Restless", "description": "Feels constrained by routine and limits"}
        ],
        "personas": [
            {"name": "The Wanderer", "description": "Roams seeking new horizons"},
            {"name": "The Pioneer", "description": "Blazes new trails and charts unknown territory"},
            {"name": "The Seeker", "description": "Searches for authentic self and truth"}
        ]
    },
    {
        "name": "The Outlaw",
        "description": "Seeks revolution and liberation. Challenges the status quo and breaks rules.",
        "traits": [
            {"name": "Rebellious", "description": "Defies authority and convention"},
            {"name": "Bold", "description": "Takes risks others fear to take"},
            {"name": "Disruptive", "description": "Shakes up established order"}
        ],
        "personas": [
            {"name": "The Revolutionary", "description": "Fights to overturn unjust systems"},
            {"name": "The Maverick", "description": "Goes their own way regardless of consequences"},
            {"name": "The Iconoclast", "description": "Destroys outdated beliefs and structures"}
        ]
    },
    {
        "name": "The Magician",
        "description": "Seeks transformation and making dreams reality. Makes things happen.",
        "traits": [
            {"name": "Visionary", "description": "Sees possibilities others cannot"},
            {"name": "Charismatic", "description": "Inspires and influences through presence"},
            {"name": "Manipulative", "description": "Bends reality and people to their will"}
        ],
        "personas": [
            {"name": "The Wizard", "description": "Transforms reality through knowledge and power"},
            {"name": "The Catalyst", "description": "Sparks change in people and situations"},
            {"name": "The Shaman", "description": "Bridges worlds and facilitates healing"}
        ]
    },
    {
        "name": "The Hero",
        "description": "Seeks to prove worth through courageous acts. Values strength and mastery.",
        "traits": [
            {"name": "Courageous", "description": "Faces danger without backing down"},
            {"name": "Determined", "description": "Pursues goals with unwavering resolve"},
            {"name": "Competitive", "description": "Driven to win and prove superiority"}
        ],
        "personas": [
            {"name": "The Warrior", "description": "Fights for what they believe in"},
            {"name": "The Champion", "description": "Defends the weak and upholds justice"},
            {"name": "The Dragon Slayer", "description": "Confronts and overcomes great evils"}
        ]
    },
    {
        "name": "The Lover",
        "description": "Seeks intimacy, beauty, and connection. Values passion and relationships.",
        "traits": [
            {"name": "Passionate", "description": "Feels deeply and loves intensely"},
            {"name": "Devoted", "description": "Commits fully to people and causes"},
            {"name": "Vulnerable", "description": "Opens heart despite risk of pain"}
        ],
        "personas": [
            {"name": "The Romantic", "description": "Pursues ideal love and beauty"},
            {"name": "The Sensualist", "description": "Savors pleasure and aesthetic experience"},
            {"name": "The Companion", "description": "Creates deep bonds and partnerships"}
        ]
    },
    {
        "name": "The Jester",
        "description": "Seeks joy and living in the moment. Uses humor to transform pain.",
        "traits": [
            {"name": "Playful", "description": "Finds fun and games in all situations"},
            {"name": "Irreverent", "description": "Mocks sacred cows and pomposity"},
            {"name": "Spontaneous", "description": "Acts on impulse without overthinking"}
        ],
        "personas": [
            {"name": "The Trickster", "description": "Uses wit and mischief to teach lessons"},
            {"name": "The Fool", "description": "Speaks truth through apparent nonsense"},
            {"name": "The Comedian", "description": "Heals through laughter and levity"}
        ]
    },
    {
        "name": "The Everyman",
        "description": "Seeks belonging and connection. Values equality and being down-to-earth.",
        "traits": [
            {"name": "Relatable", "description": "Connects through shared common experience"},
            {"name": "Humble", "description": "Doesn't put on airs or seek special status"},
            {"name": "Empathetic", "description": "Understands others' struggles and feelings"}
        ],
        "personas": [
            {"name": "The Regular Guy", "description": "Ordinary person facing life's challenges"},
            {"name": "The Good Neighbor", "description": "Reliable and supportive community member"},
            {"name": "The Realist", "description": "Sees life as it is without illusion"}
        ]
    },
    {
        "name": "The Caregiver",
        "description": "Seeks to protect and care for others. Values compassion and service.",
        "traits": [
            {"name": "Nurturing", "description": "Provides comfort and support to others"},
            {"name": "Self-Sacrificing", "description": "Puts others' needs before their own"},
            {"name": "Protective", "description": "Guards loved ones from harm"}
        ],
        "personas": [
            {"name": "The Healer", "description": "Mends wounds physical and emotional"},
            {"name": "The Guardian", "description": "Shields the vulnerable from danger"},
            {"name": "The Parent", "description": "Raises and guides the next generation"}
        ]
    },
    {
        "name": "The Ruler",
        "description": "Seeks control and order. Values power, stability, and leadership.",
        "traits": [
            {"name": "Authoritative", "description": "Commands respect and obedience"},
            {"name": "Organized", "description": "Creates systems and maintains order"},
            {"name": "Controlling", "description": "Must have things done their way"}
        ],
        "personas": [
            {"name": "The Sovereign", "description": "Rules with wisdom and authority"},
            {"name": "The Executive", "description": "Manages resources and makes decisions"},
            {"name": "The Patriarch", "description": "Leads family or clan with firm hand"}
        ]
    },
    {
        "name": "The Creator",
        "description": "Seeks to create enduring value and express vision. Values imagination and innovation.",
        "traits": [
            {"name": "Imaginative", "description": "Envisions what doesn't yet exist"},
            {"name": "Perfectionist", "description": "Demands excellence in all creations"},
            {"name": "Non-Conformist", "description": "Rejects templates in favor of originality"}
        ],
        "personas": [
            {"name": "The Artist", "description": "Expresses inner vision through creative work"},
            {"name": "The Inventor", "description": "Builds new solutions to problems"},
            {"name": "The Visionary Leader", "description": "Imagines and manifests better futures"}
        ]
    }
]

# 10 Universal Qualities
QUALITIES = [
    {"name": "Strength", "description": "Physical and mental fortitude"},
    {"name": "Intelligence", "description": "Mental acuity and problem-solving ability"},
    {"name": "Charisma", "description": "Social influence and persuasiveness"},
    {"name": "Wisdom", "description": "Deep understanding and good judgment"},
    {"name": "Agility", "description": "Physical dexterity and quick reflexes"},
    {"name": "Resilience", "description": "Ability to recover from adversity"},
    {"name": "Creativity", "description": "Capacity for original thought and innovation"},
    {"name": "Empathy", "description": "Understanding and sharing others' feelings"},
    {"name": "Willpower", "description": "Self-discipline and determination"},
    {"name": "Perception", "description": "Awareness and ability to notice details"}
]

# Quality-Trait mapping (which qualities are boosted by which traits)
QUALITY_TRAIT_LINKS = {
    "Strength": ["Courageous", "Determined", "Protective", "Authoritative"],
    "Intelligence": ["Analytical", "Curious", "Organized", "Imaginative"],
    "Charisma": ["Charismatic", "Playful", "Relatable", "Passionate"],
    "Wisdom": ["Analytical", "Detached", "Empathetic", "Perfectionist"],
    "Agility": ["Adventurous", "Spontaneous", "Restless"],
    "Resilience": ["Rebellious", "Determined", "Self-Sacrificing", "Humble"],
    "Creativity": ["Imaginative", "Visionary", "Non-Conformist", "Playful"],
    "Empathy": ["Nurturing", "Empathetic", "Vulnerable", "Devoted"],
    "Willpower": ["Determined", "Controlling", "Perfectionist", "Bold"],
    "Perception": ["Curious", "Detached", "Irreverent"]
}


class TestResults:
    """Track test results and entity IDs"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.results = {
            "test_run": {
                "start_time": self.start_time.isoformat(),
                "end_time": None,
                "duration_seconds": None,
                "success": False
            },
            "authentication": {"status": "pending", "user": None},
            "qualities": {"status": "pending", "created": 0, "failed": 0, "entities": {}},
            "traits": {"status": "pending", "created": 0, "failed": 0, "entities": {}},
            "archetypes": {"status": "pending", "created": 0, "failed": 0, "entities": {}},
            "personas": {"status": "pending", "created": 0, "failed": 0, "entities": {}},
            "links": {
                "quality_trait": {"status": "pending", "created": 0, "failed": 0, "entities": []},
                "persona_quality": {"status": "pending", "created": 0, "failed": 0, "entities": []}
            },
            "errors": []
        }
        
    def set_auth(self, user_data: dict):
        """Record successful authentication"""
        self.results["authentication"] = {
            "status": "success",
            "user": user_data
        }
        
    def add_quality(self, name: str, quality_id: str):
        """Record created quality"""
        self.results["qualities"]["entities"][name] = quality_id
        self.results["qualities"]["created"] += 1
        
    def add_trait(self, name: str, trait_id: str):
        """Record created trait"""
        self.results["traits"]["entities"][name] = trait_id
        self.results["traits"]["created"] += 1
        
    def add_archetype(self, name: str, archetype_id: str):
        """Record created archetype"""
        self.results["archetypes"]["entities"][name] = archetype_id
        self.results["archetypes"]["created"] += 1
        
    def add_persona(self, name: str, persona_id: str):
        """Record created persona"""
        self.results["personas"]["entities"][name] = persona_id
        self.results["personas"]["created"] += 1
        
    def add_link(self, link_type: str, link_data: dict):
        """Record created link"""
        self.results["links"][link_type]["entities"].append(link_data)
        self.results["links"][link_type]["created"] += 1
        
    def add_error(self, category: str, error: str):
        """Record an error"""
        self.results["errors"].append({
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "error": error
        })
        if category in self.results:
            self.results[category]["failed"] = self.results[category].get("failed", 0) + 1
        elif category in self.results["links"]:
            self.results["links"][category]["failed"] = self.results["links"][category].get("failed", 0) + 1
            
    def finalize(self, success: bool):
        """Finalize test results"""
        end_time = datetime.now()
        self.results["test_run"]["end_time"] = end_time.isoformat()
        self.results["test_run"]["duration_seconds"] = (end_time - self.start_time).total_seconds()
        self.results["test_run"]["success"] = success
        
        # Set status for all categories
        for category in ["qualities", "traits", "archetypes", "personas"]:
            if self.results[category]["created"] > 0:
                self.results[category]["status"] = "success" if self.results[category]["failed"] == 0 else "partial"
            elif self.results[category]["failed"] > 0:
                self.results[category]["status"] = "failed"
                
        for link_type in self.results["links"]:
            if self.results["links"][link_type]["created"] > 0:
                self.results["links"][link_type]["status"] = "success" if self.results["links"][link_type]["failed"] == 0 else "partial"
            elif self.results["links"][link_type]["failed"] > 0:
                self.results["links"][link_type]["status"] = "failed"
                
    def save(self, filename: str = OUTPUT_FILE):
        """Save results to JSON file"""
        output_path = Path(__file__).parent / filename
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Results saved to: {output_path}")


def print_header(title: str):
    """Print a formatted section header"""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def create_entity(session: requests.Session, endpoint: str, data: dict, entity_type: str) -> dict | None:
    """
    Generic function to create an entity via API
    
    Returns:
        dict: Created entity data or None on failure
    """
    try:
        response = session.post(f"{BASE_URL}/{endpoint}", json=data)
        
        if response.status_code in [200, 201]:
            entity = response.json()
            return entity
        else:
            print(f"    ❌ Failed to create {entity_type}: {response.status_code}")
            print(f"       Error: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"    ❌ Exception creating {entity_type}: {str(e)}")
        return None


def create_link(session: requests.Session, endpoint: str, data: dict, link_type: str) -> dict | None:
    """
    Generic function to create a relationship link via API
    
    Returns:
        dict: Created link data or None on failure
    """
    try:
        response = session.post(f"{BASE_URL}/{endpoint}", json=data)
        
        if response.status_code in [200, 201]:
            link = response.json()
            return link
        else:
            print(f"    ❌ Failed to create {link_type} link: {response.status_code}")
            print(f"       Error: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"    ❌ Exception creating {link_type} link: {str(e)}")
        return None


def main():
    """Main test execution"""
    print("\n" + "🎭" * 35)
    print("  JUNGIAN ARCHETYPE SYSTEM POPULATION TEST")
    print("🎭" * 35)
    
    results = TestResults()
    session = None
    
    # Map trait names to archetype names for later persona creation
    trait_to_archetype = {}
    
    try:
        # Step 1: Authentication
        print_header("Step 1: Authentication")
        session = get_authenticated_session()
        
        # Get user info
        response = session.get(f"{BASE_URL}/users/me")
        if response.status_code == 200:
            user_data = response.json()
            results.set_auth(user_data)
            print(f"  ✅ Authenticated as: {user_data.get('email')}")
            print(f"  👤 User: {user_data.get('full_name', 'N/A')}")
            print(f"  🔒 Superuser: {user_data.get('is_superuser', False)}")
        else:
            raise Exception("Failed to get user info")
        
        # Step 2: Create Qualities
        print_header("Step 2: Creating Qualities (10)")
        for i, quality_data in enumerate(QUALITIES, 1):
            print(f"\n  Creating quality {i}/10: {quality_data['name']}")
            entity = create_entity(session, "qualities", quality_data, "quality")
            
            if entity:
                results.add_quality(quality_data['name'], entity['id'])
                print(f"    ✅ Created: {quality_data['name']} (ID: {entity['id']})")
            else:
                results.add_error("qualities", f"Failed to create quality: {quality_data['name']}")
        
        print(f"\n  📊 Qualities: {results.results['qualities']['created']} created, "
              f"{results.results['qualities']['failed']} failed")
        
        # Step 3: Create Traits (from archetypes data)
        print_header("Step 3: Creating Traits (36)")
        trait_count = 0
        total_traits = len(JUNGIAN_ARCHETYPES) * 3
        
        for archetype_data in JUNGIAN_ARCHETYPES:
            for trait_data in archetype_data['traits']:
                trait_count += 1
                print(f"\n  Creating trait {trait_count}/{total_traits}: {trait_data['name']}")
                entity = create_entity(session, "traits", trait_data, "trait")
                
                if entity:
                    results.add_trait(trait_data['name'], entity['id'])
                    trait_to_archetype[trait_data['name']] = archetype_data['name']
                    print(f"    ✅ Created: {trait_data['name']} (ID: {entity['id']})")
                else:
                    results.add_error("traits", f"Failed to create trait: {trait_data['name']}")
        
        print(f"\n  📊 Traits: {results.results['traits']['created']} created, "
              f"{results.results['traits']['failed']} failed")
        
        # Step 4: Create Archetypes
        print_header("Step 4: Creating Archetypes (12)")
        for i, archetype_data in enumerate(JUNGIAN_ARCHETYPES, 1):
            print(f"\n  Creating archetype {i}/12: {archetype_data['name']}")
            entity = create_entity(
                session, 
                "archetypes", 
                {"name": archetype_data['name'], "description": archetype_data['description']},
                "archetype"
            )
            
            if entity:
                results.add_archetype(archetype_data['name'], entity['id'])
                print(f"    ✅ Created: {archetype_data['name']} (ID: {entity['id']})")
            else:
                results.add_error("archetypes", f"Failed to create archetype: {archetype_data['name']}")
        
        print(f"\n  📊 Archetypes: {results.results['archetypes']['created']} created, "
              f"{results.results['archetypes']['failed']} failed")
        
        # Step 5: Link Qualities to Traits
        print_header("Step 5: Linking Qualities to Traits")
        link_count = 0
        
        for quality_name, trait_names in QUALITY_TRAIT_LINKS.items():
            quality_id = results.results['qualities']['entities'].get(quality_name)
            
            if not quality_id:
                print(f"  ⚠️  Skipping links for quality {quality_name} - not created")
                continue
            
            for trait_name in trait_names:
                trait_id = results.results['traits']['entities'].get(trait_name)
                
                if not trait_id:
                    print(f"  ⚠️  Skipping link for trait {trait_name} - not created")
                    results.add_error("quality_trait", f"Trait not found: {trait_name}")
                    continue
                
                link_count += 1
                print(f"\n  Creating link {link_count}: {quality_name} ↔ {trait_name}")
                
                link = create_link(
                    session,
                    "quality-trait-links",
                    {
                        "quality_id": quality_id, 
                        "trait_id": trait_id,
                        "auto_enable": True,
                        "is_required": False
                    },
                    "quality-trait"
                )
                
                if link:
                    results.add_link("quality_trait", {
                        "quality": quality_name,
                        "trait": trait_name,
                        "link_id": link.get('id')
                    })
                    print(f"    ✅ Linked: {quality_name} ↔ {trait_name}")
                else:
                    results.add_error("quality_trait", 
                                    f"Failed to link {quality_name} ↔ {trait_name}")
        
        print(f"\n  📊 Quality-Trait Links: {results.results['links']['quality_trait']['created']} created, "
              f"{results.results['links']['quality_trait']['failed']} failed")
        
        # Step 6: Create Personas from Archetypes (automatically inherits traits)
        print_header("Step 6: Creating Personas from Archetypes (36)")
        print("  Note: Personas automatically inherit traits from their archetype")
        persona_count = 0
        total_personas = len(JUNGIAN_ARCHETYPES) * 3
        
        for archetype_data in JUNGIAN_ARCHETYPES:
            archetype_name = archetype_data['name']
            archetype_id = results.results['archetypes']['entities'].get(archetype_name)
            
            if not archetype_id:
                print(f"  ⚠️  Skipping personas for {archetype_name} - archetype not created")
                continue
            
            for persona_data in archetype_data['personas']:
                persona_count += 1
                print(f"\n  Creating persona {persona_count}/{total_personas}: {persona_data['name']}")
                print(f"    (from archetype: {archetype_name})")
                
                # Use the special endpoint that creates persona from archetype
                try:
                    response = session.post(
                        f"{BASE_URL}/personas/from-archetype/{archetype_id}",
                        json={
                            "name": persona_data['name'],
                            "description": persona_data['description'],
                            "long_description": f"A persona of {archetype_name}: {persona_data['description']}"
                        }
                    )
                    
                    if response.status_code in [200, 201]:
                        entity = response.json()
                        results.add_persona(persona_data['name'], entity['id'])
                        print(f"    ✅ Created: {persona_data['name']} (ID: {entity['id']})")
                        print(f"       (Automatically inherited {len(archetype_data['traits'])} traits)")
                    else:
                        print(f"    ❌ Failed: {response.status_code}")
                        print(f"       Error: {response.text[:200]}")
                        results.add_error("personas", f"Failed to create persona: {persona_data['name']}")
                        
                except Exception as e:
                    print(f"    ❌ Exception: {str(e)}")
                    results.add_error("personas", f"Exception creating persona: {persona_data['name']}")
        
        print(f"\n  📊 Personas: {results.results['personas']['created']} created, "
              f"{results.results['personas']['failed']} failed")
        
        # Step 7: Link Personas to Qualities (based on their inherited traits)
        print_header("Step 7: Linking Personas to Qualities")
        print("  (Based on traits inherited from archetypes)")
        link_count = 0
        
        for archetype_data in JUNGIAN_ARCHETYPES:
            # Get all traits for this archetype
            archetype_traits = [t['name'] for t in archetype_data['traits']]
            
            # Find all qualities that should be linked (based on traits)
            qualities_to_link = set()
            for quality_name, trait_names in QUALITY_TRAIT_LINKS.items():
                for trait_name in trait_names:
                    if trait_name in archetype_traits:
                        qualities_to_link.add(quality_name)
            
            # Link each persona from this archetype to the relevant qualities
            for persona_data in archetype_data['personas']:
                persona_name = persona_data['name']
                persona_id = results.results['personas']['entities'].get(persona_name)
                
                if not persona_id:
                    continue
                
                for quality_name in qualities_to_link:
                    quality_id = results.results['qualities']['entities'].get(quality_name)
                    
                    if not quality_id:
                        continue
                    
                    link_count += 1
                    print(f"\n  Creating link {link_count}: {persona_name} → {quality_name}")
                    
                    try:
                        response = session.post(
                            f"{BASE_URL}/personas/{persona_id}/qualities/{quality_id}"
                        )
                        
                        if response.status_code in [200, 201]:
                            results.add_link("persona_quality", {
                                "persona": persona_name,
                                "quality": quality_name
                            })
                            print(f"    ✅ Linked: {persona_name} → {quality_name}")
                        else:
                            print(f"    ❌ Failed: {response.status_code}")
                            results.add_error("persona_quality", 
                                            f"Failed to link {persona_name} → {quality_name}")
                    except Exception as e:
                        print(f"    ❌ Exception: {str(e)}")
                        results.add_error("persona_quality", 
                                        f"Exception linking {persona_name} → {quality_name}")
        
        print(f"\n  📊 Persona-Quality Links: {results.results['links']['persona_quality']['created']} created, "
              f"{results.results['links']['persona_quality']['failed']} failed")
        
        # Final Summary
        print_header("Test Summary")
        print(f"  ⏱️  Duration: {(datetime.now() - results.start_time).total_seconds():.2f} seconds")
        print(f"\n  📊 Entities Created:")
        print(f"    • Qualities:  {results.results['qualities']['created']}/10")
        print(f"    • Traits:     {results.results['traits']['created']}/36")
        print(f"    • Archetypes: {results.results['archetypes']['created']}/12")
        print(f"    • Personas:   {results.results['personas']['created']}/36")
        
        print(f"\n  🔗 Relationships Created:")
        print(f"    • Quality-Trait:    {results.results['links']['quality_trait']['created']}")
        print(f"    • Persona-Quality:  {results.results['links']['persona_quality']['created']}")
        print(f"\n  📝 Note: Persona-Trait links (108) are created automatically")
        print(f"           when personas are created from archetypes")
        
        total_errors = len(results.results['errors'])
        if total_errors > 0:
            print(f"\n  ⚠️  Total Errors: {total_errors}")
            print(f"    (See {OUTPUT_FILE} for details)")
        else:
            print(f"\n  ✅ No errors - all operations successful!")
        
        # Determine overall success
        success = (
            results.results['qualities']['failed'] == 0 and
            results.results['traits']['failed'] == 0 and
            results.results['archetypes']['failed'] == 0 and
            results.results['personas']['failed'] == 0 and
            total_errors == 0
        )
        
        results.finalize(success)
        results.save()
        
        if success:
            print("\n" + "🎉" * 35)
            print("  TEST COMPLETED SUCCESSFULLY!")
            print("🎉" * 35)
        else:
            print("\n" + "⚠️ " * 35)
            print("  TEST COMPLETED WITH ERRORS")
            print("⚠️ " * 35)
        
        return 0 if success else 1
        
    except AuthenticationError as e:
        print(f"\n❌ Authentication Error: {e}")
        results.add_error("authentication", str(e))
        results.finalize(False)
        results.save()
        return 1
        
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        results.add_error("general", str(e))
        results.finalize(False)
        results.save()
        return 1


if __name__ == "__main__":
    sys.exit(main())
