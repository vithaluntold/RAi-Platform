/**
 * useComplianceStateMachine — state machine hook for compliance analysis workflow.
 *
 * Manages stage transitions, guards, and status-to-stage mapping.
 * The compliance analysis follows a strict 7-stage pipeline:
 *   1. Upload → 2. Metadata → 3. Framework → 4. Standards → 5. Context → 6. Analysis → 7. Results
 */

import { useState, useCallback, useMemo } from "react";
import type {
  ComplianceSession,
  ComplianceSessionStatus,
  StageNumber,
} from "../types/compliance";
import { COMPLIANCE_STAGES } from "../types/compliance";

interface StageTransition {
  from: number;
  to: number;
  guard: (session: ComplianceSession) => boolean;
  errorMessage: string;
}

const STAGE_TRANSITIONS: StageTransition[] = [
  {
    from: 1,
    to: 2,
    guard: (s) =>
      !!s.financial_statements_filename && !!s.notes_filename,
    errorMessage: "Both financial statements and notes must be uploaded",
  },
  {
    from: 2,
    to: 3,
    guard: (s) => !!s.extracted_metadata && !s.extracted_metadata.error,
    errorMessage: "Metadata must be extracted before proceeding",
  },
  {
    from: 3,
    to: 4,
    guard: (s) => !!s.framework && s.framework.length > 0,
    errorMessage: "A compliance framework must be selected",
  },
  {
    from: 4,
    to: 5,
    guard: (s) =>
      !!s.selected_standards && s.selected_standards.length > 0,
    errorMessage: "At least one standard must be selected",
  },
  {
    from: 5,
    to: 6,
    guard: (s) =>
      !!s.selected_standards && s.selected_standards.length > 0,
    errorMessage: "Standards must be confirmed before analysis",
  },
  {
    from: 6,
    to: 7,
    guard: (s) =>
      s.status === "completed" && !!s.analysis_results,
    errorMessage: "Analysis must complete before viewing results",
  },
];

/** Map backend status to the appropriate stage number */
function statusToStage(status: ComplianceSessionStatus): number {
  switch (status) {
    case "awaiting_upload":
      return 1;
    case "processing":
      return 2;
    case "metadata_review":
      return 2;
    case "framework_selection":
      return 3;
    case "standards_selection":
      return 4;
    case "context_preview":
      return 5;
    case "analyzing":
      return 6;
    case "completed":
      return 7;
    case "failed":
      return 7;
    default:
      return 1;
  }
}

export interface UseComplianceStateMachineReturn {
  /** Current stage number (1-7) */
  currentStage: number;
  /** Label for the current stage */
  currentStageLabel: string;
  /** Description for the current stage */
  currentStageDescription: string;
  /** Whether navigation to a stage is allowed */
  canGoTo: (stage: number) => boolean;
  /** Attempt to navigate to a stage; returns error message or null */
  goTo: (stage: number) => string | null;
  /** Whether the user can move forward */
  canAdvance: boolean;
  /** Whether the user can move backward */
  canGoBack: boolean;
  /** Advance to next stage */
  advance: () => string | null;
  /** Go back to previous stage */
  goBack: () => string | null;
  /** Set stage from session status (sync with backend) */
  syncFromSession: (session: ComplianceSession) => void;
  /** All stage definitions */
  stages: typeof COMPLIANCE_STAGES;
  /** Get the highest reachable stage based on session state */
  maxReachableStage: number;
}

export function useComplianceStateMachine(
  initialSession?: ComplianceSession | null
): UseComplianceStateMachineReturn {
  const [currentStage, setCurrentStage] = useState<number>(
    initialSession ? statusToStage(initialSession.status) : 1
  );
  const [session, setSession] = useState<ComplianceSession | null>(
    initialSession ?? null
  );

  const maxReachableStage = useMemo(() => {
    if (!session) return 1;
    let maxStage = 1;
    for (const transition of STAGE_TRANSITIONS) {
      if (transition.guard(session)) {
        maxStage = Math.max(maxStage, transition.to);
      } else {
        break;
      }
    }
    return maxStage;
  }, [session]);

  const canGoTo = useCallback(
    (stage: number): boolean => {
      if (stage < 1 || stage > 7) return false;
      if (stage <= currentStage) return true;
      if (!session) return stage === 1;
      return stage <= maxReachableStage;
    },
    [currentStage, session, maxReachableStage]
  );

  const goTo = useCallback(
    (stage: number): string | null => {
      if (stage < 1 || stage > 7) return "Invalid stage";

      // Always allow going backward
      if (stage <= currentStage) {
        setCurrentStage(stage);
        return null;
      }

      if (!session) {
        if (stage === 1) {
          setCurrentStage(1);
          return null;
        }
        return "No session available";
      }

      // Check all transitions up to the target stage
      for (const transition of STAGE_TRANSITIONS) {
        if (transition.to <= stage && transition.from < stage) {
          if (!transition.guard(session)) {
            return transition.errorMessage;
          }
        }
      }

      setCurrentStage(stage);
      return null;
    },
    [currentStage, session]
  );

  const canAdvance = useMemo(
    () => canGoTo(currentStage + 1),
    [canGoTo, currentStage]
  );

  const canGoBack = useMemo(() => currentStage > 1, [currentStage]);

  const advance = useCallback(
    (): string | null => goTo(currentStage + 1),
    [goTo, currentStage]
  );

  const goBack = useCallback(
    (): string | null => goTo(currentStage - 1),
    [goTo, currentStage]
  );

  const syncFromSession = useCallback(
    (newSession: ComplianceSession) => {
      setSession(newSession);
      const derivedStage = statusToStage(newSession.status);
      setCurrentStage(derivedStage);
    },
    []
  );

  const stageInfo = COMPLIANCE_STAGES[currentStage as StageNumber] ?? {
    label: "Unknown",
    description: "",
  };

  return {
    currentStage,
    currentStageLabel: stageInfo.label,
    currentStageDescription: stageInfo.description,
    canGoTo,
    goTo,
    canAdvance,
    canGoBack,
    advance,
    goBack,
    syncFromSession,
    stages: COMPLIANCE_STAGES,
    maxReachableStage,
  };
}
