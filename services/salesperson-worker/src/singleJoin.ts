/**
 * One meeting gets one Digital Twin.
 * Darren's 2:00 PM room on 2026-10-06 had two replicas because an API
 * meeting_url join and a calendar invite both fired for the same PAL.
 * Calendar RSVP can stay needsAction even after the calendar replica enters.
 */

export type JoinPath = "calendar" | "meeting_url";

export type JoinDecision = "use_calendar" | "use_meeting_url" | "already_covered" | "block_second_path";

export interface JoinState {
  palOnGuestList: boolean;
  meetingUrlAlreadyHasConversation: boolean;
  requestedPath: JoinPath;
}

export function decideMeetingJoin(state: JoinState): JoinDecision {
  if (state.meetingUrlAlreadyHasConversation) return "already_covered";
  if (state.palOnGuestList && state.requestedPath === "meeting_url") return "block_second_path";
  if (state.palOnGuestList || state.requestedPath === "calendar") return "use_calendar";
  return "use_meeting_url";
}

export function assertOneTwin(decision: JoinDecision): void {
  if (decision === "block_second_path" || decision === "already_covered") {
    throw new Error("A second Digital Twin join was blocked for this meeting.");
  }
}
