#!/usr/bin/env python3
"""
M-2: The Cascade Event - Terminal/Technical Markdown Story

This script creates an advanced story demonstrating technical markdown formatting
in the context of a realistic production incident response simulation.

KEY CONCEPTS TESTED:
- Fenced code blocks with language hints (bash, json, yaml, log, python, sql)
- Ordered lists with nested sub-steps (runbook procedures)
- Task lists (GFM checkboxes) for system status tracking
- Inline code for commands, file paths, variables
- Escaped special characters in error messages
- Horizontal rules between terminal sessions
- Tables for system metrics and dashboards

ADVANCED FEATURES:
- Realistic system topology with cascading failures
- Authentic terminal output and error messages
- Dynamic monitoring dashboards as formatted tables
- Time-pressure mechanics through state variables
- Multiple skill-level response paths
- Real-world incident response patterns

STORY STRUCTURE:
- Start: Critical alert - multiple systems failing
- Branch: Database/Network/Application layer investigation
- Cascade: Each fix creates new problems in interconnected systems
- State: Tracks system health, time pressure, skill demonstrations
- 4 endings: Clean Recovery, Partial Fix, Cascading Failure, Heroic Save

=============================================================================

Usage:
    python test_cascade_event_story.py
    python test_cascade_event_story.py --verbose

Output:
    test_results_cascade_event.json
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
RESULTS_FILE = "test_results_cascade_event.json"

# Test results tracking
test_results = {
    "test_suite": "M-2: The Cascade Event",
    "start_time": None,
    "end_time": None,
    "story_id": None,
    "node_ids": {},
    "choice_ids": {},
    "state_variable_ids": {},
    "success": False,
    "errors": []
}


class CascadeEventBuilder:
    """Builds The Cascade Event story demonstrating advanced technical markdown."""

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
        """Build The Cascade Event story."""

        # =====================================================================
        # STEP 1: CREATE THE STORY
        # =====================================================================
        self.log("\n📖 Creating story...")

        story = self.create_story(
            title="The Cascade Event: Production Incident Response",
            description="""STORY: You're the on-call SRE when a cascade of failures hits production.
Every decision affects multiple interconnected systems. Can you restore
service before the business impact becomes catastrophic?""")

# Advanced markdown test story simulating a realistic production incident.

# TECHNICAL MARKDOWN FEATURES TESTED:
# - Fenced code blocks with language hints (bash, json, yaml, log, python, sql)
# - Ordered lists with nested procedural steps
# - Task lists (GFM checkboxes) for system status tracking
# - Inline code for commands, paths, variables, error codes
# - Escaped special characters in error messages and logs
# - Tables for monitoring dashboards and metrics
# - Horizontal rules separating terminal sessions
# """

# SIMULATION FEATURES:
# - Multi-system architecture (web → API → database → cache → monitoring)
# - Cascading failure scenarios based on real outage patterns
# - Authentic terminal output and error messages
# - Time-pressure mechanics and skill-level differentiation
# - Realistic troubleshooting workflows and incident response



# DOMAIN: Modern cloud infrastructure with microservices, containers,
# databases, load balancers, monitoring, and all the complexity that
# makes production incidents genuinely challenging.
        self.story_id = story["id"]
        test_results["story_id"] = self.story_id
        self.log(f"  Created story: {self.story_id}")

        # =====================================================================
        # STEP 2: DEFINE STATE SCHEMA
        # =====================================================================
        self.log("\n📋 Creating state schema...")

        # ---------------------------------------------------------------------
        # System Health Tracking
        # ---------------------------------------------------------------------

        self.state_vars["web_tier"] = self.create_state_variable(
            key="web_tier_status",
            value_type="enum",
            enum_values=["healthy", "degraded", "failing", "down"],
            default_value="failing",
            category="systems",
            description="Status of web tier (load balancers, CDN, frontend)"
        )

        self.state_vars["api_tier"] = self.create_state_variable(
            key="api_tier_status",
            value_type="enum",
            enum_values=["healthy", "degraded", "failing", "down"],
            default_value="failing",
            category="systems",
            description="Status of API tier (microservices, authentication)"
        )

        self.state_vars["database_tier"] = self.create_state_variable(
            key="database_tier_status",
            value_type="enum",
            enum_values=["healthy", "degraded", "failing", "down"],
            default_value="down",
            category="systems",
            description="Status of database tier (primary, replicas, cache)"
        )

        self.state_vars["infrastructure"] = self.create_state_variable(
            key="infrastructure_status",
            value_type="enum",
            enum_values=["healthy", "degraded", "failing", "down"],
            default_value="degraded",
            category="systems",
            description="Status of infrastructure (networking, DNS, monitoring)"
        )

        # ---------------------------------------------------------------------
        # Incident Response Tracking
        # ---------------------------------------------------------------------

        self.state_vars["minutes_elapsed"] = self.create_state_variable(
            key="incident_duration_minutes",
            value_type="number",
            default_value=0,
            category="incident",
            description="Minutes since incident began - affects business impact"
        )

        self.state_vars["business_impact"] = self.create_state_variable(
            key="business_impact_level",
            value_type="enum",
            enum_values=["minimal", "moderate", "severe", "catastrophic"],
            default_value="moderate",
            category="incident",
            description="Current business impact level"
        )

        self.state_vars["customers_affected"] = self.create_state_variable(
            key="estimated_customers_affected",
            value_type="number",
            default_value=50000,
            category="incident",
            description="Estimated number of customers experiencing issues"
        )

        # ---------------------------------------------------------------------
        # Technical Skills and Approach Tracking
        # ---------------------------------------------------------------------

        self.state_vars["investigation_approach"] = self.create_state_variable(
            key="primary_investigation_approach",
            value_type="enum",
            enum_values=["none", "database_first", "network_first", "application_first", "monitoring_first"],
            default_value="none",
            category="approach",
            description="Which system layer was investigated first"
        )

        self.state_vars["commands_run"] = self.create_state_variable(
            key="diagnostic_commands_executed",
            value_type="number",
            default_value=0,
            category="approach",
            description="Count of diagnostic commands executed"
        )

        self.state_vars["fixes_attempted"] = self.create_state_variable(
            key="remediation_actions_taken",
            value_type="number",
            default_value=0,
            category="approach",
            description="Count of remediation actions attempted"
        )

        self.state_vars["skill_level_demonstrated"] = self.create_state_variable(
            key="technical_skill_level_shown",
            value_type="enum",
            enum_values=["junior", "mid", "senior", "principal"],
            default_value="junior",
            category="approach",
            description="Technical skill level demonstrated through choices"
        )

        # ---------------------------------------------------------------------
        # Specific Technical Discoveries
        # ---------------------------------------------------------------------

        self.state_vars["root_cause_identified"] = self.create_state_variable(
            key="identified_root_cause",
            value_type="boolean",
            default_value=False,
            category="technical",
            description="Whether the actual root cause has been identified"
        )

        self.state_vars["cascading_failure_understood"] = self.create_state_variable(
            key="understands_cascade_pattern",
            value_type="boolean",
            default_value=False,
            category="technical",
            description="Whether the cascading failure pattern is understood"
        )

        self.state_vars["monitoring_consulted"] = self.create_state_variable(
            key="checked_monitoring_systems",
            value_type="boolean",
            default_value=False,
            category="technical",
            description="Whether monitoring dashboards were consulted"
        )

        self.state_vars["logs_analyzed"] = self.create_state_variable(
            key="analyzed_application_logs",
            value_type="boolean",
            default_value=False,
            category="technical",
            description="Whether application logs were properly analyzed"
        )

        # ---------------------------------------------------------------------
        # Incident Response Quality
        # ---------------------------------------------------------------------

        self.state_vars["communication_quality"] = self.create_state_variable(
            key="incident_communication_quality",
            value_type="enum",
            enum_values=["poor", "adequate", "good", "excellent"],
            default_value="poor",
            category="response",
            description="Quality of incident communication and updates"
        )

        self.state_vars["rollback_attempted"] = self.create_state_variable(
            key="attempted_rollback_strategy",
            value_type="boolean",
            default_value=False,
            category="response",
            description="Whether rollback was considered/attempted"
        )

        self.state_vars["escalated_appropriately"] = self.create_state_variable(
            key="escalated_to_appropriate_teams",
            value_type="boolean",
            default_value=False,
            category="response",
            description="Whether incident was escalated to appropriate teams"
        )

        self.log(f"  Created {len(self.state_vars)} state variables")

        # =====================================================================
        # STEP 3: CREATE STORY NODES
        # =====================================================================
        self.log("\n📝 Creating story nodes...")

        # ---------------------------------------------------------------------
        # ALERT NODE - The incident begins
        # ---------------------------------------------------------------------

        self.nodes["alert"] = self.create_node(
            title="🚨 CRITICAL: Production Systems Failing",
            content="""# 🚨 CRITICAL: Production Systems Failing

**3:42 AM** - Your phone explodes with alerts. Multiple monitoring systems are screaming.

```log
2024-02-13 03:41:23 [CRITICAL] PagerDuty: P0 - Multiple service failures detected
2024-02-13 03:41:31 [CRITICAL] DataDog: API response time > 30s (SLA: 200ms)  
2024-02-13 03:41:34 [CRITICAL] New Relic: Database connection pool exhausted
2024-02-13 03:41:41 [CRITICAL] AWS CloudWatch: RDS CPU at 98%, connections maxed
2024-02-13 03:41:45 [CRITICAL] Pingdom: 5xx error rate 89% (normal: 0.1%)
```

You grab your laptop and VPN in. The first thing you see makes your stomach drop:

```bash
$ kubectl get pods -n production | head -20
NAME                           READY   STATUS              RESTARTS   AGE
api-gateway-7d9f845b-4xqp8     0/1     CrashLoopBackOff    15         2h
api-gateway-7d9f845b-m2n9k     0/1     CrashLoopBackOff    12         2h
auth-service-5c8bd6-7hjk2      1/1     Running             8          2h
cart-service-6d7b9f-p9m3x      0/1     ImagePullBackOff    0          2h
payment-service-8f2c4a-q5r7t   0/1     CrashLoopBackOff    9          2h
user-service-3a1e8d-w8v9n      1/1     Running             3          2h
notification-service-2b4f6c    0/1     Pending             0          2h
```

**Status Dashboard:**

| System Layer | Status | Response Time | Error Rate | Notes |
|--------------|--------|---------------|------------|-------|
| CDN/Load Balancer | 🔴 FAILING | 45s+ | 89% | Timeouts cascading |
| API Gateway | 🔴 DOWN | N/A | 100% | All pods crashing |
| Microservices | 🟡 DEGRADED | 8-30s | 67% | Mixed states |
| Database | 🔴 CRITICAL | N/A | N/A | Connection limit hit |
| Cache (Redis) | 🟡 SLOW | 2-5s | 12% | Memory pressure |
| Monitoring | 🟢 OK | <1s | 0% | Still functional |

**Initial Assessment Checklist:**

- [x] Incident declared (P0 - Critical)
- [x] On-call engineer responding (you)
- [ ] Incident commander assigned
- [ ] Customer support notified
- [ ] Status page updated
- [ ] War room established

**Customer Impact:** Estimated **50,000 active users** experiencing service degradation or complete failures. Revenue impact approximately **$2,400/minute**.

---

> **⚠️ CRITICAL DECISION POINT**
> 
> Multiple systems are failing simultaneously. You have maybe 5-10 minutes before this becomes a **company-defining incident**.
> 
> **Where do you start your investigation?**

**Previous Similar Incidents:**
```yaml
# From incident retrospectives
2024-01-15: "Database connection leak caused API timeouts"
2023-12-03: "Load balancer config change triggered cascade"  
2023-10-22: "Redis OOM killed cache, overloaded database"
2023-09-08: "Kubernetes resource limits caused pod evictions"
```

**Available Investigation Paths:**

1. **Database Layer** - High CPU, maxed connections suggest DB issues
2. **Network/Infrastructure** - Load balancer timeouts might be root cause  
3. **Application Layer** - Pod crashes could indicate code/config problems
4. **Monitoring Deep Dive** - Get full picture before taking action

*Your next move will determine the investigation path and available solutions.*""",
            is_start=True
        )
        self.debug("Created node: alert")

        # ---------------------------------------------------------------------
        # DATABASE INVESTIGATION NODE
        # ---------------------------------------------------------------------

        self.nodes["database_investigation"] = self.create_node(
            title="🔍 Database Layer Investigation",
            content="""# 🔍 Database Layer Investigation

You decide to start with the database - the high CPU and connection exhaustion are smoking guns.

```bash
# Connect to database monitoring
$ aws rds describe-db-instances --db-instance-identifier prod-primary
{
    "DBInstances": [
        {
            "DBInstanceIdentifier": "prod-primary",
            "DBInstanceStatus": "available", 
            "Engine": "postgres",
            "DBInstanceClass": "db.r5.4xlarge",
            "AllocatedStorage": 1000,
            "ConnectionCount": 200,  # ← MAX CONNECTIONS HIT
            "MaxConnections": 200
        }
    ]
}

# Check current connections
$ psql -h prod-primary.abc123.us-east-1.rds.amazonaws.com -U monitor -d postgres -c "
    SELECT state, count(*) as connections 
    FROM pg_stat_activity 
    WHERE state IS NOT NULL 
    GROUP BY state;"
```

```sql
     state      | connections
----------------+-------------
 active         |          45
 idle in transaction |     155  -- ⚠️ PROBLEM!
 idle           |           0
(3 rows)
```

**🚨 ROOT CAUSE DISCOVERED:**

155 connections are stuck `idle in transaction` - they're holding locks and blocking new connections!

```bash
# Investigate the stuck transactions
$ psql -h prod-primary.abc123.us-east-1.rds.amazonaws.com -U admin -d postgres -c "
    SELECT pid, query_start, state_change, query 
    FROM pg_stat_activity 
    WHERE state = 'idle in transaction' 
    AND state_change < now() - interval '5 minutes' 
    LIMIT 5;"
```

```log
  pid  |          query_start          |         state_change          |                    query
-------+-------------------------------+-------------------------------+----------------------------------------------
 12847 | 2024-02-13 03:35:12.445821+00 | 2024-02-13 03:35:12.467234+00 | UPDATE user_sessions SET last_activity=$1...
 13291 | 2024-02-13 03:35:15.223156+00 | 2024-02-13 03:35:15.445891+00 | BEGIN; SELECT * FROM cart_items WHERE user_id...
 13456 | 2024-02-13 03:35:18.891234+00 | 2024-02-13 03:35:18.923445+00 | UPDATE payment_attempts SET status=$1 WHERE...
 13789 | 2024-02-13 03:35:21.334567+00 | 2024-02-13 03:35:21.445123+00 | BEGIN; INSERT INTO audit_logs (action, user_id...
 14023 | 2024-02-13 03:35:23.445612+00 | 2024-02-13 03:35:23.456789+00 | UPDATE inventory_counts SET reserved=$1 WHERE...
```

**Analysis:** Transactions started ~7 minutes ago and never committed. All are from the `cart-service` and `payment-service` - which explains why those pods are crashing!

**Connection Pool Status:**
```yaml
# Application configuration
database_pools:
  cart-service:
    max_connections: 50    # Each pod can hold up to 50 connections
    idle_timeout: 300s     # Should close idle connections after 5 minutes
    pool_timeout: 30s      # ← This is the problem!
  payment-service:  
    max_connections: 40
    idle_timeout: 300s
    pool_timeout: 30s      # ← Also problematic
```

**The Cascade Pattern:**
1. **3:35 AM** - Some transaction started and got stuck (unknown root cause)
2. **3:36-3:40 AM** - More transactions piled up, couldn't get connections
3. **3:40 AM** - Connection pool exhausted, new requests time out after 30s
4. **3:41 AM** - App pods start crashing due to database timeouts
5. **3:41-3:42 AM** - Load balancer sees failed health checks, cascades errors

---

**⚡ IMMEDIATE ACTION REQUIRED**

**Diagnostic Commands Available:**
```bash
# Option 1: Kill stuck connections (DANGEROUS - might lose data)
SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
WHERE state = 'idle in transaction' AND state_change < now() - interval '5 minutes';

# Option 2: Check for blocking locks (safer investigation)  
SELECT blocked_locks.pid AS blocked_pid, blocked_activity.query AS blocked_query,
       blocking_locks.pid AS blocking_pid, blocking_activity.query AS blocking_query
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype...

# Option 3: Restart specific application pods (might help, might make worse)
kubectl delete pods -n production -l app=cart-service
kubectl delete pods -n production -l app=payment-service

# Option 4: Scale up database connections (temporary relief)
aws rds modify-db-instance --db-instance-identifier prod-primary --max-connections 400
```

**Current Status Update:**
- **Minutes Elapsed:** 8 minutes
- **Business Impact:** SEVERE ($19,200 lost revenue so far)  
- **Customer Impact:** 50,000+ users affected
- **Root Cause:** Database connection exhaustion due to stuck transactions
- **Immediate Risk:** Data loss if connections are forcibly killed

**What's your next move?**""",
        )
        self.debug("Created node: database_investigation")

        # ---------------------------------------------------------------------
        # NETWORK INVESTIGATION NODE  
        # ---------------------------------------------------------------------

        self.nodes["network_investigation"] = self.create_node(
            title="🌐 Network & Infrastructure Investigation",
            content="""# 🌐 Network & Infrastructure Investigation

You decide to start with the network layer - those load balancer timeouts could be the root cause cascading down.

```bash
# Check load balancer health
$ aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:us-east-1:123456789:targetgroup/prod-api-tg/abc123def456
{
    "TargetHealthDescriptions": [
        {
            "Target": {"Id": "10.0.1.45", "Port": 8080},
            "HealthCheckPort": "8080", 
            "TargetHealth": {
                "State": "unhealthy",
                "Reason": "Target.Timeout",
                "Description": "Health check timeout after 30 seconds"
            }
        },
        {
            "Target": {"Id": "10.0.1.67", "Port": 8080},
            "TargetHealth": {
                "State": "unhealthy", 
                "Reason": "Target.FailedHealthChecks",
                "Description": "Health check failed with HTTP 503"
            }
        }
    ]
}
```

**All API targets are unhealthy!** But let's dig deeper into the network path:

```bash
# Check DNS resolution
$ dig api.production.company.com
;; ANSWER SECTION:
api.production.company.com. 60 IN CNAME prod-alb-123456789.us-east-1.elb.amazonaws.com.
prod-alb-123456789.us-east-1.elb.amazonaws.com. 60 IN A 52.123.45.67
prod-alb-123456789.us-east-1.elb.amazonaws.com. 60 IN A 52.123.45.68

# DNS looks fine. Check load balancer metrics
$ aws logs filter-log-events --log-group-name /aws/elasticloadbalancing/application/prod-alb \
  --start-time $(date -d "10 minutes ago" +%s)000 --filter-pattern "[timestamp, request_id, client_ip = \"ERROR\"]"
```

```log
2024-02-13T03:35:12.123Z request_id=abc-123 client:port=198.51.100.45:54321 target:port=10.0.1.45:8080 request_processing_time=0.001 target_processing_time=30.000 response_processing_time=0.001 elb_status_code=504 target_status_code=- received_bytes=0 sent_bytes=354 "GET https://api.production.company.com/health HTTP/1.1" "ELB-HealthChecker/2.0" - - arn:aws:elasticloadbalancing:us-east-1:123456789:targetgroup/prod-api-tg/abc123def456 "Root=1-abc123-def456" "-" "-" 0 2024-02-13T03:35:12.123Z "forward" "-" "-" "-" "-"

2024-02-13T03:35:15.456Z request_id=def-456 client:port=203.0.113.12:43210 target:port=10.0.1.67:8080 request_processing_time=0.002 target_processing_time=29.999 response_processing_time=0.001 elb_status_code=504 target_status_code=- received_bytes=0 sent_bytes=354 "POST https://api.production.company.com/api/v1/orders HTTP/1.1" "Mozilla/5.0..." - - arn:aws:elasticloadbalancing:us-east-1:123456789:targetgroup/prod-api-tg/abc123def456 "Root=1-def456-ghi789" "-" "-" 0 2024-02-13T03:35:15.456Z "forward" "-" "-" "-" "-"
```

**Pattern Identified:** `target_processing_time=30.000` - requests are timing out at exactly 30 seconds.

```bash
# Check what's happening at the pod level
$ kubectl logs -n production deployment/api-gateway --tail=50 --since=10m
```

```log
2024-02-13T03:35:12.123Z [ERROR] Database connection timeout after 30000ms
2024-02-13T03:35:12.124Z [ERROR] Failed to acquire connection from pool: org.postgresql.util.PSQLException: Connection refused
2024-02-13T03:35:15.456Z [INFO]  Health check endpoint /health called
2024-02-13T03:35:15.457Z [ERROR] Database health check failed: connection timeout  
2024-02-13T03:35:15.458Z [ERROR] Returning HTTP 503 - service unavailable
2024-02-13T03:35:18.789Z [WARN]  Connection pool exhausted: 0 available, 50 in use, 200 pending
2024-02-13T03:35:21.012Z [ERROR] Database connection timeout after 30000ms
2024-02-13T03:35:21.013Z [FATAL] Unable to service requests - killing process
```

**🎯 NETWORK LAYER ANALYSIS REVEALS:**

The network infrastructure is **healthy** - DNS, load balancers, and routing all work fine. The `504 Gateway Timeout` errors are happening because:

1. **API pods can't connect to database** (connection refused/timeout)
2. **Health checks fail** → Load balancer marks targets unhealthy  
3. **Load balancer returns 504** → Appears like network issue to customers

**Infrastructure Metrics Dashboard:**
```yaml
AWS_Infrastructure:
  Load_Balancer:
    status: "healthy"  
    request_rate: "2,341 req/sec → 45 req/sec"  # Dropped due to failures
    error_rate: "89% (504 Gateway Timeout)"
    response_time: "30.0s (timeout threshold)"
  
  DNS:
    status: "healthy"
    resolution_time: "12ms avg"
    failure_rate: "0%"
  
  Networking:
    vpc_connectivity: "healthy" 
    security_groups: "allowing required traffic"
    nat_gateway: "healthy"
    internet_gateway: "healthy"

Kubernetes_Infrastructure:
  cluster_health: "healthy"
  node_utilization: "CPU: 45%, Memory: 62%"  
  pod_network: "healthy"
  service_mesh: "degraded - endpoints failing"
```

**Next Level Investigation:**
```bash
# Check database connectivity from application layer
$ kubectl exec -n production deployment/api-gateway -- nc -zv prod-primary.abc123.us-east-1.rds.amazonaws.com 5432
prod-primary.abc123.us-east-1.rds.amazonaws.com (10.0.2.123:5432) : Connection refused

# Check if database security groups allow connections  
$ aws ec2 describe-security-groups --group-ids sg-abc123def456
```

```json
{
    "SecurityGroups": [{
        "GroupId": "sg-abc123def456",
        "GroupName": "prod-database-sg", 
        "InboundRules": [
            {
                "IpProtocol": "tcp",
                "FromPort": 5432,
                "ToPort": 5432,
                "UserIdGroupPairs": [{"GroupId": "sg-def456ghi789"}]
            }
        ]
    }]
}
```

**Security groups are correct.** The problem isn't network connectivity - it's **database availability**.

---

**⚡ REFINED DIAGNOSIS**

The network investigation reveals that the **root cause is database layer failure**, not network issues. The cascade works like this:

1. **Database becomes unavailable** (connection limits/performance)
2. **API pods can't connect** → Health checks fail → Pods crash
3. **Load balancer sees unhealthy targets** → Returns 504 errors  
4. **Customers see "network timeouts"** but it's really database

**Immediate Actions Available:**
```bash
# Option 1: Focus on database layer (recommended)
# → Investigate database connection limits and performance

# Option 2: Scale out application layer (temporary relief)  
kubectl scale deployment/api-gateway --replicas=10 -n production

# Option 3: Implement circuit breakers (prevents cascade but doesn't fix root cause)
kubectl patch deployment/api-gateway -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","env":[{"name":"DB_CIRCUIT_BREAKER","value":"true"}]}]}}}}'

# Option 4: Bypass database for read-only endpoints (emergency mode)
kubectl set env deployment/api-gateway EMERGENCY_READ_ONLY_MODE=true -n production
```

**Status:** 12 minutes elapsed, **$28,800** revenue impact, database investigation now critical priority.""",
        )
        self.debug("Created node: network_investigation")

        # ---------------------------------------------------------------------
        # APPLICATION INVESTIGATION NODE
        # ---------------------------------------------------------------------

        self.nodes["application_investigation"] = self.create_node(
            title="💻 Application Layer Investigation", 
            content="""# 💻 Application Layer Investigation

You decide to dive into the application layer first - those `CrashLoopBackOff` pods are screaming for attention.

```bash
# Get detailed pod status and events
$ kubectl describe pods -n production -l app=api-gateway
```

```yaml
Name:         api-gateway-7d9f845b-4xqp8
Status:       Failed
Reason:       Error
Exit Code:    1
Restart Count: 16

Events:
  Type    Reason   Age   From               Message
  ----    ------   ----  ----               -------
  Normal  Pulling  45s   kubelet            Pulling image "api-gateway:v2.3.1"
  Normal  Pulled   42s   kubelet            Successfully pulled image
  Normal  Created  42s   kubelet            Created container api
  Normal  Started  42s   kubelet            Started container api  
  Warning Failed   12s   kubelet            Container api exited with code 1
  Normal  Killing  12s   kubelet            Killing container with id abc123:Container failed liveness probe
```

**Application Logs Analysis:**
```bash  
$ kubectl logs -n production api-gateway-7d9f845b-4xqp8 --previous
```

```log
2024-02-13T03:41:45.123Z [INFO]  Starting API Gateway v2.3.1
2024-02-13T03:41:45.234Z [INFO]  Loading configuration from /app/config/production.yaml
2024-02-13T03:41:45.345Z [INFO]  Initializing database connection pool...
2024-02-13T03:41:45.456Z [INFO]  Database pool: max=50, initial=10, timeout=30s
2024-02-13T03:41:45.567Z [ERROR] Failed to initialize database pool: org.postgresql.util.PSQLException: FATAL: remaining connection slots are reserved for non-replication superuser connections
2024-02-13T03:41:45.567Z [ERROR] Database pool initialization failed after 30s timeout
2024-02-13T03:41:45.568Z [FATAL] Cannot start application without database connectivity
2024-02-13T03:41:45.568Z [FATAL] Application startup failed - exiting with code 1
```

**🔍 Deep Dive into Application Configuration:**

```bash
# Check current application configuration
$ kubectl get configmap -n production app-config -o yaml
```

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: production
data:
  database.yaml: |
    database:
      host: "prod-primary.abc123.us-east-1.rds.amazonaws.com"
      port: 5432
      database: "production"
      username: "app_user"
      password: "${DB_PASSWORD}"  # From secret
      pool:
        max_size: 50              # ← Each pod wants 50 connections
        min_size: 10
        acquire_timeout: 30000    # 30 seconds
        idle_timeout: 300000      # 5 minutes  
        max_lifetime: 1800000     # 30 minutes
  application.yaml: |
    server:
      port: 8080
      health_check_timeout: 10s
    features:
      circuit_breaker_enabled: false  # ← Problem!
      retry_enabled: true
      retry_attempts: 3
      retry_delay: 1000
```

**🚨 APPLICATION ARCHITECTURE PROBLEMS IDENTIFIED:**

```bash
# Check how many application pods are trying to connect
$ kubectl get pods -n production -o wide | grep -E "(api-gateway|cart-service|payment-service|user-service)"
```

```log
NAME                           READY   STATUS    RESTARTS   NODE
api-gateway-7d9f845b-4xqp8     0/1     Error     16         node-1
api-gateway-7d9f845b-m2n9k     0/1     Error     12         node-2  
api-gateway-7d9f845b-x8w3v     0/1     Error     8          node-3
cart-service-6d7b9f-p9m3x      0/1     Error     11         node-1
cart-service-6d7b9f-q4r7t      0/1     Error     9          node-2
payment-service-8f2c4a-q5r7t   0/1     Error     14         node-1
payment-service-8f2c4a-w9v2x   0/1     Error     7          node-3
user-service-3a1e8d-w8v9n      1/1     Running   3          node-2  # ← Only one working!
```

**Connection Math Problem:**
```yaml
# Database connections being requested:
Database_Max_Connections: 200

Attempted_Connections:
  api_gateway_pods: 3 × 50 = 150
  cart_service_pods: 2 × 40 = 80  
  payment_service_pods: 2 × 35 = 70
  user_service_pods: 1 × 30 = 30
  other_services: ~50
  
Total_Attempted: 380 connections
Available: 200 connections
Shortage: 180 connections  # ← MASSIVE OVERSUBSCRIPTION
```

**Application Code Analysis:**
```bash
# Check the application startup sequence
$ kubectl exec -n production user-service-3a1e8d-w8v9n -- cat /app/src/main/java/DatabaseConnectionManager.java | head -30
```

```java
@Component
public class DatabaseConnectionManager {
    
    @Value("${database.pool.max_size:50}")
    private int maxPoolSize;
    
    @Value("${database.pool.acquire_timeout:30000}")  
    private int acquireTimeoutMs;
    
    @PostConstruct
    public void initializePool() {
        HikariConfig config = new HikariConfig();
        config.setJdbcUrl(databaseUrl);
        config.setUsername(username);
        config.setPassword(password);
        config.setMaximumPoolSize(maxPoolSize);        // ← Each pod tries to get max immediately
        config.setMinimumIdle(maxPoolSize / 5);        // ← Starts with 20% of max  
        config.setConnectionTimeout(acquireTimeoutMs); // ← 30s timeout
        config.setIdleTimeout(300000);                 // 5 minutes
        config.setLeakDetectionThreshold(60000);       // 1 minute leak detection
        
        // ⚠️ CRITICAL FLAW: No circuit breaker, no graceful degradation
        this.dataSource = new HikariDataSource(config);
        
        // Test connection on startup - BLOCKS until success or timeout
        try (Connection conn = dataSource.getConnection()) {
            // If this fails, application won't start
        }
    }
}
```

**🎯 ROOT CAUSE IN APPLICATION LAYER:**

1. **Oversubscription:** Apps configured for 380 total connections, DB only has 200
2. **No Circuit Breaker:** Apps crash instead of gracefully degrading  
3. **Immediate Connection Demand:** All pods try to establish max connections on startup
4. **No Fallback Strategy:** Failed database = failed application startup
5. **Cascade Effect:** Connection exhaustion → startup failures → more restarts → more connection attempts

**Runtime Metrics from Working Pod:**
```bash
$ kubectl exec -n production user-service-3a1e8d-w8v9n -- curl -s localhost:8080/actuator/metrics/hikari.connections
```

```json
{
  "name": "hikari.connections", 
  "measurements": [
    {"statistic": "VALUE", "value": 30.0}
  ],
  "availableTags": [
    {"tag": "pool", "values": ["HikariPool-1"]}
  ]
}

# This service is using all 30 of its allowed connections!
```

---

**⚡ APPLICATION-FOCUSED SOLUTIONS:**

**Immediate Fixes:**
```bash
# Option 1: Reduce connection pool sizes (quick fix)
kubectl patch configmap app-config -n production --type merge -p '{
  "data": {
    "database.yaml": "database:\n  pool:\n    max_size: 15\n    min_size: 3\n    acquire_timeout: 5000"
  }
}'

# Option 2: Enable circuit breaker mode (prevent cascading failures)
kubectl set env deployment/api-gateway CIRCUIT_BREAKER_ENABLED=true -n production
kubectl set env deployment/cart-service CIRCUIT_BREAKER_ENABLED=true -n production  
kubectl set env deployment/payment-service CIRCUIT_BREAKER_ENABLED=true -n production

# Option 3: Implement graceful degradation 
kubectl set env deployment/api-gateway DEGRADED_MODE_ENABLED=true -n production

# Option 4: Scale down pod replicas temporarily (reduce connection demand)
kubectl scale deployment/api-gateway --replicas=1 -n production
kubectl scale deployment/cart-service --replicas=1 -n production
kubectl scale deployment/payment-service --replicas=1 -n production
```

**Architectural Improvements:**
```yaml
# Better connection pool configuration
database:
  pool:
    max_size: 15          # Reduced from 50  
    min_size: 2           # Start small
    acquire_timeout: 5000 # Faster timeout
    validation_timeout: 3000
    
# Circuit breaker configuration  
resilience:
  circuit_breaker:
    failure_rate_threshold: 50
    wait_duration_in_open_state: 30s
    sliding_window_size: 100
```

**Status Update:** 15 minutes elapsed, $36,000 revenue impact. Application layer analysis complete - database connection oversubscription identified as primary issue.""",
        )
        self.debug("Created node: application_investigation")

        # ---------------------------------------------------------------------
        # MONITORING INVESTIGATION NODE
        # ---------------------------------------------------------------------

        self.nodes["monitoring_investigation"] = self.create_node(
            title="📊 Monitoring Deep Dive",
            content="""# 📊 Monitoring Deep Dive

You decide to get the complete picture before taking any action. Smart move - let's see what the monitoring systems tell us.

**Grafana Dashboard - System Overview (Last 15 minutes):**

```log
Time Range: 03:27 - 03:42 (15 minutes)
Refresh: 10s | Auto-refresh: ON
```

**Database Metrics:**
```yaml
PostgreSQL_Primary:
  cpu_utilization: 
    - "03:27-03:35": "45-60% (normal)"
    - "03:35-03:42": "95-98% (critical)"
  memory_usage: "78% (elevated but acceptable)"
  active_connections:
    - "03:27-03:35": "45-80 (normal peak)"  
    - "03:35-03:42": "200/200 (maxed out)"
  connection_wait_queue:
    - "03:27-03:35": "0-5 (normal)"
    - "03:35-03:42": "150-300 (backing up)"
  slow_query_count:
    - "03:27-03:35": "2-5/min (normal)"
    - "03:35-03:42": "0/min (no queries completing)"
```

**Application Metrics:**
```bash  
# Prometheus query results
$ curl -s 'http://prometheus:9090/api/v1/query?query=rate(http_requests_total[5m])' | jq
```

```json
{
  "data": {
    "result": [
      {
        "metric": {"service": "api-gateway", "status": "200"},
        "value": [1676258522, "245.67"]
      },
      {
        "metric": {"service": "api-gateway", "status": "503"}, 
        "value": [1676258522, "1847.23"]
      },
      {
        "metric": {"service": "api-gateway", "status": "504"},
        "value": [1676258522, "892.45"]  
      }
    ]
  }
}
```

**HTTP Status Code Breakdown:**
- `200 OK`: 245/sec (normal: 2,000/sec) - **88% drop in successful requests**
- `503 Service Unavailable`: 1,847/sec - **Pod health check failures**  
- `504 Gateway Timeout`: 892/sec - **Database connection timeouts**

**Container Resource Usage:**
```log
Pod Resource Metrics (kubectl top pods):
NAME                          CPU      MEMORY    
api-gateway-7d9f845b-4xqp8    0m       0Mi       # Pod is down
api-gateway-7d9f845b-m2n9k    0m       0Mi       # Pod is down  
cart-service-6d7b9f-p9m3x     0m       0Mi       # Pod is down
user-service-3a1e8d-w8v9n     89m      234Mi     # Only working pod, high CPU
payment-service-8f2c4a-q5r7t  0m       0Mi       # Pod is down
```

**Infrastructure Monitoring - AWS CloudWatch:**

```bash
# RDS Performance Insights
$ aws rds describe-db-log-files --db-instance-identifier prod-primary
```

```json
{
  "DescribeDBLogFiles": [
    {
      "LogFileName": "error/postgresql.log.2024-02-13-03", 
      "LastWritten": 1676258522000,
      "Size": 45678
    }
  ]
}
```

```bash  
$ aws logs get-log-events --log-group-name /aws/rds/instance/prod-primary/postgresql \
  --log-stream-name postgresql.log.2024-02-13-03 --start-time 1676257500000
```

```log
2024-02-13 03:35:12 UTC [23847]: [1-1] user=app_user,db=production,app=cart-service FATAL: remaining connection slots are reserved for non-replication superuser connections
2024-02-13 03:35:15 UTC [23848]: [1-1] user=app_user,db=production,app=api-gateway FATAL: remaining connection slots are reserved for non-replication superuser connections  
2024-02-13 03:35:18 UTC [23849]: [1-1] user=app_user,db=production,app=payment-service FATAL: remaining connection slots are reserved for non-replication superuser connections
2024-02-13 03:35:21 UTC [WARNING]: connection slots exhausted, 247 attempted connections rejected
2024-02-13 03:35:24 UTC [ERROR]: too many connections for role "app_user"
```

**🎯 COMPREHENSIVE MONITORING ANALYSIS:**

**Timeline Reconstruction:**
```yaml
03:27_AM: "System operating normally"
  - Database: 60 connections, 45% CPU
  - Applications: 2000 req/sec, <1% errors  
  - Infrastructure: All green

03:35_AM: "Initial connection spike detected"  
  - Database connections jump from 60 → 150
  - CPU starts climbing 45% → 75%
  - First connection rejections appear

03:35_30s: "Cascade begins"
  - Database maxes out at 200 connections
  - Applications can't get new connections
  - Pods start failing health checks

03:36_AM: "Full cascade in effect"
  - All pods crashing due to database connectivity
  - Load balancer returns 504 errors
  - Error rate jumps to 89%

03:42_AM: "Current state - total service disruption"
  - Only 1 working pod out of 8 total
  - Database completely overloaded
  - Revenue impact: $36,000 and climbing
```

**Distributed Tracing Insights:**
```bash
# Jaeger traces for failed requests  
$ curl -s "http://jaeger:14268/api/traces?service=api-gateway&start=$(date -d '10 minutes ago' +%s)000000&limit=10"
```

```json
{
  "traces": [{
    "traceID": "abc123def456",
    "spans": [
      {
        "operationName": "HTTP GET /api/v1/orders",
        "duration": 30000000,
        "tags": [
          {"key": "error", "value": true},
          {"key": "http.status_code", "value": 503},
          {"key": "error.message", "value": "Database connection timeout"}
        ]
      }
    ]
  }]
}
```

**Business Impact Metrics:**
```yaml
Revenue_Impact:
  time_elapsed: "15 minutes"  
  revenue_lost: "$36,000"
  customers_affected: "52,000 active users"
  conversion_impact: "89% of purchase attempts failing"
  
SLA_Breaches:
  api_response_time: "BREACH - 30s vs 200ms SLA"
  availability: "BREACH - 11% vs 99.9% SLA"  
  error_rate: "BREACH - 89% vs 0.1% SLA"

Customer_Experience:
  support_tickets: "+347 in last 10 minutes"
  social_media_mentions: "+23 negative mentions"
  app_store_rating_drop: "4.8 → 4.2 stars (projected)"
```

---

**📈 MONITORING-DRIVEN INSIGHTS:**

**Root Cause:** Database connection exhaustion at **03:35 AM** triggered cascading failure across all application services.

**Contributing Factors:**
1. **Resource Oversubscription:** 380 attempted connections vs 200 available
2. **Lack of Circuit Breakers:** Failed connections cause app crashes instead of graceful degradation  
3. **No Connection Pooling Strategy:** Each pod tries to establish maximum connections immediately
4. **Monitoring Alerting Gaps:** Connection exhaustion should have alerted earlier

**Immediate Monitoring-Guided Actions:**
```bash
# Option 1: Database-focused fix (targets root cause)
# Increase connection limit temporarily
aws rds modify-db-instance --db-instance-identifier prod-primary --max-connections 400 --apply-immediately

# Option 2: Application-focused fix (prevents cascade)  
# Reduce connection pool sizes across all services
kubectl patch configmap app-config --type merge -p '{"data":{"database.yaml":"pool: {max_size: 10}"}}'

# Option 3: Infrastructure scaling (buys time)
# Scale up database instance class
aws rds modify-db-instance --db-instance-identifier prod-primary --db-instance-class db.r5.8xlarge --apply-immediately

# Option 4: Emergency degradation (preserve critical functions)
# Enable read-only mode for non-critical services
kubectl set env deployment/cart-service EMERGENCY_READ_ONLY_MODE=true
kubectl set env deployment/api-gateway EMERGENCY_READ_ONLY_MODE=true
```

**Monitoring shows this is a** ***classic database connection exhaustion cascade*** **- textbook incident response scenario.**

**What's your action plan?**""",
        )
        self.debug("Created node: monitoring_investigation")

        # ---------------------------------------------------------------------
        # ENDING NODES - Different Resolution Outcomes
        # ---------------------------------------------------------------------

        # ENDING A: Clean Recovery
        self.nodes["ending_clean_recovery"] = self.create_node(
            title="✅ Clean Recovery Achieved",
            content="""# ✅ Clean Recovery Achieved

**FINAL STATUS: INCIDENT RESOLVED**
**Total Duration: 22 minutes**
**Business Impact: Moderate ($52,800 revenue impact)**

---

## 🎯 Incident Resolution Summary

Your systematic approach and quick decision-making led to a **clean recovery** with minimal lasting impact.

**Timeline of Resolution:**

```log
03:42 AM: Incident response initiated
03:45 AM: Root cause identified (database connection exhaustion) 
03:47 AM: Connection pool configurations reduced across all services
03:49 AM: Database max connections temporarily increased to 300
03:52 AM: First pods successfully restarted
03:55 AM: Load balancer health checks passing
03:58 AM: Traffic restored to 50% of normal levels
04:02 AM: Full service restoration achieved
04:04 AM: All monitoring metrics back to green
```

**Key Actions That Led to Success:**

1. **🔍 Proper Investigation**: You identified the root cause through systematic analysis
2. **🎯 Targeted Fix**: Addressed connection pool oversubscription directly  
3. **⚡ Quick Implementation**: Applied fixes while monitoring impact
4. **📊 Data-Driven Decisions**: Used monitoring to validate recovery
5. **🛡️ Preventive Measures**: Implemented circuit breakers to prevent future cascades

**Final System Status:**
```yaml
Database_Tier:
  status: "🟢 HEALTHY"
  connections: "87/300 (29% utilization)" 
  cpu: "45% (normal operating range)"
  response_time: "15ms average"

Application_Tier:  
  status: "🟢 HEALTHY"
  pods_running: "8/8 (100%)"
  error_rate: "0.1% (within SLA)"
  response_time: "180ms average (within 200ms SLA)"

Infrastructure:
  status: "🟢 HEALTHY"  
  load_balancer: "All targets healthy"
  kubernetes: "All deployments stable"
  monitoring: "All alerts cleared"
```

---

## 🎓 Technical Skills Demonstrated

**Senior-Level Incident Response:**
- ✅ Systematic troubleshooting methodology
- ✅ Root cause analysis under pressure  
- ✅ Understanding of system dependencies
- ✅ Effective use of monitoring and observability
- ✅ Risk assessment of potential fixes
- ✅ Clean implementation with rollback planning

**Specific Technical Competencies:**
- Database connection pool management
- Kubernetes pod lifecycle and health checks
- Load balancer behavior and health routing
- Application configuration management
- Circuit breaker and resilience patterns
- Monitoring and alerting interpretation

**Code Changes Applied:**
```yaml
# database.yaml - Connection pool optimization
database:
  pool:
    max_size: 15        # Reduced from 50
    min_size: 3         # Reduced from 10  
    acquire_timeout: 5000ms  # Reduced from 30000ms
    validation_timeout: 3000ms

# resilience.yaml - Circuit breaker enabled
resilience:
  circuit_breaker:
    enabled: true
    failure_rate_threshold: 60
    wait_duration_in_open_state: 30s
    sliding_window_size: 10
```

```bash
# Infrastructure changes
aws rds modify-db-instance \
  --db-instance-identifier prod-primary \
  --max-connections 300 \
  --apply-immediately

# All changes applied through proper CI/CD pipeline for audit trail
```

---

## 📊 Post-Incident Metrics

**Business Recovery:**
- Service restored in **22 minutes** (well under 1-hour SLA)
- Revenue impact contained to **$52,800** (vs projected $200K+ for longer outage)
- Customer impact: **52,000** users affected, **average 8 minutes** of disruption
- No data loss or corruption

**Technical Recovery:**  
- **100% of systems** back to healthy status
- **0% ongoing error rate** 
- **All SLAs restored** to normal operating parameters
- **Monitoring confidence** restored with new alerting thresholds

**Learning Outcomes:**
- Connection pool sizing calculations need regular review as scale grows
- Circuit breakers should be enabled by default in production
- Database connection monitoring alerts need lower thresholds  
- Capacity planning should include connection pool overhead

---

## 🏆 Incident Response Excellence

You demonstrated **Principal Engineer** level incident response skills:

**✅ Exceptional Performance:**
- Stayed calm under extreme pressure ($2,400/minute revenue impact)  
- Made data-driven decisions using multiple monitoring sources
- Identified root cause quickly through systematic elimination
- Applied targeted fixes without creating additional problems
- Monitored recovery carefully to ensure stability

**✅ Systems Thinking:**
- Understood the cascade pattern from database → application → load balancer
- Recognized the importance of connection pool arithmetic
- Balanced immediate fixes vs long-term architectural improvements
- Considered business impact alongside technical metrics

**✅ Technical Leadership:**
- Applied proven incident response methodologies
- Used appropriate tooling (kubectl, AWS CLI, monitoring dashboards)
- Made appropriate risk/benefit tradeoffs under pressure
- Documented changes for post-incident review

**Result:** You've **saved the company** from a potentially catastrophic outage. The clean recovery with minimal business impact showcases exactly the kind of technical leadership that defines senior engineering talent.

---

## 🎭 Markdown Technical Showcase

This incident simulation demonstrated every advanced markdown feature:

**✅ Technical Code Blocks:**
- `bash` shell commands with authentic output
- `json`, `yaml`, `log` formatted data with proper syntax  
- `sql` queries with realistic database responses
- `java` application code showing actual bugs

**✅ Advanced Formatting:**
- Nested ordered lists for procedural steps
- Task lists (checkboxes) for system status tracking
- Tables for metrics dashboards and comparisons  
- Inline code for commands, variables, file paths
- Escaped special characters in error messages
- Horizontal rules for logical section separation

**✅ Authentic Technical Content:**
- Real Kubernetes commands and output
- Actual AWS CLI usage and responses
- Legitimate database queries and connection management
- Proper monitoring and observability practices
- Realistic incident response workflows

You've proven the system can handle **production-grade technical documentation** with full markdown formatting support.

**🎉 CONGRATULATIONS - INCIDENT COMMANDER CERTIFICATION EARNED! 🎉**""",
            is_end=True
        )
        self.debug("Created node: ending_clean_recovery")

        # ENDING B: Partial Fix  
        self.nodes["ending_partial_fix"] = self.create_node(
            title="⚠️ Partial Recovery - System Limping",
            content="""# ⚠️ Partial Recovery - System Limping

**FINAL STATUS: INCIDENT ONGOING - DEGRADED SERVICE**
**Duration: 35 minutes and counting**
**Business Impact: Severe ($84,000 revenue impact, still growing)**

---

## 🔄 Current System Status

Your fixes helped, but the system is still struggling. You've stopped the bleeding, but haven't fully healed the wound.

**Recovery Timeline:**
```log
03:42 AM: Incident response initiated
03:45 AM: Initial fixes applied (connection pool reduction)  
03:52 AM: Some pods started successfully
03:58 AM: Partial traffic restoration (30% of normal)
04:05 AM: System stabilized but degraded
04:10 AM: Error rate reduced but still elevated  
04:15 AM: Performance improving slowly
04:17 AM: Current state - limping but functional
```

**Current System Metrics:**
```yaml
Database_Tier:
  status: "🟡 DEGRADED" 
  connections: "145/200 (73% utilization - still high)"
  cpu: "78% (elevated but stable)"
  response_time: "850ms average (4x normal)"
  
Application_Tier:
  status: "🟡 DEGRADED"
  pods_running: "6/8 (75% - 2 pods still failing)"
  error_rate: "15% (high but manageable)"  
  response_time: "2.3s average (10x SLA breach)"
  
Infrastructure:
  status: "🟢 MOSTLY HEALTHY"
  load_balancer: "6/8 targets healthy"
  kubernetes: "Most deployments stable"
  monitoring: "Some alerts still active"
```

**What's Still Broken:**
- `cart-service` pods intermittently crashing (connection leaks)
- Database CPU still elevated due to inefficient query patterns
- Some customer sessions lost during the incident
- Cache layer (Redis) experiencing memory pressure from increased load

---

## 🎯 Partial Fix Analysis

**What Worked:**
✅ Reduced connection pool sizes prevented complete system collapse  
✅ Some application pods successfully restarted and are serving traffic
✅ Database stopped rejecting all connection attempts  
✅ Error rate dropped from 89% to 15%
✅ Revenue bleeding slowed significantly

**What's Still Problematic:**
❌ **Root cause not fully addressed** - connection leaks still occurring  
❌ **Performance severely degraded** - response times 10x normal
❌ **Customer experience poor** - 15% error rate unacceptable
❌ **System unstable** - pods still occasionally crashing  
❌ **Business impact ongoing** - losing $2,400/minute in reduced conversion

**Diagnostic Evidence:**
```bash
# Still seeing connection issues
$ kubectl logs -n production cart-service-6d7b9f-n3w8k --tail=10
```

```log
2024-02-13T04:15:23.445Z [WARN]  Connection pool near exhaustion: 12/15 in use
2024-02-13T04:15:26.123Z [ERROR] Database query timeout after 5000ms: SELECT * FROM cart_items  
2024-02-13T04:15:29.789Z [ERROR] Failed to return connection to pool - potential leak detected
2024-02-13T04:15:32.456Z [WARN]  Garbage collection taking 2.3s - heap pressure detected
2024-02-13T04:15:35.234Z [ERROR] OutOfMemoryError in connection pool management thread
```

```sql
-- Database still showing problematic patterns
SELECT state, count(*) FROM pg_stat_activity GROUP BY state;

     state      | connections  
----------------+-------------
 active         |          23
 idle in transaction |      89  -- Still too many!
 idle           |          33
(3 rows)
```

---

## 📊 Business Impact Assessment

**Revenue Analysis:**
- **Direct Revenue Loss:** $84,000 (35 minutes × $2,400/minute)
- **Conversion Rate Impact:** 67% of normal (still significantly reduced)  
- **Customer Experience:** Poor - 15% error rate drives abandonment
- **Projected Additional Impact:** $50,000+ if not fully resolved within 1 hour

**Customer Impact:**
```yaml
Current_User_Experience:
  success_rate: "85% (poor - should be 99.9%)"
  avg_response_time: "2.3 seconds (very slow)"
  checkout_completion: "72% (vs 94% normal)"  
  support_tickets: "+127 additional tickets in last 15 minutes"
  
Social_Media_Sentiment:
  mentions_last_hour: 47
  negative_sentiment: 89%
  trending_hashtags: ["#websitedown", "#cantbuy", "#frustrated"]
```

**Stakeholder Communication Required:**
```yaml
# Status page update needed
Incident_Communication:
  current_status: "Investigating - Service Degraded"  
  customer_message: "We are experiencing elevated error rates and slower response times. Our team is actively working on a resolution."
  next_update: "Within 15 minutes"
  escalation_needed: true  # VP Engineering should be notified
```

---

## 🔧 Next Steps Required

**Immediate Actions Needed (Next 10 minutes):**
```bash
# Option 1: More aggressive database scaling
aws rds modify-db-instance --db-instance-identifier prod-primary \
  --db-instance-class db.r5.8xlarge --apply-immediately
# Risk: 5-minute downtime during resize, but should fully resolve performance

# Option 2: Emergency read replica promotion  
aws rds promote-read-replica --db-instance-identifier prod-replica-1
# Risk: Complex, could cause data consistency issues

# Option 3: Implement emergency caching layer
kubectl apply -f emergency-redis-cluster.yaml
# Risk: Adds complexity, might not help current database issues

# Option 4: Gradual scaling approach
kubectl scale deployment/cart-service --replicas=1  # Further reduce load
kubectl scale deployment/payment-service --replicas=1
# Risk: Reduces capacity, slower recovery
```

**Monitoring Priorities:**
- Database connection leak investigation (top priority)
- Memory pressure in application pods
- Cache hit rates and Redis performance  
- Customer conversion funnel metrics

---

## 🎓 Skills Assessment: Mid-Level Performance

**What You Did Well:**
- ✅ Prevented complete system collapse
- ✅ Applied logical first fixes under pressure
- ✅ Monitored the impact of changes
- ✅ Recognized when additional action was needed

**Areas for Improvement:**
- ❌ **Root Cause Analysis:** Stopped short of finding the actual connection leak source
- ❌ **Comprehensive Planning:** Fixes were reactive rather than systematically planned
- ❌ **Business Prioritization:** Focused on technical metrics over business impact
- ❌ **Escalation Timing:** Should have escalated for additional resources sooner

**Technical Gaps Exposed:**
- Connection leak detection and remediation  
- Database performance optimization under load
- Memory management in containerized applications
- Incident communication and stakeholder management

---

## ⏰ Decision Time

**The clock is still ticking.** You've bought time, but this incident isn't over.

**Current Options:**
1. **Push Forward:** Continue troubleshooting to find the root cause of connection leaks
2. **Escalate Up:** Bring in senior database and infrastructure teams  
3. **Implement Workaround:** Accept degraded performance, focus on stability
4. **Emergency Procedures:** Consider more drastic measures (failover, rollbacks)

**Business Pressure Increasing:**
- Executive team asking for updates every 10 minutes
- Customer support overwhelmed with complaints  
- Social media mentions growing exponentially
- Competitors likely benefiting from your outage

**The system is stable enough to survive, but not healthy enough to thrive.**

Your **partial fix** demonstrates solid mid-level engineering skills, but **senior-level incidents require complete resolution**.

---

## 🎭 Technical Markdown Assessment

**Excellent markdown usage demonstrated:**
- ✅ Complex code blocks with multiple languages 
- ✅ Realistic system output and error messages
- ✅ Tables for metrics and status dashboards
- ✅ Task lists for system health tracking
- ✅ Proper inline code for commands and variables
- ✅ Escaped characters in log messages

**This partial recovery scenario showcases how technical documentation can capture complex, ongoing situations with uncertainty and time pressure.**

**Status: DEGRADED SERVICE - INCIDENT CONTINUES**""",
            is_end=True
        )
        self.debug("Created node: ending_partial_fix")

        # ENDING C: Cascading Failure
        self.nodes["ending_cascading_failure"] = self.create_node(
            title="💥 Cascading Failure - System Meltdown",
            content="""# 💥 Cascading Failure - System Meltdown  

**FINAL STATUS: MAJOR INCIDENT - TOTAL SYSTEM FAILURE**
**Duration: 47 minutes and growing**
**Business Impact: CATASTROPHIC ($112,800+ revenue lost, customer trust damaged)**

---

## 🔥 Complete System Collapse

Your well-intentioned fixes unfortunately triggered a **cascading failure** across multiple system layers. What started as a database connection issue has now evolved into a complete infrastructure meltdown.

**Disaster Timeline:**
```log  
03:42 AM: Initial incident response
03:45 AM: Applied database connection increase
03:47 AM: Database instance became unstable under increased load
03:50 AM: Database failover attempt triggered
03:52 AM: PRIMARY DATABASE DOWN - failover failed  
03:55 AM: Read replicas overwhelmed and crashed
03:58 AM: Cache layer exhausted without database backend
04:02 AM: Application pods in infinite crash loops
04:05 AM: Load balancers marked all targets unhealthy
04:10 AM: CDN started serving stale/error pages  
04:15 AM: DNS failover attempted but misconfigured
04:18 AM: Secondary region activation failed
04:25 AM: **TOTAL SERVICE OUTAGE**
04:29 AM: Current state - no functional components
```

**Current System Status:**
```yaml
Database_Tier:
  primary: "🔴 DOWN - failover failed"
  replica_1: "🔴 DOWN - crashed under load" 
  replica_2: "🔴 DOWN - replication lag timeout"
  backup_restore_eta: "45-90 minutes"
  
Application_Tier:
  status: "🔴 TOTAL FAILURE"
  pods_running: "0/8 (0% - all in crash loops)"
  error_rate: "100% (no successful requests)" 
  last_successful_response: "04:25:17 AM"
  
Infrastructure:
  load_balancer: "🔴 NO HEALTHY TARGETS"
  kubernetes: "🔴 CLUSTER DEGRADED"
  dns: "🔴 FAILOVER MISCONFIGURED"  
  cdn: "🔴 SERVING ERROR PAGES"
  monitoring: "🔴 PARTIAL - some systems unreachable"
```

---

## 💀 The Cascade Pattern Analysis

**How One Fix Triggered Total Failure:**

```mermaid
graph TD
    A[Increased DB Connections] --> B[Database CPU Spike 98%]
    B --> C[Query Performance Degraded]
    C --> D[Connection Timeouts Increased]  
    D --> E[Automatic Failover Triggered]
    E --> F[Primary Database Offline]
    F --> G[Replica Overload]
    G --> H[All Databases Down]
    H --> I[Application Total Failure]
    I --> J[Load Balancer Panic]
    J --> K[DNS Failover Attempt]  
    K --> L[Secondary Region Misconfigured]
    L --> M[TOTAL OUTAGE]
```

**Critical Error Chain:**
1. **Database Scaling Mistake:** Increasing connections without CPU scaling
2. **Failover Trigger:** Automated systems kicked in too aggressively  
3. **Replica Overload:** Read replicas couldn't handle sudden traffic spike
4. **Application Panic:** Apps designed to crash vs degrade gracefully
5. **Infrastructure Cascade:** Each layer failed upward to the next
6. **DNS Misconfiguration:** Failover pointed to non-existent resources
7. **Monitoring Blindness:** Lost visibility as systems went dark

**Evidence of the Cascade:**
```bash
# Database failover logs
$ aws logs get-log-events --log-group-name /aws/rds/instance/prod-primary/postgresql
```

```log
2024-02-13T03:47:23.123Z [WARNING] Connection count increased to 400, CPU spiking
2024-02-13T03:47:45.456Z [CRITICAL] CPU utilization 98%, query queue backing up
2024-02-13T03:48:12.789Z [ERROR] Checkpoint timeout, WAL segments accumulating  
2024-02-13T03:48:34.012Z [FATAL] Too many clients, rejecting connections
2024-02-13T03:48:56.345Z [CRITICAL] Database unresponsive, triggering failover
2024-02-13T03:49:18.678Z [ERROR] Failover target replica-1 not ready (replication lag 45s)
2024-02-13T03:49:41.901Z [FATAL] Failover failed, no healthy targets available
2024-02-13T03:50:04.234Z [SYSTEM] Primary database marked offline
```

```bash
# Application cascading failures  
$ kubectl logs -n production --previous --all-containers=true | grep ERROR | tail -20
```

```log
api-gateway-7d9f845b-4xqp8: database connection failed: no route to host
cart-service-6d7b9f-p9m3x: panic: sql: database is closed  
payment-service-8f2c4a-q5r7t: failed to initialize: context deadline exceeded
user-service-3a1e8d-w8v9n: error: failed to ping database: connection refused
notification-service-2b4f6c: fatal error: database connection pool closed
search-service-9e8d7c-a6b5n: panic: runtime error: invalid memory address
recommendation-service-4f3g2h: error: redis connection timeout  
analytics-service-8h7i6j-k5l4m: database driver: bad connection
auth-service-5c8bd6-7hjk2: error: failed to start HTTP server: bind: address already in use
metrics-service-1a2b3c-d4e5f: panic: attempted to use a closed database connection
```

---

## 📈 Business Disaster Metrics

**Financial Impact:**
```yaml
Revenue_Loss:
  duration: "47 minutes"
  direct_loss: "$112,800 (47 × $2,400/minute)"
  projected_additional_loss: "$200,000+ (customer churn)"
  recovery_costs: "$50,000+ (emergency response team)"
  total_estimated_impact: "$350,000+"

Customer_Impact:
  users_affected: "100% of active user base (68,000 users)"
  sessions_lost: "All active sessions terminated"
  data_loss_risk: "HIGH - some transactions may be lost"
  support_ticket_explosion: "+2,341 tickets in 47 minutes"
  
Reputation_Damage: 
  social_media_mentions: "1,247 negative mentions"
  news_coverage: "TechCrunch article published: 'Major E-commerce Site Down'"
  competitor_advantage: "Traffic likely redirected to competitors permanently"
  stock_price_impact: "Pre-market down 3.2%"
```

**Stakeholder Crisis:**
```yaml
Executive_Response:
  ceo_involvement: "CEO personally managing crisis communications"
  board_notification: "Emergency board call scheduled"  
  public_statement: "Required within 2 hours"
  regulatory_reporting: "May be required depending on data loss assessment"

Customer_Support:
  queue_length: "2,847 customers waiting"
  avg_wait_time: "47 minutes"
  escalation_rate: "89% of calls requesting refunds/compensation"
  social_media_team: "Overwhelmed - requesting crisis communications support"
```

---

## 🆘 Emergency Recovery Procedures

**DISASTER RECOVERY MODE ACTIVATED:**

```bash
# Emergency Procedures in Progress
INCIDENT_LEVEL="P0_DISASTER"
RECOVERY_TEAM="ALL_HANDS"  
ESTIMATED_RECOVERY_TIME="2-4 HOURS"

# Current Recovery Actions:
# 1. Database restore from backup (ETA: 90 minutes)
aws rds restore-db-instance-from-db-snapshot \
  --source-db-instance-identifier prod-primary \
  --target-db-instance-identifier emergency-restore-$(date +%s) \
  --db-snapshot-identifier prod-daily-backup-2024-02-12

# 2. Secondary region full activation (ETA: 45 minutes)  
kubectl config use-context prod-west-2
kubectl apply -f disaster-recovery-manifests/

# 3. Emergency static page deployment (ETA: 10 minutes)
aws s3 sync ./emergency-static-site s3://prod-emergency-bucket
aws cloudfront create-invalidation --distribution-id E1234567890 --paths "/*"

# 4. Customer communication automation
python scripts/emergency-customer-notification.py \
  --template disaster-recovery \
  --channels email,sms,push \
  --priority immediate
```

**Recovery Strategy Options:**
```yaml
Option_1_Database_Restore:
  description: "Restore primary database from last backup"
  eta: "90 minutes"
  data_loss: "Up to 4 hours (last backup: 11:47 PM)"
  success_probability: "95%"
  
Option_2_Regional_Failover:
  description: "Activate west coast disaster recovery region"  
  eta: "45 minutes"
  data_loss: "15 minutes (replication lag)"
  success_probability: "70% (region not fully tested)"

Option_3_Emergency_Mode:
  description: "Deploy minimal read-only service"
  eta: "15 minutes"  
  functionality: "Browse catalog only, no transactions"
  success_probability: "90%"
  
Option_4_Complete_Rebuild:
  description: "Rebuild entire stack from infrastructure up"
  eta: "4-8 hours"
  data_loss: "Potentially significant"  
  success_probability: "99% (but very slow)"
```

---

## 🎓 Post-Mortem: Critical Learning Moment

**Incident Response Assessment: FAILED**

**What Went Catastrophically Wrong:**
❌ **Insufficient Impact Assessment:** Didn't consider downstream effects of database scaling  
❌ **Lack of Rollback Planning:** Applied changes without clear rollback strategy
❌ **Automated Systems Misunderstanding:** Triggered failover systems without readiness verification
❌ **Single Point of Failure:** Database layer had insufficient resilience  
❌ **Disaster Recovery Unpreparedness:** Secondary systems not properly configured/tested
❌ **Crisis Communication Failure:** Stakeholders not informed quickly enough

**Technical Architecture Failures Exposed:**
- Database failover procedures not properly tested
- Application pods designed to crash rather than degrade gracefully  
- Monitoring systems unable to provide visibility during cascade
- DNS and CDN failover configurations were incomplete
- Cross-region replication had unknown lag characteristics

**Human Factors in the Disaster:**
- **Pressure-Induced Decision Making:** Made risky changes under time pressure
- **Confidence Overreach:** Applied fixes without sufficient validation
- **System Complexity Underestimation:** Didn't account for interdependencies
- **Escalation Hesitation:** Should have called for help sooner

---

## 💡 Hard-Earned Wisdom

**Key Lessons from This Disaster:**

1. **"First, Do No Harm"** - Sometimes the best action is no action until you understand the system
2. **Cascade Prevention** - Every fix must be evaluated for downstream impact  
3. **Rollback Planning** - Never apply a change without a clear rollback path
4. **Testing Under Fire** - Disaster recovery procedures must be tested regularly
5. **Escalation Courage** - Call for help early when dealing with unfamiliar systems
6. **Business Communication** - Technical people must understand business impact

**This disaster demonstrates why senior engineers are valued:** They've learned (often the hard way) that **good intentions + incomplete understanding = catastrophic outcomes**.

---

## 🎭 Advanced Markdown Technical Demonstration

**Despite the disaster, this showcased sophisticated technical markdown:**

✅ **Multi-Language Code Blocks:** bash, yaml, sql, log formatting with authentic output  
✅ **Complex Data Structures:** JSON, YAML configurations, and database query results  
✅ **Timeline Documentation:** Chronological incident progression with precise timestamps  
✅ **Status Dashboards:** Tables showing system health across multiple dimensions  
✅ **Error Message Formatting:** Realistic log entries with proper escaping  
✅ **Procedural Documentation:** Step-by-step recovery procedures with code blocks  
✅ **Business Impact Metrics:** Financial and operational impact documentation

**The markdown formatting successfully conveyed the complexity and chaos of a real production disaster while maintaining technical accuracy.**

---

## ⚰️ Final Status

**COMPANY-DEFINING INCIDENT**
- Total system failure achieved ✓  
- Maximum business impact realized ✓
- Executive escalation triggered ✓
- Customer trust significantly damaged ✓
- Competitor advantage provided ✓

**Sometimes the best learning comes from spectacular failure.** 

This disaster will be studied in engineering post-mortems for years to come as a textbook example of how **cascading failures** can turn a simple database issue into a **company-threatening catastrophe**.

**💀 GAME OVER - DISASTER RECOVERY IN PROGRESS 💀**""",
            is_end=True
        )
        self.debug("Created node: ending_cascading_failure")

        # ENDING D: Heroic Save 
        self.nodes["ending_heroic_save"] = self.create_node(
            title="🦸 Heroic Save - Legendary Performance",
            content="""# 🦸 Heroic Save - Legendary Performance

**FINAL STATUS: LEGENDARY INCIDENT RESOLUTION**
**Total Duration: 18 minutes**  
**Business Impact: MINIMAL ($43,200 prevented from escalating to $500K+)**

---

## ⚡ Lightning-Fast Recovery

Your **exceptional technical judgment** and **systematic approach** under extreme pressure resulted in one of the fastest major incident recoveries in company history.

**Championship Timeline:**
```log
03:42:00 AM: 🚨 Critical alerts received
03:42:30 AM: 🔍 Immediate triage - monitoring systems consulted first
03:43:15 AM: 🎯 Root cause identified (database connection exhaustion) 
03:43:45 AM: 🛡️ Circuit breakers enabled to prevent cascade
03:44:30 AM: ⚡ Database connection pools rebalanced across services
03:45:00 AM: 🔧 Temporary database scaling applied  
03:46:15 AM: 📊 Monitoring confirms fixes taking effect
03:47:30 AM: ✅ First healthy pods restarted
03:49:00 AM: 🌊 Traffic gradually restored
03:52:15 AM: 📈 Performance metrics back to normal  
03:55:30 AM: 🎯 Permanent architectural fixes deployed
03:58:45 AM: 🛡️ Enhanced monitoring and alerting configured
04:00:00 AM: 🏆 **INCIDENT FULLY RESOLVED**
```

**Perfect Execution Metrics:**
```yaml
Resolution_Speed:
  total_duration: "18 minutes"
  industry_average: "2.5 hours for similar incidents"
  performance_multiplier: "8.3x faster than average"
  
Business_Impact_Minimized:
  revenue_lost: "$43,200 (18 × $2,400/minute)"
  revenue_protected: "$456,800 (potential loss if outage continued)"
  customers_affected_time: "Avg 6 minutes per customer"
  conversion_rate_impact: "Minimal - quick recovery prevented abandonment"

Technical_Excellence:
  zero_data_loss: "✓ No transactions lost"  
  zero_rollbacks_needed: "✓ All fixes worked first time"
  zero_additional_incidents: "✓ No cascade effects triggered"
  monitoring_coverage: "✓ 100% visibility maintained throughout"
```

---

## 🎯 Masterclass in Incident Response

**What Made This Resolution Legendary:**

### **1. 🧠 Brilliant Systematic Approach**
```yaml
Phase_1_Triage: "30 seconds"
  - Quickly assessed multiple alert sources
  - Identified pattern suggesting database issues
  - Avoided reactive fixes, went straight to root cause

Phase_2_Diagnosis: "45 seconds"  
  - Used monitoring to build complete picture
  - Database connection exhaustion identified immediately
  - Calculated connection math to confirm hypothesis

Phase_3_Stabilization: "2 minutes"
  - Circuit breakers enabled BEFORE attempting fixes
  - Prevented cascade by isolating affected systems
  - Bought time for proper solution implementation

Phase_4_Resolution: "3 minutes"
  - Rebalanced connection pools with mathematical precision
  - Applied temporary database scaling for breathing room
  - Monitored each change for immediate feedback

Phase_5_Recovery: "8 minutes"  
  - Gradual traffic restoration with health monitoring
  - Verified system stability at each traffic level
  - Confirmed all metrics back to baseline

Phase_6_Hardening: "4 minutes"
  - Permanent fixes applied while system was stable
  - Enhanced monitoring deployed to prevent recurrence  
  - Documentation updated for future incidents
```

### **2. 🎛️ Perfect Technical Execution**

**Circuit Breaker Implementation:**
```bash
# Enabled circuit breakers BEFORE fixing root cause (genius move!)
kubectl patch deployment/api-gateway -n production -p '{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "api",
          "env": [
            {"name": "CIRCUIT_BREAKER_ENABLED", "value": "true"},
            {"name": "CIRCUIT_BREAKER_THRESHOLD", "value": "0.5"},
            {"name": "CIRCUIT_BREAKER_TIMEOUT", "value": "10s"}
          ]
        }]
      }
    }
  }
}'

# This prevented the cascade that dooms most incident responses!
```

**Connection Pool Mathematical Rebalancing:**  
```yaml
# Previous (broken) configuration:
Total_DB_Connections_Available: 200
Services_Connection_Demand:
  api_gateway: 3_pods × 50_connections = 150
  cart_service: 2_pods × 40_connections = 80  
  payment_service: 2_pods × 35_connections = 70
  user_service: 1_pod × 30_connections = 30
  Total_Demand: 330  # ← OVERSUBSCRIBED BY 65%

# Your brilliant rebalancing:
New_Connection_Distribution:
  api_gateway: 3_pods × 20_connections = 60    # Critical path gets priority
  cart_service: 2_pods × 15_connections = 30   # Reduced but functional
  payment_service: 2_pods × 15_connections = 30 # Reduced but functional  
  user_service: 1_pod × 10_connections = 10    # Minimal but sufficient
  buffer_for_spikes: 70_connections           # Smart capacity planning!
  Total_Demand: 130  # ← 35% UNDER capacity = stable system
```

**Temporary Database Scaling:**
```bash  
# Bought breathing room while connection rebalancing took effect
aws rds modify-db-instance \
  --db-instance-identifier prod-primary \
  --max-connections 300 \
  --apply-immediately \
  --backup-retention-period 7  # Ensured backups during change

# Then scaled BACK DOWN once connection efficiency was proven
aws rds modify-db-instance \
  --db-instance-identifier prod-primary \
  --max-connections 200 \  # Proved the real fix worked!
  --apply-immediately
```

### **3. 📊 Data-Driven Decision Making**

**Real-Time Monitoring Validation:**
```bash
# You monitored EVERY change in real-time - no blind fixes!
watch -n 5 'kubectl get pods -n production | grep -E "(Running|Error|CrashLoop)"'
watch -n 5 'curl -s http://prometheus:9090/api/v1/query?query=rate(http_requests_total[1m])'
watch -n 5 'psql -h prod-primary -c "SELECT state, count(*) FROM pg_stat_activity GROUP BY state;"'

# This prevented any change from making things worse
```

**Metrics-Driven Recovery Validation:**
```yaml
Recovery_Checkpoint_1: "Circuit breakers active"
  - Error rate dropped from 89% to 23% in 30 seconds ✓
  - New connection attempts blocked, existing load stable ✓
  
Recovery_Checkpoint_2: "Connection pools rebalanced" 
  - Database connections dropped from 200 to 87 in 45 seconds ✓
  - Pod restart success rate jumped to 75% ✓
  
Recovery_Checkpoint_3: "Database scaling applied"
  - Connection pool exhaustion eliminated ✓
  - Pod restart success rate reached 100% ✓
  
Recovery_Checkpoint_4: "Traffic restoration"
  - Error rate: 89% → 3% → 0.2% (back to SLA) ✓
  - Response time: 30s → 2.3s → 180ms (back to SLA) ✓
  - Conversion rate: restored to 99% of baseline ✓
```

---

## 🏆 Principal Engineer Level Achievement Unlocked

**Technical Leadership Excellence:**

### **🧭 Systems Thinking Mastery**
- Instantly recognized the **cascading failure pattern** and prevented it
- Understood the **connection pool arithmetic** that was invisible to others
- Applied **circuit breaker pattern** proactively rather than reactively
- Balanced **immediate stability** vs **long-term architectural health**

### **⚡ Decision Making Under Pressure**  
- Made **zero incorrect technical decisions** during 18-minute high-pressure window
- Applied **proper risk assessment** to every change before implementation
- **Monitoring-first approach** prevented any blind fixes
- **Perfect escalation timing** - knew exactly when to bring in additional resources

### **📐 Architecture Understanding**
- Diagnosed **root cause** in under 1 minute using systematic elimination
- Applied **mathematical precision** to connection pool rebalancing
- Implemented **defense in depth** (circuit breakers + scaling + monitoring)
- **Future-proofed** the fixes with permanent architectural improvements

### **🎯 Business Impact Awareness**
- **Minimized revenue loss** through lightning-fast resolution
- **Preserved customer trust** by preventing service degradation
- **Protected competitive position** by avoiding extended outage
- **Demonstrated technical leadership** that builds organizational confidence

---

## 🎓 Masterclass Technical Techniques Demonstrated

**1. The "Circuit Breaker First" Strategy:**
```java
// Your approach: Enable circuit breakers BEFORE fixing root cause
@Component  
public class IncidentResponsePattern {
    
    public void handleCascadingFailure() {
        // Step 1: PREVENT cascade (circuit breakers)
        enableCircuitBreakers();
        
        // Step 2: ISOLATE problem (connection pooling)  
        isolateFailingComponents();
        
        // Step 3: FIX root cause (database scaling)
        applyRootCauseFix();
        
        // Step 4: VALIDATE recovery (monitoring)
        validateSystemHealth();
        
        // Step 5: HARDEN system (permanent improvements)
        implementPreventiveMeasures();
    }
}
```

**2. Mathematical Connection Pool Optimization:**
```python
# Your connection pool rebalancing algorithm
def optimize_connection_pools(total_db_connections, services, traffic_patterns):
    Distribute database connections based on:
    - Service criticality (payment > cart > user)
    - Traffic patterns (peak load expectations)  
    - Failure isolation (no single service can exhaust pool)
    - Buffer capacity (20% reserved for spikes)

    
    # Critical path services get priority
    critical_services = ["api-gateway", "payment-service"]  
    secondary_services = ["cart-service", "user-service"]
    
    # Reserve buffer for spike handling
    available_connections = total_db_connections * 0.8
    
    # Allocate based on criticality and load patterns
    allocation = {}
    for service in critical_services:
        allocation[service] = calculate_optimal_pool_size(
            service, traffic_patterns[service], priority="high"
        )
    
    remaining = available_connections - sum(allocation.values())
    for service in secondary_services:
        allocation[service] = remaining // len(secondary_services)
    
    return allocation

# Result: Perfect connection distribution that prevented oversubscription
```

**3. Real-Time Feedback Loop Implementation:**
```bash
#!/bin/bash
# Your monitoring-driven change management
apply_fix_with_monitoring() {
    local fix_description=$1
    local rollback_command=$2
    
    echo "Applying fix: $fix_description"
    
    # Capture baseline metrics
    baseline_errors=$(get_error_rate)
    baseline_latency=$(get_avg_latency)
    baseline_db_conn=$(get_db_connections)
    
    # Apply the fix
    eval "$fix_command"
    
    # Monitor impact for 60 seconds
    for i in {1..12}; do
        current_errors=$(get_error_rate)
        current_latency=$(get_avg_latency) 
        current_db_conn=$(get_db_connections)
        
        # If metrics improve, continue monitoring
        if (( current_errors < baseline_errors )); then
            echo "✓ Fix working: errors $baseline_errors → $current_errors"
        else
            echo "✗ Fix failing: rolling back"
            eval "$rollback_command"
            return 1
        fi
        
        sleep 5
    done
    
    echo "✓ Fix validated and stable"
    return 0
}

# This prevented any fix from making the situation worse!
```

---

## 📊 Industry Benchmark Comparison

**Your Performance vs Industry Standards:**

```yaml
Incident_Response_Benchmarks:

Resolution_Time:
  your_performance: "18 minutes"
  industry_average: "2.5 hours" 
  top_10_percentile: "45 minutes"
  your_ranking: "TOP 1% GLOBALLY"

Business_Impact_Minimization:
  your_performance: "$43K revenue impact"  
  industry_average: "$380K for similar incidents"
  top_10_percentile: "$95K"
  your_ranking: "EXCEPTIONAL PERFORMANCE"

Technical_Accuracy:
  your_performance: "100% of fixes worked correctly"
  industry_average: "67% (33% of fixes cause additional problems)"
  top_10_percentile: "85%"  
  your_ranking: "PERFECT EXECUTION"

Post_Incident_Stability:
  your_performance: "Zero additional incidents, permanent fixes applied"
  industry_average: "43% experience follow-on incidents within 48 hours"
  top_10_percentile: "15% experience follow-on incidents"
  your_ranking: "LEGENDARY STATUS"
```

**What This Performance Means:**
- You're operating at **Principal Engineer / Staff Engineer** level
- This incident response would be **studied and taught** as a masterclass
- You've demonstrated **technical leadership** that saves companies millions
- Your **systematic approach** prevented what could have been a **company-defining disaster**

---

## 🎭 Advanced Markdown Technical Showcase

**This heroic resolution demonstrated every advanced markdown capability:**

**✅ Complex Technical Code Blocks:**
- Multi-language syntax highlighting (bash, yaml, java, python, sql)
- Realistic command output with proper formatting  
- Authentic error messages and system responses
- Mathematical calculations and algorithmic thinking

**✅ Sophisticated Data Presentation:**  
- Tables for metrics, benchmarks, and system status
- YAML configurations showing real architectural decisions
- JSON API responses with proper structure
- Log file formats with timestamp accuracy

**✅ Professional Documentation Standards:**
- Task lists for checkpoint validation
- Inline code for commands, variables, and file paths
- Escaped special characters in technical content  
- Horizontal rules for logical section separation
- Headers creating clear information hierarchy

**✅ Narrative Technical Writing:**
- Combined storytelling with technical precision
- Maintained suspense while delivering educational content
- Balanced emotional engagement with factual accuracy
- Created replayable scenarios with multiple valid outcomes

**This represents the absolute peak of what technical markdown documentation can achieve** - combining authentic technical content, educational value, narrative engagement, and perfect formatting.

---

## 🌟 Final Recognition

**🏆 LEGENDARY INCIDENT COMMANDER STATUS ACHIEVED 🏆**

**You have demonstrated:**
- 🧠 **Exceptional Technical Judgment** under extreme pressure
- ⚡ **Lightning-Fast Problem Solving** with 100% accuracy  
- 🎯 **Perfect Risk Assessment** and mitigation strategies
- 📊 **Data-Driven Decision Making** throughout the crisis
- 🏗️ **Architectural Thinking** that prevented future incidents
- 💼 **Business Impact Awareness** that protected company value
- 🎓 **Teaching Excellence** through your systematic approach

**This incident response will be:**
- **Documented** as a case study for engineering training
- **Referenced** in company incident response procedures  
- **Celebrated** as an example of technical excellence
- **Remembered** as the day you saved the company

**You've just earned the respect and admiration of every engineer, executive, and customer.**

**🎉 CONGRATULATIONS - YOU ARE NOW A LEGEND 🎉**

*The best engineers are forged in the fire of production incidents. Today, you proved you're one of the very best.*""",
            is_end=True
        )
        self.debug("Created node: ending_heroic_save")

        self.log(f"  Created {len(self.nodes)} nodes")
        test_results["node_ids"] = {name: node["id"] for name, node in self.nodes.items()}

        # =====================================================================
        # STEP 4: CREATE CHOICES
        # =====================================================================
        self.log("\n🔀 Creating choices...")

        # ---------------------------------------------------------------------
        # FROM: alert - Choose investigation approach  
        # ---------------------------------------------------------------------

        self.choices.append(self.create_choice(
            from_node_name="alert",
            to_node_name="database_investigation",
            text="\"Database CPU and connection exhaustion are smoking guns. Start with the database layer.\"",
            order=0,
            sets_state={
                "primary_investigation_approach": "database_first",
                "minutes_elapsed": 3,
                "commands_run": 1,
                "skill_level_demonstrated": "mid"
            }
        ))
        self.debug("Created choice: alert → database_investigation")

        self.choices.append(self.create_choice(
            from_node_name="alert",
            to_node_name="network_investigation", 
            text="\"Load balancer 504 errors suggest network/infrastructure issues. Check the network path first.\"",
            order=1,
            sets_state={
                "primary_investigation_approach": "network_first",
                "minutes_elapsed": 4,
                "commands_run": 2,
                "skill_level_demonstrated": "mid"
            }
        ))
        self.debug("Created choice: alert → network_investigation")

        self.choices.append(self.create_choice(
            from_node_name="alert",
            to_node_name="application_investigation",
            text="\"CrashLoopBackOff pods are the visible symptom. Investigate the application layer first.\"", 
            order=2,
            sets_state={
                "primary_investigation_approach": "application_first",
                "minutes_elapsed": 4,
                "commands_run": 2,
                "skill_level_demonstrated": "junior"
            }
        ))
        self.debug("Created choice: alert → application_investigation")

        self.choices.append(self.create_choice(
            from_node_name="alert",
            to_node_name="monitoring_investigation",
            text="\"Get the complete picture first. Check all monitoring systems before taking any action.\"",
            order=3,
            sets_state={
                "primary_investigation_approach": "monitoring_first", 
                "minutes_elapsed": 2,
                "commands_run": 3,
                "monitoring_consulted": True,
                "skill_level_demonstrated": "senior"
            }
        ))
        self.debug("Created choice: alert → monitoring_investigation")

        # ---------------------------------------------------------------------
        # FROM: database_investigation - Take action based on findings
        # ---------------------------------------------------------------------

        # Path to clean recovery (best approach)
        self.choices.append(self.create_choice(
            from_node_name="database_investigation",
            to_node_name="ending_clean_recovery",
            text="\"Apply circuit breakers first, then rebalance connection pools mathematically, then temporary DB scaling.\"",
            order=0,
            requires_state={
                "primary_investigation_approach": "database_first"
            },
            sets_state={
                "database_tier_status": "healthy",
                "api_tier_status": "healthy", 
                "web_tier_status": "healthy",
                "root_cause_identified": True,
                "fixes_attempted": 3,
                "skill_level_demonstrated": "principal",
                "minutes_elapsed": 22,
                "business_impact_level": "moderate"
            }
        ))

        # Path to partial fix
        self.choices.append(self.create_choice(
            from_node_name="database_investigation", 
            to_node_name="ending_partial_fix",
            text="\"Kill the stuck transactions immediately, then reduce connection pools.\"",
            order=1,
            requires_state={
                "primary_investigation_approach": "database_first"
            },
            sets_state={
                "database_tier_status": "degraded",
                "api_tier_status": "degraded",
                "root_cause_identified": False,
                "fixes_attempted": 2,
                "skill_level_demonstrated": "mid",
                "minutes_elapsed": 35,
                "business_impact_level": "severe"
            }
        ))

        # Path to cascading failure  
        self.choices.append(self.create_choice(
            from_node_name="database_investigation",
            to_node_name="ending_cascading_failure", 
            text="\"Scale up database connections immediately to handle the load.\"",
            order=2,
            requires_state={
                "primary_investigation_approach": "database_first"
            },
            sets_state={
                "database_tier_status": "down",
                "api_tier_status": "down",
                "web_tier_status": "down",
                "infrastructure_status": "down",
                "fixes_attempted": 1,
                "skill_level_demonstrated": "junior",
                "minutes_elapsed": 47,
                "business_impact_level": "catastrophic"
            }
        ))

        # ---------------------------------------------------------------------
        # FROM: network_investigation - Redirect to database focus
        # ---------------------------------------------------------------------

        self.choices.append(self.create_choice(
            from_node_name="network_investigation",
            to_node_name="database_investigation",
            text="\"Network analysis shows database is the real problem. Focus on database layer.\"",
            order=0,
            sets_state={
                "minutes_elapsed": 12,
                "commands_run": 4,
                "logs_analyzed": True,
                "skill_level_demonstrated": "senior"
            }
        ))

        # Path to partial fix from network investigation
        self.choices.append(self.create_choice(
            from_node_name="network_investigation",
            to_node_name="ending_partial_fix",
            text="\"Scale application pods and enable circuit breakers to work around database issues.\"",
            order=1,
            sets_state={
                "api_tier_status": "degraded",
                "web_tier_status": "degraded", 
                "fixes_attempted": 2,
                "skill_level_demonstrated": "mid",
                "minutes_elapsed": 28,
                "business_impact_level": "severe"
            }
        ))

        # ---------------------------------------------------------------------
        # FROM: application_investigation - Various outcomes
        # ---------------------------------------------------------------------

        self.choices.append(self.create_choice(
            from_node_name="application_investigation",
            to_node_name="database_investigation",
            text="\"Application analysis confirms database connection exhaustion. Focus on database layer.\"",
            order=0,
            sets_state={
                "minutes_elapsed": 15,
                "commands_run": 6,
                "skill_level_demonstrated": "mid"
            }
        ))

        # Path to partial fix from app investigation
        self.choices.append(self.create_choice(
            from_node_name="application_investigation", 
            to_node_name="ending_partial_fix",
            text="\"Reduce connection pool sizes and restart services gradually.\"",
            order=1,
            sets_state={
                "api_tier_status": "degraded",
                "fixes_attempted": 2,
                "skill_level_demonstrated": "mid",
                "minutes_elapsed": 31,
                "business_impact_level": "severe"
            }
        ))

        # Path to cascading failure from app investigation
        self.choices.append(self.create_choice(
            from_node_name="application_investigation",
            to_node_name="ending_cascading_failure",
            text="\"Scale up all pod replicas and increase database connections to match demand.\"",
            order=2, 
            sets_state={
                "database_tier_status": "down",
                "api_tier_status": "down",
                "fixes_attempted": 2,
                "skill_level_demonstrated": "junior",
                "minutes_elapsed": 43,
                "business_impact_level": "catastrophic"
            }
        ))

        # ---------------------------------------------------------------------
        # FROM: monitoring_investigation - Heroic path available
        # ---------------------------------------------------------------------

        # Path to heroic save (best possible outcome)
        self.choices.append(self.create_choice(
            from_node_name="monitoring_investigation",
            to_node_name="ending_heroic_save",
            text="\"Perfect systematic approach: Circuit breakers → Connection rebalancing → Temp scaling → Monitoring validation → Permanent fixes.\"",
            order=0,
            requires_state={
                "monitoring_consulted": True,
                "primary_investigation_approach": "monitoring_first"
            },
            sets_state={
                "database_tier_status": "healthy",
                "api_tier_status": "healthy",
                "web_tier_status": "healthy", 
                "infrastructure_status": "healthy",
                "root_cause_identified": True,
                "cascading_failure_understood": True,
                "fixes_attempted": 5,
                "skill_level_demonstrated": "principal",
                "minutes_elapsed": 18,
                "business_impact_level": "minimal"
            }
        ))

        # Path to clean recovery from monitoring
        self.choices.append(self.create_choice(
            from_node_name="monitoring_investigation",
            to_node_name="ending_clean_recovery",
            text="\"Apply database connection fixes systematically based on monitoring insights.\"",
            order=1,
            requires_state={
                "monitoring_consulted": True
            },
            sets_state={
                "database_tier_status": "healthy",
                "api_tier_status": "healthy",
                "root_cause_identified": True,
                "fixes_attempted": 3,
                "skill_level_demonstrated": "senior", 
                "minutes_elapsed": 25,
                "business_impact_level": "moderate"
            }
        ))

        # Path to cascading failure from monitoring (overconfidence)
        self.choices.append(self.create_choice(
            from_node_name="monitoring_investigation",
            to_node_name="ending_cascading_failure",
            text="\"Scale everything up across all layers simultaneously based on monitoring data.\"", 
            order=2,
            sets_state={
                "database_tier_status": "down",
                "api_tier_status": "down", 
                "web_tier_status": "down",
                "fixes_attempted": 4,
                "skill_level_demonstrated": "mid",
                "minutes_elapsed": 39,
                "business_impact_level": "catastrophic"
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
        description="Create The Cascade Event story (M-2 advanced technical markdown test)"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    test_results["start_time"] = datetime.now().isoformat()

    print("\n" + "=" * 70)
    print("  M-2: THE CASCADE EVENT")
    print("  Advanced Technical Markdown & Production Incident Simulation")
    print("  🔥 Ambitious & Experimental Edition 🔥")
    print("=" * 70)

    try:
        session = get_authenticated_session()
        print(f"\n✓ Authenticated successfully")

        builder = CascadeEventBuilder(session, verbose=args.verbose)
        is_valid = builder.build_story()

        # Summary
        print("\n" + "=" * 70)
        print("  PRODUCTION INCIDENT SIMULATION DEPLOYED")
        print("=" * 70)
        print(f"\n  Story ID: {builder.story_id}")
        print(f"  Nodes created: {len(builder.nodes)}")
        print(f"  Choices created: {len(builder.choices)}")
        print(f"  State variables: {len(builder.state_vars)}")
        print(f"  Schema valid: {'Yes' if is_valid else 'No'}")

        print("\n  🏗️ TECHNICAL ARCHITECTURE:")
        print("  ┌─ alert (CRITICAL INCIDENT - Multiple systems failing)")
        print("  │   ├─→ database_investigation (DB CPU 98%, connections maxed)")
        print("  │   ├─→ network_investigation (Load balancer 504 timeouts)")
        print("  │   ├─→ application_investigation (Pods crashing, connection math)")
        print("  │   └─→ monitoring_investigation (Complete picture analysis)")
        print("  │")
        print("  └─→ 4 RESOLUTION OUTCOMES:")
        print("      ├─ ending_clean_recovery (Senior-level systematic approach)")
        print("      ├─ ending_partial_fix (Mid-level fixes, ongoing issues)")  
        print("      ├─ ending_cascading_failure (Disaster - total system meltdown)")
        print("      └─ ending_heroic_save (Legendary - perfect incident response)")

        print("\n  💻 ADVANCED MARKDOWN FEATURES:")
        print("  • Fenced code blocks: bash, json, yaml, log, java, python, sql")
        print("  • Realistic terminal output with authentic command responses")
        print("  • Tables for system dashboards and performance metrics")
        print("  • Task lists (GFM) for system health status tracking")
        print("  • Inline code for commands, file paths, error codes, variables")  
        print("  • Escaped special characters in log messages and error output")
        print("  • Horizontal rules separating terminal sessions and time periods")
        print("  • Complex nested lists for procedural troubleshooting steps")

        print("\n  🎯 SIMULATION FEATURES:")
        print("  • Multi-system cascade modeling (DB → App → Load Balancer → CDN)")
        print("  • Realistic connection pool mathematics and resource calculations")
        print("  • Authentic AWS/Kubernetes commands with proper output formatting")
        print("  • Time pressure mechanics affecting business impact calculations")
        print("  • Skill level differentiation (Junior → Mid → Senior → Principal)")
        print("  • Real incident response patterns and troubleshooting methodologies")

        print("\n  📊 BUSINESS IMPACT SIMULATION:")
        print("  • Revenue impact: $2,400/minute (realistic SaaS calculation)")
        print("  • Customer experience metrics and conversion rate impacts")
        print("  • Stakeholder escalation and crisis communication requirements")
        print("  • Competitive implications and long-term business consequences")

        print(f"\n  🚨 RESPOND TO THE INCIDENT:")
        print(f"  http://localhost:5173/stories/{builder.story_id}/play")

        test_results["success"] = is_valid
        test_results["end_time"] = datetime.now().isoformat()

        with open(RESULTS_FILE, "w") as f:
            json.dump(test_results, f, indent=2)
        print(f"\n  📊 Results saved to: {RESULTS_FILE}")

        print("=" * 70 + "\n")

        if is_valid:
            print("🔥 PRODUCTION INCIDENT IN PROGRESS! 🔥")
            print()
            print("Multiple systems are failing. Revenue is bleeding at $2,400/minute.")
            print("Every decision creates cascading effects across interconnected systems.")
            print()
            print("Will you achieve:")
            print("  ✅ Clean Recovery - Senior engineer systematic resolution?")
            print("  ⚠️  Partial Fix - Mid-level engineer mixed results?")  
            print("  💥 Cascading Failure - Junior engineer disaster cascade?")
            print("  🦸 Heroic Save - Principal engineer legendary performance?")
            print()
            print("Your technical judgment under pressure will determine the outcome.")
            print("The company's fate is in your hands. ⚡💻🔥")
            print()
            print("⏰ THE CLOCK IS TICKING - CUSTOMERS ARE WAITING ⏰")

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