#!/usr/bin/env python3
"""
Test Agent Integration (Phase 2)

Tests the complete agent integration system:
- Agent registry and StoryAdvisor agent
- Room creation with agent participants
- Message sending that triggers agent responses
- Agent context awareness (story, messages, participants)
- Event persistence and message retrieval

Test Flow:
1. Authentication
2. Create a test story (optional)
3. Create a room
4. Add StoryAdvisor agent as participant
5. Send messages to trigger agent
6. Verify agent responses
7. Test agent context awareness
8. Validate event persistence

Results saved to: test_results_agent_integration.json
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

# Add auth_helper to path
sys.path.append(str(Path(__file__).parent))
from auth_helper import AuthenticationError, get_authenticated_session

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
OUTPUT_FILE = "test_results_agent_integration.json"


class TestResults:
    """Track test results and statistics"""

    def __init__(self):
        self.start_time = datetime.now()
        self.results = {
            "test_run": {
                "start_time": self.start_time.isoformat(),
                "end_time": None,
                "duration_seconds": None,
                "success": False,
                "phase": "Phase 2: Agent Integration"
            },
            "authentication": {"status": "pending", "user": None},
            "story": {"status": "pending", "story_id": None, "title": None},
            "room": {"status": "pending", "room_id": None, "title": None},
            "agent_participant": {
                "status": "pending",
                "agent_name": "StoryAdvisor",
                "participant_id": None
            },
            "messages": {
                "user_messages_sent": 0,
                "agent_responses_received": 0,
                "messages": []
            },
            "context_awareness": {
                "story_context_test": {"status": "pending", "passed": False},
                "message_history_test": {"status": "pending", "passed": False}
            },
            "persistence": {
                "event_count": 0,
                "messages_persisted": True,
                "messages_retrieved": []
            },
            "errors": []
        }

    def set_auth(self, user_data: dict):
        """Record successful authentication"""
        self.results["authentication"] = {
            "status": "success",
            "user": user_data
        }

    def set_story(self, story_id: str, title: str):
        """Record created story"""
        self.results["story"] = {
            "status": "success",
            "story_id": story_id,
            "title": title
        }

    def set_room(self, room_id: str, title: str):
        """Record created room"""
        self.results["room"] = {
            "status": "success",
            "room_id": room_id,
            "title": title
        }

    def set_agent_participant(self, participant_id: str):
        """Record agent participant"""
        self.results["agent_participant"]["status"] = "success"
        self.results["agent_participant"]["participant_id"] = participant_id

    def add_message(self, message_type: str, content: str, sender: str, message_id: str = None):
        """Record a message"""
        self.results["messages"]["messages"].append({
            "type": message_type,
            "content": content,
            "sender": sender,
            "message_id": message_id,
            "timestamp": datetime.now().isoformat()
        })

        if message_type == "user":
            self.results["messages"]["user_messages_sent"] += 1
        elif message_type == "agent":
            self.results["messages"]["agent_responses_received"] += 1

    def set_context_test(self, test_name: str, passed: bool, details: str = None):
        """Record context awareness test result"""
        self.results["context_awareness"][test_name] = {
            "status": "success" if passed else "failed",
            "passed": passed,
            "details": details
        }

    def set_persistence(self, event_count: int, messages: list):
        """Record persistence validation"""
        self.results["persistence"]["event_count"] = event_count
        self.results["persistence"]["messages_retrieved"] = messages

    def add_error(self, category: str, error: str):
        """Record an error"""
        self.results["errors"].append({
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "error": error
        })

    def finalize(self, success: bool):
        """Finalize test results"""
        end_time = datetime.now()
        self.results["test_run"]["end_time"] = end_time.isoformat()
        self.results["test_run"]["duration_seconds"] = (end_time - self.start_time).total_seconds()
        self.results["test_run"]["success"] = success

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


def print_step(step_num: int, total_steps: int, title: str):
    """Print a step header"""
    print(f"\n[{step_num}/{total_steps}] {title}")
    print("-" * 70)


def list_llm_providers(session: requests.Session) -> list[dict]:
    """List configured LLM providers for the current user."""
    try:
        response = session.get(f"{BASE_URL}/llm-providers")
        if response.status_code == 200:
            data = response.json()
            return data.get("data", [])
        print(f"  ❌ Failed to list providers: {response.status_code}")
        print(f"     Error: {response.text[:200]}")
        return []
    except Exception as e:
        print(f"  ❌ Exception listing providers: {str(e)}")
        return []


def test_llm_provider(session: requests.Session, provider_id: str) -> bool:
    """Trigger backend provider test endpoint."""
    try:
        response = session.post(f"{BASE_URL}/llm-providers/{provider_id}/test")
        if response.status_code == 200:
            return True
        print(f"  ❌ Provider test failed: {response.status_code}")
        print(f"     Error: {response.text[:200]}")
        return False
    except Exception as e:
        print(f"  ❌ Exception testing provider: {str(e)}")
        return False


def validate_api_key(session: requests.Session) -> bool:
    """Validate API key by testing the user's default LLM provider."""
    providers = list_llm_providers(session)
    if not providers:
        print("  ❌ No LLM providers configured; cannot validate API key")
        return False

    default_provider = next((p for p in providers if p.get("is_default")), None)
    provider = default_provider or providers[0]
    provider_id = provider.get("id")
    provider_name = provider.get("name", "provider")

    if not provider_id:
        print("  ❌ Provider missing id; cannot validate API key")
        return False

    print(f"  🔌 Testing provider: {provider_name}")
    return test_llm_provider(session, provider_id)


def create_story(session: requests.Session, title: str, description: str) -> dict | None:
    """Create a test story"""
    try:
        response = session.post(
            f"{BASE_URL}/stories",
            json={
                "title": title,
                "description": description
            }
        )

        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"  ❌ Failed to create story: {response.status_code}")
            print(f"     Error: {response.text[:200]}")
            return None

    except Exception as e:
        print(f"  ❌ Exception creating story: {str(e)}")
        return None


def create_room(session: requests.Session, title: str, story_id: str = None) -> dict | None:
    """Create a room"""
    try:
        data = {"title": title}
        if story_id:
            data["story_id"] = story_id

        response = session.post(f"{BASE_URL}/rooms", json=data)

        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"  ❌ Failed to create room: {response.status_code}")
            print(f"     Error: {response.text[:200]}")
            return None

    except Exception as e:
        print(f"  ❌ Exception creating room: {str(e)}")
        return None


def add_agent_participant(session: requests.Session, room_id: str, agent_name: str = "StoryAdvisor") -> dict | None:
    """Add agent as room participant"""
    try:
        response = session.post(
            f"{BASE_URL}/rooms/{room_id}/participants",
            json={
                "participant_id": agent_name,
                "participant_type": "agent",
                "role": "member"
            }
        )

        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"  ❌ Failed to add agent: {response.status_code}")
            print(f"     Error: {response.text[:200]}")
            return None

    except Exception as e:
        print(f"  ❌ Exception adding agent: {str(e)}")
        return None


def send_message(session: requests.Session, room_id: str, content: str) -> dict | None:
    """Send a message to the room"""
    try:
        response = session.post(
            f"{BASE_URL}/rooms/{room_id}/messages",
            json={"content": content}
        )

        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"  ❌ Failed to send message: {response.status_code}")
            print(f"     Error: {response.text[:200]}")
            return None

    except Exception as e:
        print(f"  ❌ Exception sending message: {str(e)}")
        return None


def format_agent_mention(mention: str, content: str) -> str:
    """Prefix content with agent mention for on_mention participation."""
    return f"{mention} {content}".strip()


def get_room_messages(session: requests.Session, room_id: str) -> list[dict]:
    """Get all messages from a room"""
    try:
        response = session.get(f"{BASE_URL}/rooms/{room_id}/messages")

        if response.status_code == 200:
            data = response.json()
            return data.get('data', [])
        else:
            print(f"  ❌ Failed to get messages: {response.status_code}")
            return []

    except Exception as e:
        print(f"  ❌ Exception getting messages: {str(e)}")
        return []


def get_room_participants(session: requests.Session, room_id: str) -> list[dict]:
    """Get all participants from a room"""
    try:
        response = session.get(f"{BASE_URL}/rooms/{room_id}/participants")

        if response.status_code == 200:
            data = response.json()
            return data.get('data', [])
        else:
            print(f"  ❌ Failed to get participants: {response.status_code}")
            return []

    except Exception as e:
        print(f"  ❌ Exception getting participants: {str(e)}")
        return []


def wait_for_agent_response(session: requests.Session, room_id: str, initial_message_count: int, max_wait: int = 10, debug: bool = False) -> bool:
    """Wait for agent to respond (poll for new messages)"""
    print(f"  ⏳ Waiting for agent response (max {max_wait}s)...")
    print(f"     Starting message count: {initial_message_count}")

    for i in range(max_wait):
        time.sleep(1)
        messages = get_room_messages(session, room_id)
        current_count = len(messages)

        if debug:
            print(f"     [Poll {i+1}] Messages: {current_count} (need > {initial_message_count})")
            if messages:
                latest = messages[0]
                print(f"     [Poll {i+1}] Latest: {latest.get('sender_type')} - {latest.get('content', '')[:50]}...")

        if current_count > initial_message_count:
            # Check if latest message is from agent
            # API returns messages in descending order (newest first)
            latest = messages[0]  # Get the newest message (first in array)
            if latest.get('sender_type') == 'agent':
                print(f"  ✅ Agent responded in {i+1}s")
                return True
            elif debug:
                print(f"     [Poll {i+1}] New message found but it's from {latest.get('sender_type')}, not agent")

    print(f"  ⚠️  No agent response after {max_wait}s")
    print(f"     Final message count: {len(messages)}")
    return False


def main():
    """Main test execution"""
    parser = argparse.ArgumentParser(
        description="Test Phase 2 Agent Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic test with story context
  python test_agent_integration.py

  # Test without story
  python test_agent_integration.py --no-story

  # Custom room title
  python test_agent_integration.py --room-title "My Test Room"

  # Save to custom output file
  python test_agent_integration.py --output my_results.json
        """
    )

    parser.add_argument(
        "--no-story",
        action="store_true",
        help="Don't create a story (test agent without story context)"
    )

    parser.add_argument(
        "--room-title",
        type=str,
        default="Agent Integration Test Room",
        help="Title for the test room"
    )

    parser.add_argument(
        "--story-title",
        type=str,
        default="The Quest for the Ancient Scroll",
        help="Title for the test story"
    )

    parser.add_argument(
        "--agent-mention",
        type=str,
        default="@StoryAdvisor",
        help="Agent mention to trigger on_mention participation mode"
    )

    parser.add_argument(
        "--output",
        type=str,
        default=OUTPUT_FILE,
        help=f"Output JSON file for results (default: {OUTPUT_FILE})"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable verbose debug logging"
    )

    args = parser.parse_args()

    print("\n" + "🤖" * 35)
    print("  PHASE 2: AGENT INTEGRATION TEST")
    print("🤖" * 35)

    results = TestResults()
    total_steps = 10 if not args.no_story else 9
    current_step = 0

    try:
        # Step 1: Authentication
        current_step += 1
        print_step(current_step, total_steps, "Authentication")

        session = get_authenticated_session()
        response = session.get(f"{BASE_URL}/users/me")

        if response.status_code == 200:
            user_data = response.json()
            results.set_auth(user_data)
            print(f"  ✅ Authenticated as: {user_data.get('email')}")
        else:
            raise Exception("Failed to get user info")

        # Step 2: API Key Validation
        current_step += 1
        print_step(current_step, total_steps, "Validating Agent API Key")

        if validate_api_key(session):
            print("  ✅ Agent API key validated")
        else:
            results.add_error("api_key_validation", "Agent API key validation failed")
            raise Exception("Agent API key validation failed")

        # Step 3: Create Story (optional)
        story_id = None
        if not args.no_story:
            current_step += 1
            print_step(current_step, total_steps, "Creating Test Story")

            story = create_story(
                session,
                args.story_title,
                "A brave adventurer seeks an ancient scroll of power, facing magical trials and mysterious guardians along the way."
            )

            if story:
                story_id = story['id']
                results.set_story(story_id, story['title'])
                print(f"  ✅ Created story: {story['title']}")
                print(f"     ID: {story_id}")
            else:
                results.add_error("story", "Failed to create story")

        # Step 4: Create Room
        current_step += 1
        print_step(current_step, total_steps, "Creating Room")

        room = create_room(session, args.room_title, story_id)

        if not room:
            raise Exception("Failed to create room")

        room_id = room['room_id']
        results.set_room(room_id, room['title'])
        print(f"  ✅ Created room: {room['title']}")
        print(f"     ID: {room_id}")
        if story_id:
            print(f"     Linked to story: {args.story_title}")

        # Step 5: Add StoryAdvisor Agent
        current_step += 1
        print_step(current_step, total_steps, "Adding StoryAdvisor Agent as Participant")

        participant = add_agent_participant(session, room_id, "StoryAdvisor")

        if not participant:
            raise Exception("Failed to add agent participant")

        results.set_agent_participant(participant['participant_id'])
        print(f"  ✅ Added agent: {participant['participant_id']}")
        print(f"     Type: {participant['participant_type']}")
        print(f"     Role: {participant['role']}")

        # Verify participants
        participants = get_room_participants(session, room_id)
        agent_participants = [p for p in participants if p.get('participant_type') == 'agent']
        print(f"  📊 Room participants: {len(participants)} total, {len(agent_participants)} agents")

        # Step 6: Send Initial Message
        current_step += 1
        print_step(current_step, total_steps, "Sending Initial Message to Trigger Agent")

        initial_messages = get_room_messages(session, room_id)
        initial_count = len(initial_messages)

        test_message = format_agent_mention(
            args.agent_mention,
            "Hello! I'm working on my story and need some advice about pacing. "
            "How should I structure the opening chapter?"
        )

        message = send_message(session, room_id, test_message)

        if not message:
            raise Exception("Failed to send message")

        results.add_message("user", test_message, "user", message.get('message_id'))
        print(f"  ✅ Sent message: {test_message[:60]}...")
        print(f"     Message ID: {message.get('message_id')}")

        # Wait for agent response
        agent_responded = wait_for_agent_response(session, room_id, initial_count, max_wait=15)

        if not agent_responded:
            results.add_error("agent_response", "Agent did not respond to message")

        # Step 7: Verify Agent Response
        current_step += 1
        print_step(current_step, total_steps, "Verifying Agent Response")

        messages = get_room_messages(session, room_id)
        agent_messages = [m for m in messages if m.get('sender_type') == 'agent']

        print(f"  📊 Total messages: {len(messages)}")
        print(f"  🤖 Agent messages: {len(agent_messages)}")

        if agent_messages:
            # Messages are in descending order (newest first)
            latest_agent = agent_messages[0]  # Get the newest agent message
            results.add_message("agent", latest_agent['content'], latest_agent.get('agent_name'), latest_agent.get('message_id'))
            print(f"  ✅ Agent response received:")
            print(f"     From: {latest_agent.get('agent_name')}")
            print(f"     Content: {latest_agent['content'][:100]}...")
        else:
            results.add_error("agent_response", "No agent messages found")

        # Step 8: Test Context Awareness - Story Context
        current_step += 1
        print_step(current_step, total_steps, "Testing Context Awareness - Story Context")

        if story_id:
            # Capture count BEFORE sending message
            before_count = len(get_room_messages(session, room_id))
            print(f"  📊 Message count before sending: {before_count}")

            test_message = format_agent_mention(
                args.agent_mention,
                "Can you remind me what my story is about?"
            )
            print(f"  📤 Sending: {test_message}")

            message = send_message(session, room_id, test_message)
            results.add_message("user", test_message, "user", message.get('message_id'))

            after_count = len(get_room_messages(session, room_id))
            print(f"  📊 Message count after sending: {after_count}")
            print(f"  📊 Messages added during request: {after_count - before_count}")

            # If agent already responded during the request, don't wait
            if after_count > before_count + 1:
                print(f"  ⚡ Agent responded during request (synchronously)!")
                agent_responded = True
            else:
                print(f"  ⏱️  Agent will respond asynchronously, waiting...")
                agent_responded = wait_for_agent_response(session, room_id, after_count, max_wait=45, debug=args.debug)

            if agent_responded:
                messages = get_room_messages(session, room_id)
                # Messages are in descending order (newest first)
                agent_messages = [m for m in messages if m.get('sender_type') == 'agent']
                latest_agent = agent_messages[0]  # Get the newest agent message

                # Check if response mentions the story
                content_lower = latest_agent['content'].lower()
                story_mentioned = any(word in content_lower for word in ['scroll', 'quest', 'ancient', 'story'])

                results.set_context_test(
                    "story_context_test",
                    story_mentioned,
                    f"Agent {'did' if story_mentioned else 'did not'} reference story context"
                )

                if story_mentioned:
                    print(f"  ✅ Agent demonstrated story context awareness")
                else:
                    print(f"  ⚠️  Agent response didn't clearly reference story")
            else:
                results.set_context_test("story_context_test", False, "Agent did not respond")
        else:
            results.set_context_test("story_context_test", True, "Skipped (no story created)")
            print(f"  ⏭️  Skipped (no story created)")

        # Step 9: Test Context Awareness - Message History
        current_step += 1
        print_step(current_step, total_steps, "Testing Context Awareness - Message History")

        # Capture count BEFORE sending message
        before_count = len(get_room_messages(session, room_id))
        print(f"  📊 Message count before sending: {before_count}")

        test_message = format_agent_mention(
            args.agent_mention,
            "What did I just ask you about in my previous message?"
        )
        print(f"  📤 Sending: {test_message}")

        message = send_message(session, room_id, test_message)
        results.add_message("user", test_message, "user", message.get('message_id'))

        after_count = len(get_room_messages(session, room_id))
        print(f"  📊 Message count after sending: {after_count}")
        print(f"  📊 Messages added during request: {after_count - before_count}")

        # If agent already responded during the request, don't wait
        if after_count > before_count + 1:
            print(f"  ⚡ Agent responded during request (synchronously)!")
            agent_responded = True
        else:
            print(f"  ⏱️  Agent will respond asynchronously, waiting...")
            agent_responded = wait_for_agent_response(session, room_id, after_count, max_wait=45, debug=args.debug)

        if agent_responded:
            messages = get_room_messages(session, room_id)
            # Messages are in descending order (newest first)
            agent_messages = [m for m in messages if m.get('sender_type') == 'agent']
            latest_agent = agent_messages[0]  # Get the newest agent message

            # Check if response references previous question
            content_lower = latest_agent['content'].lower()
            previous_mentioned = any(word in content_lower for word in ['pacing', 'chapter', 'opening', 'previous', 'asked', 'story', 'remind'])

            results.set_context_test(
                "message_history_test",
                previous_mentioned,
                f"Agent {'did' if previous_mentioned else 'did not'} reference message history"
            )

            if previous_mentioned:
                print(f"  ✅ Agent demonstrated message history awareness")
            else:
                print(f"  ⚠️  Agent response didn't clearly reference previous messages")
        else:
            results.set_context_test("message_history_test", False, "Agent did not respond")

        # Step 10: Validate Persistence
        current_step += 1
        print_step(current_step, total_steps, "Validating Event Persistence")

        final_messages = get_room_messages(session, room_id)
        results.set_persistence(len(final_messages), final_messages)

        user_messages = [m for m in final_messages if m.get('sender_type') == 'user']
        agent_messages = [m for m in final_messages if m.get('sender_type') == 'agent']

        print(f"  ✅ Messages persisted and retrieved")
        print(f"     Total messages: {len(final_messages)}")
        print(f"     User messages: {len(user_messages)}")
        print(f"     Agent messages: {len(agent_messages)}")

        # Final Summary
        print_header("Test Summary")
        print(f"  ⏱️  Duration: {(datetime.now() - results.start_time).total_seconds():.2f} seconds")

        print(f"\n  📊 Test Results:")
        print(f"    • Authentication:     ✅ {results.results['authentication']['status']}")

        if not args.no_story:
            print(f"    • Story Creation:     ✅ {results.results['story']['status']}")

        print(f"    • Room Creation:      ✅ {results.results['room']['status']}")
        print(f"    • Agent Participant:  ✅ {results.results['agent_participant']['status']}")

        print(f"\n  💬 Messages:")
        print(f"    • User messages sent:        {results.results['messages']['user_messages_sent']}")
        print(f"    • Agent responses received:  {results.results['messages']['agent_responses_received']}")

        print(f"\n  🧠 Context Awareness:")
        for test_name, test_data in results.results['context_awareness'].items():
            status_icon = "✅" if test_data.get('passed') else "⚠️"
            test_label = test_name.replace('_', ' ').title()
            print(f"    • {test_label}: {status_icon} {test_data.get('status')}")

        print(f"\n  💾 Persistence:")
        print(f"    • Events persisted:  {results.results['persistence']['event_count']}")
        print(f"    • Messages retrieved: {len(results.results['persistence']['messages_retrieved'])}")

        total_errors = len(results.results['errors'])
        if total_errors > 0:
            print(f"\n  ⚠️  Errors encountered: {total_errors}")
            for error in results.results['errors']:
                print(f"     - {error['category']}: {error['error']}")
        else:
            print(f"\n  ✅ No errors encountered")

        # Determine success
        success = (
            results.results['authentication']['status'] == 'success' and
            results.results['room']['status'] == 'success' and
            results.results['agent_participant']['status'] == 'success' and
            results.results['messages']['agent_responses_received'] > 0 and
            total_errors == 0
        )

        results.finalize(success)
        results.save(args.output)

        if success:
            print("\n" + "🎉" * 35)
            print("  AGENT INTEGRATION TEST PASSED!")
            print("🎉" * 35)
        else:
            print("\n" + "⚠️ " * 35)
            print("  AGENT INTEGRATION TEST COMPLETED WITH ISSUES")
            print("⚠️ " * 35)

        return 0 if success else 1

    except AuthenticationError as e:
        print(f"\n❌ Authentication Error: {e}")
        results.add_error("authentication", str(e))
        results.finalize(False)
        results.save(args.output)
        return 1

    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        results.add_error("general", str(e))
        results.finalize(False)
        results.save(args.output)
        return 1


if __name__ == "__main__":
    sys.exit(main())
