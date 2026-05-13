{
  "id": "brownfield-monolith-llm-feature-workflow",
  "version": "1.0.0",
  "title": "LLM-assisted feature delivery in a brownfield monolith",
  "description": "A review-oriented state machine spec for guiding a user and an LLM through safe feature development in an existing brownfield monolith.",
  "queryLanguage": "jsonlogic-like",
  "startAt": "N0_Intake",
  "terminalStates": [
    "N_abort",
    "N12_LearnAndUpdateMemory"
  ],
  "stateSchema": {
    "request": {
      "featureRequest": null,
      "businessGoal": null,
      "urgency": null,
      "riskTolerance": null,
      "targetUsers": [],
      "knownConstraints": [],
      "repoRef": null,
      "environmentAvailable": false,
      "openQuestions": [],
      "resolvedAnswers": [],
      "acceptedAssumptions": []
    },
    "systemUnderstanding": {
      "candidateModules": [],
      "entrypoints": [],
      "callPaths": [],
      "dataModels": [],
      "externalIntegrations": [],
      "ownershipSignals": [],
      "existingDocs": [],
      "unknowns": [],
      "docGaps": [],
      "tribalKnowledgeRequests": [],
      "productionSignalsNeeded": [],
      "codeReadingNotes": [],
      "dependencyMapConfidence": 0.0
    },
    "baseline": {
      "currentBehavior": [],
      "existingTests": [],
      "observedFlows": [],
      "invariants": [],
      "nonfunctionalConstraints": [],
      "baselineFailures": [],
      "missingTestAreas": [],
      "characterizationCoverage": 0.0
    },
    "safety": {
      "newCharacterizationTests": [],
      "e2ePaths": [],
      "fixtures": [],
      "goldenOutputs": [],
      "loggingHooks": [],
      "coverageOnTouchedArea": 0.0,
      "rollbackPlan": null,
      "rollbackThresholds": {},
      "featureFlagStrategy": null
    },
    "spec": {
      "currentBehaviorSummary": null,
      "targetBehaviorSummary": null,
      "specInvariants": [],
      "scopeBoundary": null,
      "acceptanceCriteria": [],
      "approved": false,
      "approvedBy": [],
      "excludedChanges": []
    },
    "risk": {
      "blastRadius": null,
      "riskLevel": null,
      "couplingHotspots": [],
      "securityImpact": null,
      "dataIntegrityRisk": null,
      "migrationNeed": false,
      "feasible": null,
      "requiresSeam": false
    },
    "seamPlan": {
      "seamType": null,
      "adapterContract": null,
      "facadePoints": [],
      "intermediateState": null,
      "deployabilityPerStep": []
    },
    "execution": {
      "taskList": [],
      "taskDependencies": [],
      "affectedFiles": [],
      "parallelizableUnits": [],
      "definitionOfDonePerTask": [],
      "reviewCheckpoints": [],
      "selectedContextFiles": [],
      "architectureNotes": [],
      "codingConventions": [],
      "specExcerpt": null,
      "taskPrompt": null,
      "forbiddenChanges": [],
      "successChecks": [],
      "patches": [],
      "filesChanged": [],
      "rationale": [],
      "assumptionsMade": [],
      "todoFlags": [],
      "unexpectedFindings": []
    },
    "validation": {
      "lintResults": null,
      "buildResults": null,
      "testResults": null,
      "contractResults": null,
      "performanceSmoke": null,
      "validationFailures": [],
      "passed": false
    },
    "review": {
      "reviewComments": [],
      "architectureConformance": null,
      "securityFindings": [],
      "scopeDrift": false,
      "maintainabilityNotes": [],
      "approved": false
    },
    "release": {
      "mergeReadiness": false,
      "featureFlagConfig": null,
      "migrationSteps": [],
      "releaseNotes": [],
      "operationalChecks": [],
      "deployable": false
    },
    "runtime": {
      "stagingResults": null,
      "canaryMetrics": {},
      "errorRate": null,
      "latencyDelta": null,
      "businessKpis": {},
      "userFeedback": [],
      "rollbackTriggerState": false,
      "healthy": false
    },
    "governance": {
      "confidenceScore": 0.0,
      "evidenceLinks": [],
      "assumptionLog": [],
      "decisionLog": [],
      "riskRegister": [],
      "lastVerifiedAt": null
    }
  },
  "states": {
    "N0_Intake": {
      "type": "task",
      "label": "Intake",
      "purpose": "Capture the requested feature and operating constraints.",
      "requires": [],
      "collects": [
        "request.featureRequest",
        "request.businessGoal",
        "request.urgency",
        "request.riskTolerance",
        "request.targetUsers",
        "request.knownConstraints",
        "request.repoRef",
        "request.environmentAvailable"
      ],
      "entryCriteria": [],
      "exitCriteria": [
        "request.featureRequest != null",
        "request.repoRef != null || request.environmentAvailable == false"
      ],
      "transitions": [
        {
          "to": "N0a_ClarifyRequest",
          "when": "request.featureRequest == null || request.businessGoal == null"
        },
        {
          "to": "N1_SystemRecon",
          "when": "request.featureRequest != null"
        }
      ]
    },
    "N0a_ClarifyRequest": {
      "type": "task",
      "label": "Clarify Request",
      "purpose": "Resolve ambiguity in the requested feature and assumptions.",
      "requires": [
        "request.featureRequest"
      ],
      "collects": [
        "request.openQuestions",
        "request.resolvedAnswers",
        "request.acceptedAssumptions"
      ],
      "entryCriteria": [
        "request.featureRequest == null || request.businessGoal == null || size(request.openQuestions) > 0"
      ],
      "exitCriteria": [
        "request.featureRequest != null",
        "request.businessGoal != null"
      ],
      "transitions": [
        {
          "to": "N1_SystemRecon",
          "when": "request.featureRequest != null && request.businessGoal != null"
        }
      ]
    },
    "N1_SystemRecon": {
      "type": "task",
      "label": "System Recon",
      "purpose": "Map relevant modules, entrypoints, dependencies, and unknowns in the monolith.",
      "requires": [
        "request.featureRequest"
      ],
      "collects": [
        "systemUnderstanding.candidateModules",
        "systemUnderstanding.entrypoints",
        "systemUnderstanding.callPaths",
        "systemUnderstanding.dataModels",
        "systemUnderstanding.externalIntegrations",
        "systemUnderstanding.ownershipSignals",
        "systemUnderstanding.existingDocs",
        "systemUnderstanding.unknowns",
        "systemUnderstanding.dependencyMapConfidence"
      ],
      "entryCriteria": [
        "request.featureRequest != null"
      ],
      "exitCriteria": [
        "size(systemUnderstanding.candidateModules) > 0 || size(systemUnderstanding.unknowns) > 0"
      ],
      "transitions": [
        {
          "to": "N1a_ContextRecovery",
          "when": "systemUnderstanding.dependencyMapConfidence < 0.7"
        },
        {
          "to": "N2_BaselineBehavior",
          "when": "systemUnderstanding.dependencyMapConfidence >= 0.7"
        }
      ]
    },
    "N1a_ContextRecovery": {
      "type": "task",
      "label": "Context Recovery",
      "purpose": "Recover missing architecture and dependency context before specifying change.",
      "requires": [
        "request.featureRequest",
        "systemUnderstanding.unknowns"
      ],
      "collects": [
        "systemUnderstanding.docGaps",
        "systemUnderstanding.tribalKnowledgeRequests",
        "systemUnderstanding.productionSignalsNeeded",
        "systemUnderstanding.codeReadingNotes",
        "systemUnderstanding.dependencyMapConfidence"
      ],
      "entryCriteria": [
        "systemUnderstanding.dependencyMapConfidence < 0.7"
      ],
      "exitCriteria": [
        "systemUnderstanding.dependencyMapConfidence >= 0.7 || size(systemUnderstanding.docGaps) > 0"
      ],
      "transitions": [
        {
          "to": "N2_BaselineBehavior",
          "when": "systemUnderstanding.dependencyMapConfidence >= 0.7"
        },
        {
          "to": "N_abort",
          "when": "systemUnderstanding.dependencyMapConfidence < 0.4 && size(systemUnderstanding.docGaps) > 0"
        }
      ]
    },
    "N2_BaselineBehavior": {
      "type": "task",
      "label": "Baseline Behavior",
      "purpose": "Document current behavior and invariants before making changes.",
      "requires": [
        "systemUnderstanding.candidateModules"
      ],
      "collects": [
        "baseline.currentBehavior",
        "baseline.existingTests",
        "baseline.observedFlows",
        "baseline.invariants",
        "baseline.nonfunctionalConstraints",
        "baseline.baselineFailures",
        "baseline.missingTestAreas",
        "baseline.characterizationCoverage"
      ],
      "entryCriteria": [
        "size(systemUnderstanding.candidateModules) > 0"
      ],
      "exitCriteria": [
        "size(baseline.invariants) > 0",
        "size(baseline.currentBehavior) > 0"
      ],
      "transitions": [
        {
          "to": "N2a_SafetyNetBuild",
          "when": "baseline.characterizationCoverage < 0.6 || size(baseline.missingTestAreas) > 0"
        },
        {
          "to": "N3_ChangeSpec",
          "when": "baseline.characterizationCoverage >= 0.6 && size(baseline.invariants) > 0"
        }
      ]
    },
    "N2a_SafetyNetBuild": {
      "type": "task",
      "label": "Safety-Net Build",
      "purpose": "Add characterization tests and observability to reduce regression risk.",
      "requires": [
        "baseline.currentBehavior",
        "baseline.missingTestAreas"
      ],
      "collects": [
        "safety.newCharacterizationTests",
        "safety.e2ePaths",
        "safety.fixtures",
        "safety.goldenOutputs",
        "safety.loggingHooks",
        "safety.coverageOnTouchedArea"
      ],
      "entryCriteria": [
        "baseline.characterizationCoverage < 0.6 || size(baseline.missingTestAreas) > 0"
      ],
      "exitCriteria": [
        "safety.coverageOnTouchedArea >= 0.7"
      ],
      "transitions": [
        {
          "to": "N3_ChangeSpec",
          "when": "safety.coverageOnTouchedArea >= 0.7"
        }
      ]
    },
    "N3_ChangeSpec": {
      "type": "task",
      "label": "Change Spec",
      "purpose": "Define the narrow feature delta and explicit acceptance criteria.",
      "requires": [
        "baseline.currentBehavior",
        "baseline.invariants",
        "request.featureRequest"
      ],
      "collects": [
        "spec.currentBehaviorSummary",
        "spec.targetBehaviorSummary",
        "spec.specInvariants",
        "spec.scopeBoundary",
        "spec.acceptanceCriteria",
        "spec.excludedChanges",
        "safety.rollbackPlan"
      ],
      "entryCriteria": [
        "size(baseline.currentBehavior) > 0",
        "size(baseline.invariants) > 0"
      ],
      "exitCriteria": [
        "spec.currentBehaviorSummary != null",
        "spec.targetBehaviorSummary != null",
        "size(spec.specInvariants) > 0",
        "spec.scopeBoundary != null",
        "size(spec.acceptanceCriteria) > 0"
      ],
      "transitions": [
        {
          "to": "N0a_ClarifyRequest",
          "when": "request.businessGoal == null"
        },
        {
          "to": "N1_SystemRecon",
          "when": "systemUnderstanding.dependencyMapConfidence < 0.7"
        },
        {
          "to": "N4_FeasibilityAndRiskGate",
          "when": "spec.targetBehaviorSummary != null && size(spec.acceptanceCriteria) > 0"
        }
      ]
    },
    "N4_FeasibilityAndRiskGate": {
      "type": "task",
      "label": "Feasibility and Risk Gate",
      "purpose": "Assess blast radius, architectural fit, and whether a seam is needed.",
      "requires": [
        "spec.targetBehaviorSummary",
        "spec.scopeBoundary"
      ],
      "collects": [
        "risk.blastRadius",
        "risk.riskLevel",
        "risk.couplingHotspots",
        "risk.securityImpact",
        "risk.dataIntegrityRisk",
        "risk.migrationNeed",
        "risk.feasible",
        "risk.requiresSeam",
        "safety.featureFlagStrategy",
        "safety.rollbackThresholds"
      ],
      "entryCriteria": [
        "spec.targetBehaviorSummary != null",
        "spec.scopeBoundary != null"
      ],
      "exitCriteria": [
        "risk.feasible != null",
        "risk.requiresSeam != null"
      ],
      "transitions": [
        {
          "to": "N_abort",
          "when": "risk.feasible == false"
        },
        {
          "to": "N4a_SeamCreationPlan",
          "when": "risk.feasible == true && risk.requiresSeam == true"
        },
        {
          "to": "N5_TaskDecomposition",
          "when": "risk.feasible == true && risk.requiresSeam == false"
        }
      ]
    },
    "N4a_SeamCreationPlan": {
      "type": "task",
      "label": "Seam Creation Plan",
      "purpose": "Define the adapter, facade, or flag seam needed before feature implementation.",
      "requires": [
        "risk.requiresSeam"
      ],
      "collects": [
        "seamPlan.seamType",
        "seamPlan.adapterContract",
        "seamPlan.facadePoints",
        "seamPlan.intermediateState",
        "seamPlan.deployabilityPerStep"
      ],
      "entryCriteria": [
        "risk.requiresSeam == true"
      ],
      "exitCriteria": [
        "seamPlan.seamType != null",
        "size(seamPlan.deployabilityPerStep) > 0"
      ],
      "transitions": [
        {
          "to": "N5_TaskDecomposition",
          "when": "seamPlan.seamType != null"
        }
      ]
    },
    "N5_TaskDecomposition": {
      "type": "task",
      "label": "Task Decomposition",
      "purpose": "Break the change into small, reversible tasks.",
      "requires": [
        "spec.targetBehaviorSummary",
        "risk.feasible"
      ],
      "collects": [
        "execution.taskList",
        "execution.taskDependencies",
        "execution.affectedFiles",
        "execution.parallelizableUnits",
        "execution.definitionOfDonePerTask",
        "execution.reviewCheckpoints"
      ],
      "entryCriteria": [
        "risk.feasible == true"
      ],
      "exitCriteria": [
        "size(execution.taskList) > 0",
        "size(execution.definitionOfDonePerTask) > 0"
      ],
      "transitions": [
        {
          "to": "N6_PromptContextAssembly",
          "when": "size(execution.taskList) > 0"
        }
      ]
    },
    "N6_PromptContextAssembly": {
      "type": "task",
      "label": "Prompt and Context Assembly",
      "purpose": "Prepare a bounded context package for the LLM.",
      "requires": [
        "execution.taskList"
      ],
      "collects": [
        "execution.selectedContextFiles",
        "execution.architectureNotes",
        "execution.codingConventions",
        "execution.specExcerpt",
        "execution.taskPrompt",
        "execution.forbiddenChanges",
        "execution.successChecks"
      ],
      "entryCriteria": [
        "size(execution.taskList) > 0"
      ],
      "exitCriteria": [
        "size(execution.selectedContextFiles) > 0",
        "execution.taskPrompt != null",
        "size(execution.successChecks) > 0"
      ],
      "transitions": [
        {
          "to": "N7_Implementation",
          "when": "execution.taskPrompt != null && size(execution.selectedContextFiles) > 0"
        }
      ]
    },
    "N7_Implementation": {
      "type": "task",
      "label": "Implementation",
      "purpose": "Generate and apply a bounded patch for the current task.",
      "requires": [
        "execution.taskPrompt",
        "execution.selectedContextFiles"
      ],
      "collects": [
        "execution.patches",
        "execution.filesChanged",
        "execution.rationale",
        "execution.assumptionsMade",
        "execution.todoFlags",
        "execution.unexpectedFindings"
      ],
      "entryCriteria": [
        "execution.taskPrompt != null"
      ],
      "exitCriteria": [
        "size(execution.patches) > 0 || size(execution.unexpectedFindings) > 0"
      ],
      "transitions": [
        {
          "to": "N1a_ContextRecovery",
          "when": "size(execution.unexpectedFindings) > 0 && governance.confidenceScore < 0.7"
        },
        {
          "to": "N6_PromptContextAssembly",
          "when": "size(execution.patches) == 0 && size(execution.unexpectedFindings) == 0"
        },
        {
          "to": "N8_LocalValidation",
          "when": "size(execution.patches) > 0"
        }
      ]
    },
    "N8_LocalValidation": {
      "type": "task",
      "label": "Local Validation",
      "purpose": "Run lint, build, tests, and targeted verification.",
      "requires": [
        "execution.patches"
      ],
      "collects": [
        "validation.lintResults",
        "validation.buildResults",
        "validation.testResults",
        "validation.contractResults",
        "validation.performanceSmoke",
        "validation.validationFailures",
        "validation.passed"
      ],
      "entryCriteria": [
        "size(execution.patches) > 0"
      ],
      "exitCriteria": [
        "validation.passed == true || size(validation.validationFailures) > 0"
      ],
      "transitions": [
        {
          "to": "N2a_SafetyNetBuild",
          "when": "validation.passed == false && size(baseline.missingTestAreas) > 0"
        },
        {
          "to": "N7_Implementation",
          "when": "validation.passed == false"
        },
        {
          "to": "N9_Review",
          "when": "validation.passed == true"
        }
      ]
    },
    "N9_Review": {
      "type": "task",
      "label": "Review",
      "purpose": "Review for architecture fit, security, maintainability, and scope adherence.",
      "requires": [
        "validation.passed"
      ],
      "collects": [
        "review.reviewComments",
        "review.architectureConformance",
        "review.securityFindings",
        "review.scopeDrift",
        "review.maintainabilityNotes",
        "review.approved"
      ],
      "entryCriteria": [
        "validation.passed == true"
      ],
      "exitCriteria": [
        "review.approved == true || size(review.reviewComments) > 0"
      ],
      "transitions": [
        {
          "to": "N4_FeasibilityAndRiskGate",
          "when": "review.scopeDrift == true"
        },
        {
          "to": "N7_Implementation",
          "when": "review.approved == false"
        },
        {
          "to": "N10_IntegrationAndFlagging",
          "when": "review.approved == true"
        }
      ]
    },
    "N10_IntegrationAndFlagging": {
      "type": "task",
      "label": "Integration and Flagging",
      "purpose": "Prepare merge, feature flag configuration, and reversible deployment steps.",
      "requires": [
        "review.approved"
      ],
      "collects": [
        "release.mergeReadiness",
        "release.featureFlagConfig",
        "release.migrationSteps",
        "release.releaseNotes",
        "release.operationalChecks",
        "release.deployable"
      ],
      "entryCriteria": [
        "review.approved == true"
      ],
      "exitCriteria": [
        "release.deployable == true"
      ],
      "transitions": [
        {
          "to": "N11_RuntimeVerification",
          "when": "release.deployable == true"
        }
      ]
    },
    "N11_RuntimeVerification": {
      "type": "task",
      "label": "Runtime Verification",
      "purpose": "Verify the feature under staging, canary, or production guardrails.",
      "requires": [
        "release.deployable"
      ],
      "collects": [
        "runtime.stagingResults",
        "runtime.canaryMetrics",
        "runtime.errorRate",
        "runtime.latencyDelta",
        "runtime.businessKpis",
        "runtime.userFeedback",
        "runtime.rollbackTriggerState",
        "runtime.healthy"
      ],
      "entryCriteria": [
        "release.deployable == true"
      ],
      "exitCriteria": [
        "runtime.healthy == true || runtime.rollbackTriggerState == true"
      ],
      "transitions": [
        {
          "to": "N10a_RollbackOrContain",
          "when": "runtime.rollbackTriggerState == true || runtime.healthy == false"
        },
        {
          "to": "N12_LearnAndUpdateMemory",
          "when": "runtime.healthy == true"
        }
      ]
    },
    "N10a_RollbackOrContain": {
      "type": "task",
      "label": "Rollback or Contain",
      "purpose": "Disable, revert, or contain the change when runtime criteria fail.",
      "requires": [
        "runtime.rollbackTriggerState"
      ],
      "collects": [
        "governance.decisionLog",
        "governance.riskRegister",
        "runtime.userFeedback"
      ],
      "entryCriteria": [
        "runtime.rollbackTriggerState == true || runtime.healthy == false"
      ],
      "exitCriteria": [
        "size(governance.decisionLog) > 0"
      ],
      "transitions": [
        {
          "to": "N1a_ContextRecovery",
          "when": "risk.couplingHotspots != null && size(risk.couplingHotspots) > 0"
        },
        {
          "to": "N3_ChangeSpec",
          "when": "spec.targetBehaviorSummary != null && review.scopeDrift == false"
        },
        {
          "to": "N4_FeasibilityAndRiskGate",
          "when": "review.scopeDrift == true || risk.feasible == null"
        }
      ]
    },
    "N12_LearnAndUpdateMemory": {
      "type": "succeed",
      "label": "Learn and Update Memory",
      "purpose": "Persist new knowledge into docs, test assets, and future-agent context.",
      "requires": [
        "runtime.healthy"
      ],
      "collects": [
        "systemUnderstanding.existingDocs",
        "baseline.existingTests",
        "governance.assumptionLog",
        "governance.decisionLog",
        "governance.lastVerifiedAt"
      ],
      "entryCriteria": [
        "runtime.healthy == true"
      ],
      "exitCriteria": [
        "governance.lastVerifiedAt != null"
      ],
      "end": true
    },
    "N_abort": {
      "type": "fail",
      "label": "Abort",
      "purpose": "Terminate the workflow because critical context or feasibility is missing.",
      "error": "WorkflowAborted",
      "cause": "Insufficient context or unacceptable implementation risk.",
      "end": true
    }
  }
}