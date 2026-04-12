#!/usr/bin/env bash
# Creates the "LLM-assisted feature delivery in a brownfield monolith" story
# Mirrors the structure from built-up.md

set -e

TYPER_DIR="/home/josep/dog/backend/app/test_scripts/typer"
cd "$TYPER_DIR"

# Ensure venv is active
source /home/josep/dog/backend/.venv/bin/activate

PY="python main.py"

# Extract JSON .id from output that may contain login status lines before the JSON
extract_id() {
    python3 -c "
import sys, json
raw = sys.stdin.read()
start = raw.find('{')
if start >= 0:
    try:
        obj = json.loads(raw[start:])
        print(obj.get('id', ''))
    except Exception as e:
        sys.stderr.write('JSON parse error: ' + str(e) + '\n')
        sys.stderr.write('Raw: ' + raw + '\n')
"
}

echo "=== Step 1: Create story ==="
STORY_ID=$($PY stories create "LLM-assisted feature delivery in a brownfield monolith" \
  --desc "A review-oriented state machine for guiding a user and an LLM through safe feature development in an existing brownfield monolith." \
  | grep "^ID:" | awk '{print $2}')
echo "STORY_ID=$STORY_ID"

echo ""
echo "=== Step 2: Add state variables ==="

# request namespace
$PY stories add-state-var $STORY_ID --key feature_request_set --type boolean --default false --category request --desc "request.featureRequest has been captured"
$PY stories add-state-var $STORY_ID --key business_goal_set --type boolean --default false --category request --desc "request.businessGoal has been captured"
$PY stories add-state-var $STORY_ID --key open_questions_exist --type boolean --default false --category request --desc "request.openQuestions is non-empty"

# systemUnderstanding namespace
$PY stories add-state-var $STORY_ID --key dep_confidence_adequate --type boolean --default false --category system --desc "dependencyMapConfidence >= 0.7"
$PY stories add-state-var $STORY_ID --key dep_confidence_critical --type boolean --default false --category system --desc "dependencyMapConfidence < 0.4 and docGaps exist — abort territory"
$PY stories add-state-var $STORY_ID --key candidate_modules_found --type boolean --default false --category system --desc "candidateModules or unknowns non-empty"

# baseline namespace
$PY stories add-state-var $STORY_ID --key baseline_adequate --type boolean --default false --category baseline --desc "characterizationCoverage >= 0.6 and invariants exist"
$PY stories add-state-var $STORY_ID --key needs_safety_net --type boolean --default false --category baseline --desc "characterizationCoverage < 0.6 or missingTestAreas non-empty"

# safety namespace
$PY stories add-state-var $STORY_ID --key safety_coverage_adequate --type boolean --default false --category safety --desc "coverageOnTouchedArea >= 0.7"

# spec namespace
$PY stories add-state-var $STORY_ID --key spec_complete --type boolean --default false --category spec --desc "targetBehavior, scopeBoundary, and acceptanceCriteria all set"

# risk namespace
$PY stories add-state-var $STORY_ID --key risk_feasible --type boolean --default false --category risk --desc "risk.feasible == true"
$PY stories add-state-var $STORY_ID --key risk_not_feasible --type boolean --default false --category risk --desc "risk.feasible == false"
$PY stories add-state-var $STORY_ID --key requires_seam --type boolean --default false --category risk --desc "risk.requiresSeam == true"
$PY stories add-state-var $STORY_ID --key seam_plan_complete --type boolean --default false --category risk --desc "seamPlan.seamType set and deployabilityPerStep non-empty"

# execution namespace
$PY stories add-state-var $STORY_ID --key tasks_defined --type boolean --default false --category execution --desc "taskList and definitionOfDonePerTask non-empty"
$PY stories add-state-var $STORY_ID --key context_assembled --type boolean --default false --category execution --desc "selectedContextFiles and taskPrompt set"
$PY stories add-state-var $STORY_ID --key patches_ready --type boolean --default false --category execution --desc "execution.patches non-empty"
$PY stories add-state-var $STORY_ID --key unexpected_findings --type boolean --default false --category execution --desc "execution.unexpectedFindings non-empty"

# validation namespace
$PY stories add-state-var $STORY_ID --key validation_passed --type boolean --default false --category validation --desc "validation.passed == true"
$PY stories add-state-var $STORY_ID --key validation_failures_exist --type boolean --default false --category validation --desc "validation.validationFailures non-empty"

# review namespace
$PY stories add-state-var $STORY_ID --key review_approved --type boolean --default false --category review --desc "review.approved == true"
$PY stories add-state-var $STORY_ID --key scope_drift --type boolean --default false --category review --desc "review.scopeDrift == true"

# release namespace
$PY stories add-state-var $STORY_ID --key release_deployable --type boolean --default false --category release --desc "release.deployable == true"

# runtime namespace
$PY stories add-state-var $STORY_ID --key runtime_healthy --type boolean --default false --category runtime --desc "runtime.healthy == true"
$PY stories add-state-var $STORY_ID --key rollback_triggered --type boolean --default false --category runtime --desc "runtime.rollbackTriggerState == true"

# governance namespace
$PY stories add-state-var $STORY_ID --key confidence_low --type boolean --default false --category governance --desc "governance.confidenceScore < 0.7"
$PY stories add-state-var $STORY_ID --key decision_logged --type boolean --default false --category governance --desc "governance.decisionLog non-empty"
$PY stories add-state-var $STORY_ID --key memory_updated --type boolean --default false --category governance --desc "governance.lastVerifiedAt set"
$PY stories add-state-var $STORY_ID --key coupling_hotspots --type boolean --default false --category governance --desc "risk.couplingHotspots non-empty"

echo ""
echo "=== Step 3: Create nodes ==="

# N0_Intake (start)
N0=$($PY stories add-node $STORY_ID \
  --title "Intake" \
  --content "Capture the requested feature and operating constraints.

Requires: (nothing — this is the entry point)
Collects: featureRequest, businessGoal, urgency, riskTolerance, targetUsers, knownConstraints, repoRef, environmentAvailable

Exit when: featureRequest is set and (repoRef is set OR environment is not available)" \
  --node-type task \
  --start \
  --json | extract_id)
echo "N0=$N0"

# N0a_ClarifyRequest
N0a=$($PY stories add-node $STORY_ID \
  --title "Clarify Request" \
  --content "Resolve ambiguity in the requested feature and assumptions.

Requires: request.featureRequest (partial)
Collects: openQuestions, resolvedAnswers, acceptedAssumptions

Exit when: featureRequest is set AND businessGoal is set" \
  --node-type task \
  --json | extract_id)
echo "N0a=$N0a"

# N1_SystemRecon
N1=$($PY stories add-node $STORY_ID \
  --title "System Recon" \
  --content "Map relevant modules, entrypoints, dependencies, and unknowns in the monolith.

Requires: request.featureRequest
Collects: candidateModules, entrypoints, callPaths, dataModels, externalIntegrations, ownershipSignals, existingDocs, unknowns, dependencyMapConfidence

Exit when: candidateModules or unknowns are non-empty" \
  --node-type task \
  --json | extract_id)
echo "N1=$N1"

# N1a_ContextRecovery
N1a=$($PY stories add-node $STORY_ID \
  --title "Context Recovery" \
  --content "Recover missing architecture and dependency context before specifying the change.

Requires: request.featureRequest, systemUnderstanding.unknowns
Collects: docGaps, tribalKnowledgeRequests, productionSignalsNeeded, codeReadingNotes, dependencyMapConfidence (updated)

Exit when: dependencyMapConfidence >= 0.7 OR docGaps non-empty" \
  --node-type task \
  --json | extract_id)
echo "N1a=$N1a"

# N2_BaselineBehavior
N2=$($PY stories add-node $STORY_ID \
  --title "Baseline Behavior" \
  --content "Document current behavior and invariants before making changes.

Requires: systemUnderstanding.candidateModules
Collects: currentBehavior, existingTests, observedFlows, invariants, nonfunctionalConstraints, baselineFailures, missingTestAreas, characterizationCoverage

Exit when: invariants non-empty AND currentBehavior non-empty" \
  --node-type task \
  --json | extract_id)
echo "N2=$N2"

# N2a_SafetyNetBuild
N2a=$($PY stories add-node $STORY_ID \
  --title "Safety-Net Build" \
  --content "Add characterization tests and observability to reduce regression risk.

Requires: baseline.currentBehavior, baseline.missingTestAreas
Collects: newCharacterizationTests, e2ePaths, fixtures, goldenOutputs, loggingHooks, coverageOnTouchedArea

Exit when: safety.coverageOnTouchedArea >= 0.7" \
  --node-type task \
  --json | extract_id)
echo "N2a=$N2a"

# N3_ChangeSpec
N3=$($PY stories add-node $STORY_ID \
  --title "Change Spec" \
  --content "Define the narrow feature delta and explicit acceptance criteria.

Requires: baseline.currentBehavior, baseline.invariants, request.featureRequest
Collects: currentBehaviorSummary, targetBehaviorSummary, specInvariants, scopeBoundary, acceptanceCriteria, excludedChanges, safety.rollbackPlan

Exit when: currentBehaviorSummary, targetBehaviorSummary, specInvariants, scopeBoundary, and acceptanceCriteria are all set" \
  --node-type task \
  --json | extract_id)
echo "N3=$N3"

# N4_FeasibilityAndRiskGate
N4=$($PY stories add-node $STORY_ID \
  --title "Feasibility and Risk Gate" \
  --content "Assess blast radius, architectural fit, and whether a seam is needed.

Requires: spec.targetBehaviorSummary, spec.scopeBoundary
Collects: blastRadius, riskLevel, couplingHotspots, securityImpact, dataIntegrityRisk, migrationNeed, feasible, requiresSeam, featureFlagStrategy, rollbackThresholds

Exit when: risk.feasible is determined AND risk.requiresSeam is determined" \
  --node-type task \
  --json | extract_id)
echo "N4=$N4"

# N4a_SeamCreationPlan
N4a=$($PY stories add-node $STORY_ID \
  --title "Seam Creation Plan" \
  --content "Define the adapter, facade, or flag seam needed before feature implementation.

Requires: risk.requiresSeam == true
Collects: seamType, adapterContract, facadePoints, intermediateState, deployabilityPerStep

Exit when: seamPlan.seamType is set AND deployabilityPerStep is non-empty" \
  --node-type task \
  --json | extract_id)
echo "N4a=$N4a"

# N5_TaskDecomposition
N5=$($PY stories add-node $STORY_ID \
  --title "Task Decomposition" \
  --content "Break the change into small, reversible tasks.

Requires: spec.targetBehaviorSummary, risk.feasible
Collects: taskList, taskDependencies, affectedFiles, parallelizableUnits, definitionOfDonePerTask, reviewCheckpoints

Exit when: taskList non-empty AND definitionOfDonePerTask non-empty" \
  --node-type task \
  --json | extract_id)
echo "N5=$N5"

# N6_PromptContextAssembly
N6=$($PY stories add-node $STORY_ID \
  --title "Prompt and Context Assembly" \
  --content "Prepare a bounded context package for the LLM.

Requires: execution.taskList
Collects: selectedContextFiles, architectureNotes, codingConventions, specExcerpt, taskPrompt, forbiddenChanges, successChecks

Exit when: selectedContextFiles non-empty AND taskPrompt is set AND successChecks non-empty" \
  --node-type task \
  --json | extract_id)
echo "N6=$N6"

# N7_Implementation
N7=$($PY stories add-node $STORY_ID \
  --title "Implementation" \
  --content "Generate and apply a bounded patch for the current task.

Requires: execution.taskPrompt, execution.selectedContextFiles
Collects: patches, filesChanged, rationale, assumptionsMade, todoFlags, unexpectedFindings

Exit when: patches non-empty OR unexpectedFindings non-empty" \
  --node-type task \
  --json | extract_id)
echo "N7=$N7"

# N8_LocalValidation
N8=$($PY stories add-node $STORY_ID \
  --title "Local Validation" \
  --content "Run lint, build, tests, and targeted verification.

Requires: execution.patches
Collects: lintResults, buildResults, testResults, contractResults, performanceSmoke, validationFailures, passed

Exit when: validation.passed == true OR validationFailures non-empty" \
  --node-type task \
  --json | extract_id)
echo "N8=$N8"

# N9_Review
N9=$($PY stories add-node $STORY_ID \
  --title "Review" \
  --content "Review for architecture fit, security, maintainability, and scope adherence.

Requires: validation.passed == true
Collects: reviewComments, architectureConformance, securityFindings, scopeDrift, maintainabilityNotes, approved

Exit when: review.approved == true OR reviewComments non-empty" \
  --node-type task \
  --json | extract_id)
echo "N9=$N9"

# N10_IntegrationAndFlagging
N10=$($PY stories add-node $STORY_ID \
  --title "Integration and Flagging" \
  --content "Prepare merge, feature flag configuration, and reversible deployment steps.

Requires: review.approved == true
Collects: mergeReadiness, featureFlagConfig, migrationSteps, releaseNotes, operationalChecks, deployable

Exit when: release.deployable == true" \
  --node-type task \
  --json | extract_id)
echo "N10=$N10"

# N11_RuntimeVerification
N11=$($PY stories add-node $STORY_ID \
  --title "Runtime Verification" \
  --content "Verify the feature under staging, canary, or production guardrails.

Requires: release.deployable == true
Collects: stagingResults, canaryMetrics, errorRate, latencyDelta, businessKpis, userFeedback, rollbackTriggerState, healthy

Exit when: runtime.healthy == true OR rollbackTriggerState == true" \
  --node-type task \
  --json | extract_id)
echo "N11=$N11"

# N10a_RollbackOrContain
N10a=$($PY stories add-node $STORY_ID \
  --title "Rollback or Contain" \
  --content "Disable, revert, or contain the change when runtime criteria fail.

Requires: runtime.rollbackTriggerState == true OR runtime.healthy == false
Collects: governance.decisionLog, governance.riskRegister, runtime.userFeedback

Exit when: governance.decisionLog non-empty" \
  --node-type task \
  --json | extract_id)
echo "N10a=$N10a"

# N12_LearnAndUpdateMemory (end - succeed)
N12=$($PY stories add-node $STORY_ID \
  --title "Learn and Update Memory" \
  --content "Persist new knowledge into docs, test assets, and future-agent context.

Requires: runtime.healthy == true
Collects: systemUnderstanding.existingDocs (updated), baseline.existingTests (updated), governance.assumptionLog, governance.decisionLog, governance.lastVerifiedAt

Exit when: governance.lastVerifiedAt is set" \
  --node-type succeed \
  --end \
  --json | extract_id)
echo "N12=$N12"

# N_abort (end - fail)
N_abort=$($PY stories add-node $STORY_ID \
  --title "Abort" \
  --content "Terminate the workflow because critical context or feasibility is missing.

Error: WorkflowAborted
Cause: Insufficient context or unacceptable implementation risk." \
  --node-type fail \
  --end \
  --json | extract_id)
echo "N_abort=$N_abort"

echo ""
echo "=== Step 4: Create choices (transitions) ==="

# N0_Intake → N0a_ClarifyRequest (when featureRequest or businessGoal not set)
$PY stories add-choice $N0 $N0a \
  --text "Feature request or business goal is missing — clarify before proceeding" \
  --requires-state '{"feature_request_set": false}' \
  --order 1

# N0_Intake → N1_SystemRecon (when featureRequest is set)
$PY stories add-choice $N0 $N1 \
  --text "Feature request captured — begin system reconnaissance" \
  --requires-state '{"feature_request_set": true}' \
  --order 2

# N0a_ClarifyRequest → N1_SystemRecon (when both are set)
$PY stories add-choice $N0a $N1 \
  --text "Request and business goal are clear — proceed to system recon" \
  --requires-state '{"feature_request_set": true, "business_goal_set": true}' \
  --order 1

# N1_SystemRecon → N1a_ContextRecovery (low confidence)
$PY stories add-choice $N1 $N1a \
  --text "Dependency map confidence below threshold — recover missing context" \
  --requires-state '{"dep_confidence_adequate": false}' \
  --order 1

# N1_SystemRecon → N2_BaselineBehavior (adequate confidence)
$PY stories add-choice $N1 $N2 \
  --text "System map confidence adequate — document baseline behavior" \
  --requires-state '{"dep_confidence_adequate": true}' \
  --order 2

# N1a_ContextRecovery → N2_BaselineBehavior (confidence recovered)
$PY stories add-choice $N1a $N2 \
  --text "Context recovered, confidence >= 0.7 — document baseline behavior" \
  --requires-state '{"dep_confidence_adequate": true}' \
  --order 1

# N1a_ContextRecovery → N_abort (critically low confidence + doc gaps)
$PY stories add-choice $N1a $N_abort \
  --text "Confidence critically low (<0.4) with unresolvable doc gaps — abort workflow" \
  --requires-state '{"dep_confidence_critical": true}' \
  --order 2

# N2_BaselineBehavior → N2a_SafetyNetBuild (insufficient coverage or missing tests)
$PY stories add-choice $N2 $N2a \
  --text "Characterization coverage < 0.6 or missing test areas — build safety net first" \
  --requires-state '{"needs_safety_net": true}' \
  --order 1

# N2_BaselineBehavior → N3_ChangeSpec (adequate baseline)
$PY stories add-choice $N2 $N3 \
  --text "Baseline coverage adequate and invariants documented — specify the change" \
  --requires-state '{"baseline_adequate": true}' \
  --order 2

# N2a_SafetyNetBuild → N3_ChangeSpec (safety coverage adequate)
$PY stories add-choice $N2a $N3 \
  --text "Safety coverage on touched area >= 0.7 — specify the change" \
  --requires-state '{"safety_coverage_adequate": true}' \
  --order 1

# N3_ChangeSpec → N0a_ClarifyRequest (business goal missing)
$PY stories add-choice $N3 $N0a \
  --text "Business goal still unclear during spec — return to clarify request" \
  --requires-state '{"business_goal_set": false}' \
  --order 1

# N3_ChangeSpec → N1_SystemRecon (confidence degraded during spec)
$PY stories add-choice $N3 $N1 \
  --text "Dependency confidence dropped during spec — re-run system recon" \
  --requires-state '{"dep_confidence_adequate": false}' \
  --order 2

# N3_ChangeSpec → N4_FeasibilityAndRiskGate (spec complete)
$PY stories add-choice $N3 $N4 \
  --text "Spec complete with target behavior and acceptance criteria — assess feasibility" \
  --requires-state '{"spec_complete": true}' \
  --order 3

# N4_FeasibilityAndRiskGate → N_abort (not feasible)
$PY stories add-choice $N4 $N_abort \
  --text "Risk assessment: implementation not feasible — abort" \
  --requires-state '{"risk_not_feasible": true}' \
  --order 1

# N4_FeasibilityAndRiskGate → N4a_SeamCreationPlan (feasible + seam required)
$PY stories add-choice $N4 $N4a \
  --text "Feasible but requires an adapter/facade/flag seam — plan the seam" \
  --requires-state '{"risk_feasible": true, "requires_seam": true}' \
  --order 2

# N4_FeasibilityAndRiskGate → N5_TaskDecomposition (feasible, no seam needed)
$PY stories add-choice $N4 $N5 \
  --text "Feasible with no seam required — decompose into tasks" \
  --requires-state '{"risk_feasible": true, "requires_seam": false}' \
  --order 3

# N4a_SeamCreationPlan → N5_TaskDecomposition (seam plan ready)
$PY stories add-choice $N4a $N5 \
  --text "Seam type defined and deployment steps planned — decompose into tasks" \
  --requires-state '{"seam_plan_complete": true}' \
  --order 1

# N5_TaskDecomposition → N6_PromptContextAssembly (tasks defined)
$PY stories add-choice $N5 $N6 \
  --text "Task list and definition of done defined — assemble LLM context" \
  --requires-state '{"tasks_defined": true}' \
  --order 1

# N6_PromptContextAssembly → N7_Implementation (context assembled)
$PY stories add-choice $N6 $N7 \
  --text "Context package ready with task prompt and selected files — implement" \
  --requires-state '{"context_assembled": true}' \
  --order 1

# N7_Implementation → N1a_ContextRecovery (unexpected findings + low confidence)
$PY stories add-choice $N7 $N1a \
  --text "Unexpected findings with low governance confidence — recover context before continuing" \
  --requires-state '{"unexpected_findings": true, "confidence_low": true}' \
  --order 1

# N7_Implementation → N6_PromptContextAssembly (no patches, no findings)
$PY stories add-choice $N7 $N6 \
  --text "No patches and no unexpected findings — re-assemble context and retry" \
  --requires-state '{"patches_ready": false, "unexpected_findings": false}' \
  --order 2

# N7_Implementation → N8_LocalValidation (patches generated)
$PY stories add-choice $N7 $N8 \
  --text "Patches generated — validate locally" \
  --requires-state '{"patches_ready": true}' \
  --order 3

# N8_LocalValidation → N2a_SafetyNetBuild (validation failed, missing test areas)
$PY stories add-choice $N8 $N2a \
  --text "Validation failed and missing test areas identified — strengthen safety net" \
  --requires-state '{"validation_passed": false, "needs_safety_net": true}' \
  --order 1

# N8_LocalValidation → N7_Implementation (validation failed)
$PY stories add-choice $N8 $N7 \
  --text "Validation failed — revise implementation" \
  --requires-state '{"validation_passed": false}' \
  --order 2

# N8_LocalValidation → N9_Review (validation passed)
$PY stories add-choice $N8 $N9 \
  --text "All validation checks passed — submit for review" \
  --requires-state '{"validation_passed": true}' \
  --order 3

# N9_Review → N4_FeasibilityAndRiskGate (scope drift detected)
$PY stories add-choice $N9 $N4 \
  --text "Scope drift detected during review — re-assess feasibility and risk" \
  --requires-state '{"scope_drift": true}' \
  --order 1

# N9_Review → N7_Implementation (review not approved)
$PY stories add-choice $N9 $N7 \
  --text "Review comments require changes — revise implementation" \
  --requires-state '{"review_approved": false}' \
  --order 2

# N9_Review → N10_IntegrationAndFlagging (review approved)
$PY stories add-choice $N9 $N10 \
  --text "Review approved — prepare integration and feature flagging" \
  --requires-state '{"review_approved": true}' \
  --order 3

# N10_IntegrationAndFlagging → N11_RuntimeVerification (deployable)
$PY stories add-choice $N10 $N11 \
  --text "Release package is deployable — verify in runtime environment" \
  --requires-state '{"release_deployable": true}' \
  --order 1

# N11_RuntimeVerification → N10a_RollbackOrContain (rollback triggered or unhealthy)
$PY stories add-choice $N11 $N10a \
  --text "Rollback triggered or runtime unhealthy — contain or revert the change" \
  --requires-state '{"rollback_triggered": true}' \
  --order 1

# N11_RuntimeVerification → N12_LearnAndUpdateMemory (healthy)
$PY stories add-choice $N11 $N12 \
  --text "Runtime healthy — persist learnings and close out the workflow" \
  --requires-state '{"runtime_healthy": true}' \
  --order 2

# N10a_RollbackOrContain → N1a_ContextRecovery (coupling hotspots exist)
$PY stories add-choice $N10a $N1a \
  --text "Coupling hotspots found during rollback analysis — recover architectural context" \
  --requires-state '{"coupling_hotspots": true}' \
  --order 1

# N10a_RollbackOrContain → N3_ChangeSpec (re-spec after rollback, no scope drift)
$PY stories add-choice $N10a $N3 \
  --text "Rollback complete, no scope drift — re-specify the change with new knowledge" \
  --requires-state '{"decision_logged": true, "scope_drift": false}' \
  --order 2

# N10a_RollbackOrContain → N4_FeasibilityAndRiskGate (scope drift or feasibility unclear)
$PY stories add-choice $N10a $N4 \
  --text "Scope drift or feasibility unclear after rollback — re-run risk gate" \
  --requires-state '{"scope_drift": true}' \
  --order 3

echo ""
echo "=== Step 5: Validate state schema ==="
$PY stories validate-state-schema $STORY_ID

echo ""
echo "=== Step 6: Validate graph structure ==="
$PY stories validate $STORY_ID

echo ""
echo "=== Step 7: Display story tree ==="
$PY stories tree $STORY_ID

echo ""
echo "=== Done! ==="
echo "Story ID: $STORY_ID"
echo "To publish: python main.py stories publish $STORY_ID"
