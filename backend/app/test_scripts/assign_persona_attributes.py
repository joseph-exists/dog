#!/usr/bin/env python3
"""
Attribute Assignment Script for TinyFoot Personas

Reads attributes from a CSV file and assigns them to personas
missing data in specified fields. Supports both sequential and
stochastic (random) assignment modes.

Usage Examples:
    # Dry run to preview changes
    python assign_persona_attributes.py \\
        --file attributes.csv \\
        --field general_domain \\
        --sample-size 2 \\
        --dry-run

    # Sequential assignment (default)
    python assign_persona_attributes.py \\
        --file attributes.csv \\
        --field general_domain \\
        --sample-size 2

    # Stochastic (random) assignment with replacement
    python assign_persona_attributes.py \\
        --file attributes.csv \\
        --field specific_domain \\
        --sample-size 3 \\
        --mode stochastic

    # Assign to long_description field
    python assign_persona_attributes.py \\
        --file descriptions.csv \\
        --field long_description \\
        --sample-size 1 \\
        --separator " "

CSV File Format:
    Comma-separated values, can span multiple rows
    Example: funny,serious,professor,mohawk
             loves oranges,afraid of the dark,heavily tattooed
"""

import argparse
import csv
import json
import random
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
OUTPUT_FILE = "assignment_results.json"

# Valid persona fields that can be assigned
VALID_FIELDS = [
    'general_domain',
    'specific_domain', 
    'general_domain_high',
    'specific_domain_high',
    'long_description'
]


class AssignmentResults:
    """Track assignment results and statistics"""
    
    def __init__(self, field_name: str, mode: str):
        self.start_time = datetime.now()
        self.field_name = field_name
        self.mode = mode
        self.results = {
            "assignment_run": {
                "start_time": self.start_time.isoformat(),
                "end_time": None,
                "duration_seconds": None,
                "field": field_name,
                "mode": mode,
                "success": False
            },
            "authentication": {"status": "pending", "user": None},
            "attributes": {
                "total_loaded": 0,
                "source_file": None
            },
            "personas": {
                "total_found": 0,
                "missing_field": 0,
                "updated": 0,
                "failed": 0,
                "assignments": []
            },
            "errors": []
        }
        
    def set_auth(self, user_data: dict):
        """Record successful authentication"""
        self.results["authentication"] = {
            "status": "success",
            "user": user_data
        }
        
    def set_attributes(self, count: int, source_file: str):
        """Record loaded attributes"""
        self.results["attributes"]["total_loaded"] = count
        self.results["attributes"]["source_file"] = source_file
        
    def set_personas_found(self, total: int, missing: int):
        """Record persona counts"""
        self.results["personas"]["total_found"] = total
        self.results["personas"]["missing_field"] = missing
        
    def add_assignment(self, persona_name: str, persona_id: str, attributes: list[str], success: bool):
        """Record an assignment attempt"""
        if success:
            self.results["personas"]["updated"] += 1
        else:
            self.results["personas"]["failed"] += 1
            
        self.results["personas"]["assignments"].append({
            "persona_name": persona_name,
            "persona_id": persona_id,
            "attributes": attributes,
            "success": success,
            "timestamp": datetime.now().isoformat()
        })
        
    def add_error(self, error: str):
        """Record an error"""
        self.results["errors"].append({
            "timestamp": datetime.now().isoformat(),
            "error": error
        })
        
    def finalize(self, success: bool):
        """Finalize results"""
        end_time = datetime.now()
        self.results["assignment_run"]["end_time"] = end_time.isoformat()
        self.results["assignment_run"]["duration_seconds"] = (end_time - self.start_time).total_seconds()
        self.results["assignment_run"]["success"] = success
        
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


def load_attributes(filepath: Path) -> list[str]:
    """
    Load attributes from CSV file
    
    Returns list of trimmed attribute strings
    """
    attributes = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            # Add each cell as an attribute, stripping whitespace
            for cell in row:
                attr = cell.strip()
                if attr:  # Only add non-empty attributes
                    attributes.append(attr)
    
    return attributes


def get_all_personas(session: requests.Session) -> list[dict]:
    """
    Fetch all personas from API
    
    Returns list of persona dictionaries
    """
    try:
        # Use a high limit to get all personas in one call
        response = session.get(f"{BASE_URL}/personas?limit=1000")
        
        if response.status_code == 200:
            data = response.json()
            return data.get('data', [])
        else:
            print(f"    ❌ Failed to fetch personas: {response.status_code}")
            print(f"       Error: {response.text[:200]}")
            return []
            
    except Exception as e:
        print(f"    ❌ Exception fetching personas: {str(e)}")
        return []


def filter_personas_missing_field(personas: list[dict], field_name: str) -> list[dict]:
    """
    Filter personas that are missing data in the specified field
    
    A field is considered "missing" if:
    - The field doesn't exist in the persona dict
    - The field value is None
    - The field value is an empty string
    """
    missing = []
    
    for persona in personas:
        value = persona.get(field_name)
        if value is None or value == "":
            missing.append(persona)
    
    return missing


def assign_attributes_sequential(
    attributes: list[str], 
    n_personas: int, 
    sample_size: int
) -> list[list[str]]:
    """
    Assign attributes sequentially without replacement
    
    Takes sample_size attributes from the front of the list for each persona,
    removing them from the pool as they're used.
    
    Returns list of attribute lists (one per persona)
    """
    assignments = []
    attribute_pool = attributes.copy()
    
    for _ in range(n_personas):
        # Take up to sample_size from front of pool
        take_count = min(sample_size, len(attribute_pool))
        if take_count == 0:
            # No more attributes available
            break
            
        selected = attribute_pool[:take_count]
        attribute_pool = attribute_pool[take_count:]
        assignments.append(selected)
    
    return assignments


def assign_attributes_stochastic(
    attributes: list[str],
    n_personas: int,
    sample_size: int
) -> list[list[str]]:
    """
    Assign attributes randomly with replacement
    
    Each persona gets a random sample of sample_size attributes.
    Attributes can be reused across personas.
    
    Returns list of attribute lists (one per persona)
    """
    assignments = []
    
    for _ in range(n_personas):
        # Random sample with replacement
        actual_sample_size = min(sample_size, len(attributes))
        if actual_sample_size == 0:
            break
            
        selected = random.sample(attributes, actual_sample_size)
        assignments.append(selected)
    
    return assignments


def update_persona_field(
    session: requests.Session,
    persona_id: str,
    field_name: str,
    attributes: list[str],
    separator: str = ", "
) -> bool:
    """
    Update a persona's field with the given attributes
    
    For most fields, attributes are joined with separator (default: ", ")
    For long_description, you might want to use " " as separator
    
    Returns True if successful, False otherwise
    """
    try:
        # Join attributes with separator
        value = separator.join(attributes)
        
        # Call PUT endpoint
        response = session.put(
            f"{BASE_URL}/personas/{persona_id}",
            json={field_name: value}
        )
        
        return response.status_code in [200, 201]
        
    except Exception as e:
        print(f"    ❌ Exception updating persona: {str(e)}")
        return False


def main():
    """Main script execution"""
    parser = argparse.ArgumentParser(
        description="Assign attributes to personas missing field data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to preview changes
  python assign_persona_attributes.py --file attrs.csv --field general_domain --dry-run
  
  # Sequential assignment (attributes used once)
  python assign_persona_attributes.py --file attrs.csv --field general_domain --sample-size 2
  
  # Stochastic assignment (attributes can repeat)
  python assign_persona_attributes.py --file attrs.csv --field specific_domain --mode stochastic
  
  # Assign to long_description with space separator
  python assign_persona_attributes.py --file desc.csv --field long_description --separator " "
        """
    )
    
    parser.add_argument(
        "--file",
        type=Path,
        required=True,
        help="CSV file containing attributes (comma-separated, can span multiple rows)"
    )
    
    parser.add_argument(
        "--field",
        type=str,
        required=True,
        choices=VALID_FIELDS,
        help="Persona field to populate"
    )
    
    parser.add_argument(
        "--sample-size",
        type=int,
        default=2,
        help="Number of attributes to assign per persona (default: 2)"
    )
    
    parser.add_argument(
        "--mode",
        type=str,
        default="sequential",
        choices=["sequential", "stochastic"],
        help="Assignment mode: sequential (no replacement) or stochastic (with replacement)"
    )
    
    parser.add_argument(
        "--separator",
        type=str,
        default=", ",
        help="Separator to join attributes (default: ', ')"
    )
    
    parser.add_argument(
        "--shuffle",
        action="store_true",
        help="Shuffle attributes before assigning (only affects sequential mode)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=OUTPUT_FILE,
        help=f"Output JSON file for results (default: {OUTPUT_FILE})"
    )
    
    args = parser.parse_args()
    
    # Validate file exists
    if not args.file.exists():
        print(f"❌ Error: File not found: {args.file}")
        return 1
    
    print("\n" + "🎯" * 35)
    print("  PERSONA ATTRIBUTE ASSIGNMENT")
    print("🎯" * 35)
    
    results = AssignmentResults(args.field, args.mode)
    
    try:
        # Step 1: Load attributes
        print_header("Step 1: Loading Attributes")
        print(f"  📖 Reading from: {args.file}")
        attributes = load_attributes(args.file)
        results.set_attributes(len(attributes), str(args.file))
        print(f"  ✅ Loaded {len(attributes)} attributes")
        
        if not attributes:
            print("  ❌ No attributes found in file!")
            return 1
        
        if args.shuffle and args.mode == "sequential":
            random.shuffle(attributes)
            print("  🔀 Shuffled attributes")
        
        # Show first few attributes
        preview = attributes[:5]
        if len(attributes) > 5:
            preview_str = ", ".join(preview) + f"... (+{len(attributes) - 5} more)"
        else:
            preview_str = ", ".join(preview)
        print(f"  📋 Preview: {preview_str}")
        
        # Step 2: Authentication
        print_header("Step 2: Authentication")
        session = get_authenticated_session()
        
        response = session.get(f"{BASE_URL}/users/me")
        if response.status_code == 200:
            user_data = response.json()
            results.set_auth(user_data)
            print(f"  ✅ Authenticated as: {user_data.get('email')}")
        else:
            raise Exception("Failed to get user info")
        
        # Step 3: Fetch personas
        print_header("Step 3: Finding Personas")
        print(f"  🔍 Fetching all personas...")
        all_personas = get_all_personas(session)
        print(f"  📊 Found {len(all_personas)} total personas")
        
        # Filter for missing field
        print(f"  🔍 Filtering for personas missing '{args.field}'...")
        missing_personas = filter_personas_missing_field(all_personas, args.field)
        results.set_personas_found(len(all_personas), len(missing_personas))
        print(f"  🎯 Found {len(missing_personas)} personas missing this field")
        
        if not missing_personas:
            print("\n  ✅ All personas already have this field populated!")
            results.finalize(True)
            results.save(args.output)
            return 0
        
        # Step 4: Generate assignments
        print_header("Step 4: Generating Assignments")
        print(f"  🎲 Mode: {args.mode}")
        print(f"  📏 Sample size: {args.sample_size} attributes per persona")
        
        if args.mode == "sequential":
            assignments = assign_attributes_sequential(
                attributes, 
                len(missing_personas), 
                args.sample_size
            )
        else:  # stochastic
            assignments = assign_attributes_stochastic(
                attributes,
                len(missing_personas),
                args.sample_size
            )
        
        # Check if we generated enough assignments
        if len(assignments) < len(missing_personas):
            print(f"\n  ⚠️  Warning: Only generated {len(assignments)} assignments")
            print(f"     for {len(missing_personas)} personas")
            print(f"     (Ran out of attributes in pool)")
        
        print(f"  ✅ Generated {len(assignments)} assignments")
        
        # Step 5: Apply assignments
        print_header("Step 5: Applying Assignments")
        
        if args.dry_run:
            print("  🧪 DRY RUN MODE - No changes will be made")
        
        success_count = 0
        
        for i, (persona, attrs) in enumerate(zip(missing_personas, assignments), 1):
            print(f"\n  [{i}/{len(assignments)}] {persona['name']}")
            print(f"     Assigning: {args.separator.join(attrs)}")
            
            if args.dry_run:
                print(f"     [DRY RUN - would update persona {persona['id']}]")
                results.add_assignment(persona['name'], persona['id'], attrs, True)
                success_count += 1
            else:
                success = update_persona_field(
                    session,
                    persona['id'],
                    args.field,
                    attrs,
                    args.separator
                )
                
                results.add_assignment(persona['name'], persona['id'], attrs, success)
                
                if success:
                    print(f"     ✅ Updated")
                    success_count += 1
                else:
                    print(f"     ❌ Failed to update")
                    results.add_error(f"Failed to update persona {persona['name']} ({persona['id']})")
        
        # Step 6: Summary
        print_header("Summary")
        print(f"  ⏱️  Duration: {(datetime.now() - results.start_time).total_seconds():.2f} seconds")
        print(f"\n  📊 Statistics:")
        print(f"    • Attributes loaded:     {len(attributes)}")
        print(f"    • Total personas:        {len(all_personas)}")
        print(f"    • Missing field:         {len(missing_personas)}")
        print(f"    • Successfully updated:  {success_count}")
        print(f"    • Failed:                {results.results['personas']['failed']}")
        
        if args.mode == "sequential":
            used = len(assignments) * args.sample_size
            remaining = max(0, len(attributes) - used)
            print(f"    • Attributes used:       {used}")
            print(f"    • Attributes remaining:  {remaining}")
        
        if args.dry_run:
            print("\n  💡 This was a dry run. Use without --dry-run to apply changes.")
        
        # Determine success
        success = (success_count == len(assignments) and results.results['personas']['failed'] == 0)
        
        results.finalize(success)
        results.save(args.output)
        
        if success:
            print("\n" + "🎉" * 35)
            print("  ASSIGNMENT COMPLETED SUCCESSFULLY!")
            print("🎉" * 35)
        else:
            print("\n" + "⚠️ " * 35)
            print("  ASSIGNMENT COMPLETED WITH ERRORS")
            print("⚠️ " * 35)
        
        return 0 if success else 1
        
    except AuthenticationError as e:
        print(f"\n❌ Authentication Error: {e}")
        results.add_error(str(e))
        results.finalize(False)
        results.save(args.output)
        return 1
        
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        results.add_error(str(e))
        results.finalize(False)
        results.save(args.output)
        return 1


if __name__ == "__main__":
    sys.exit(main())
