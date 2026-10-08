import assert from "node:assert/strict";
import test from "node:test";

import { assertOneTwin, decideMeetingJoin } from "../src/singleJoin.ts";

test("calendar invite alone is the join", () => {
  assert.equal(
    decideMeetingJoin({
      palOnGuestList: true,
      meetingUrlAlreadyHasConversation: false,
      requestedPath: "calendar",
    }),
    "use_calendar",
  );
});

test("API join is blocked once the PAL is already a guest", () => {
  const decision = decideMeetingJoin({
    palOnGuestList: true,
    meetingUrlAlreadyHasConversation: false,
    requestedPath: "meeting_url",
  });
  assert.equal(decision, "block_second_path");
  assert.throws(() => assertOneTwin(decision), /second Digital Twin/);
});

test("a second join is blocked when a conversation already owns the Meet link", () => {
  assert.equal(
    decideMeetingJoin({
      palOnGuestList: false,
      meetingUrlAlreadyHasConversation: true,
      requestedPath: "meeting_url",
    }),
    "already_covered",
  );
});

test("API join is allowed only when nobody has started a twin for that room", () => {
  assert.equal(
    decideMeetingJoin({
      palOnGuestList: false,
      meetingUrlAlreadyHasConversation: false,
      requestedPath: "meeting_url",
    }),
    "use_meeting_url",
  );
});
