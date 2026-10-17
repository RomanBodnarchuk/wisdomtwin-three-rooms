import assert from "node:assert/strict";
import test from "node:test";

import { GrantClaimError } from "../src/errors.ts";
import {
  CANADA_GRANT_OUTBOUND_ENABLED,
  PROVINCE_CODES,
  assertNotANationalOntarioCopy,
  assertProspectDispatchAllowed,
  assertSpokenGrantClaim,
  listGrantPrograms,
  normalizeProvince,
  spokenGrantSentences,
} from "../src/grants.ts";

const AS_OF = "2026-10-16";

test("every province and territory has one official program record", () => {
  const programs = listGrantPrograms();
  assert.deepEqual(
    programs.map((program) => program.code).sort(),
    [...PROVINCE_CODES].sort(),
  );
  const urls = new Set(programs.map((program) => program.officialUrl));
  assert.equal(urls.size, programs.length);
  for (const program of programs) {
    assert.match(program.officialUrl, /^https:\/\//);
    assert.ok(program.sentences.length > 0);
    assert.match(program.sentences.join(" "), /N5R is not/);
    assert.equal(program.sentences.join(" ").includes("—"), false);
  }
});

test("Ontario can be quoted and cannot be copied nationwide", () => {
  const sentences = spokenGrantSentences("Ontario", AS_OF);
  assert.match(sentences[0], /\$10,000 per trainee/);
  assert.equal(sentences.join(" ").includes("cannot start before approval"), false);
  assertSpokenGrantClaim("ON", sentences[1], AS_OF);
  assert.throws(
    () => assertNotANationalOntarioCopy("Every province has a grant program like Ontario does."),
    GrantClaimError,
  );
  assert.throws(
    () => assertSpokenGrantClaim("British Columbia", sentences[0], AS_OF),
    /not approved for this region/,
  );
});

test("British Columbia does not inherit Ontario's start rule", () => {
  const sentences = spokenGrantSentences("B.C.", AS_OF);
  assert.match(sentences.join(" "), /may begin before a decision/);
  assert.equal(sentences.join(" ").includes("$15,000"), false);
  assert.equal(normalizeProvince("British Columbia"), "BC");
});

test("closed and unquoted regions cannot be given a dollar grant", () => {
  for (const region of ["Saskatchewan", "Quebec", "Newfoundland and Labrador", "Nunavut", "New Brunswick"]) {
    const sentences = spokenGrantSentences(region, AS_OF);
    assert.equal(sentences.join(" ").includes("$"), false);
    assert.throws(
      () => assertSpokenGrantClaim(region, "You can get up to $10,000 per employee.", AS_OF),
      GrantClaimError,
    );
  }
  assert.match(spokenGrantSentences("NL", AS_OF)[0], /not being accepted/);
  assert.match(spokenGrantSentences("SK", AS_OF)[0], /would be eliminated/);
});

test("Nova Scotia's intake date expires after October 18, 2026", () => {
  assert.match(spokenGrantSentences("Nova Scotia", "2026-10-18").join(" "), /October 18, 2026/);
  assert.equal(spokenGrantSentences("NS", "2026-10-19").join(" ").includes("October 18, 2026"), false);
  assert.throws(
    () =>
      assertSpokenGrantClaim(
        "NS",
        "The Fall 2026 intake opened on September 28, 2026 and closes at midnight on October 18, 2026.",
        "2026-10-19",
      ),
    GrantClaimError,
  );
});

test("an unknown location cannot borrow Ontario's rules", () => {
  const sentences = spokenGrantSentences("Canada", AS_OF);
  assert.equal(sentences.length, 1);
  assert.match(sentences[0], /will not apply Ontario's grant rules/);
  assert.equal(normalizeProvince(""), null);
});

test("prospect dispatch stays off", () => {
  assert.equal(CANADA_GRANT_OUTBOUND_ENABLED, false);
  assert.throws(() => assertProspectDispatchAllowed(), /stay off/);
});
