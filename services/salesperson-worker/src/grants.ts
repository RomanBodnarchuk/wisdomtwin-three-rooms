import { GrantClaimError } from "./errors.ts";

/**
 * Spoken training-grant claims, checked against official pages on 2026-10-16.
 * Ontario's rules are not reused for any other province or territory.
 * Prospect dispatch stays off. N5R is not claimed as an approved provider.
 */

export const GRANT_CHECKED_ON = "2026-10-16";
export const CANADA_GRANT_OUTBOUND_ENABLED = false;

export const PROVINCE_CODES = [
  "AB",
  "BC",
  "MB",
  "NB",
  "NL",
  "NS",
  "NT",
  "NU",
  "ON",
  "PE",
  "QC",
  "SK",
  "YT",
] as const;

export type ProvinceCode = (typeof PROVINCE_CODES)[number];
export type GrantMode = "quotable" | "closed" | "unquotable";

export interface GrantProgram {
  readonly code: ProvinceCode;
  readonly regionName: string;
  readonly programName: string;
  readonly mode: GrantMode;
  readonly officialUrl: string;
  readonly sentences: readonly string[];
  readonly deadlineSentence?: {
    readonly through: string;
    readonly text: string;
  };
}

const UNKNOWN_REGION_SENTENCE =
  "I need the business location before I can discuss a training program. I will not apply Ontario's grant rules outside Ontario.";

const PROGRAMS: readonly GrantProgram[] = [
  {
    code: "ON",
    regionName: "Ontario",
    programName: "Ontario Job Grant",
    mode: "quotable",
    officialUrl: "https://www.ontario.ca/page/ontario-job-grant",
    sentences: [
      "The Ontario Job Grant can support eligible training costs up to $10,000 per trainee. It does not pay that amount for every employee.",
      "Employers with 100 or more employees pay half of the training costs. Employers with fewer than 100 pay at least one-sixth.",
      "A small employer training a previously unemployed new hire may qualify for up to $15,000 per trainee without a minimum contribution. That is not free training for the current team.",
      "An approved third-party trainer must deliver the training in Ontario. Vendor product training and business consulting are excluded.",
      "The ministry is accepting individual-employer applications for 25 or fewer participants, and an employer submits one application at a time. Meeting the rules does not guarantee funding.",
      "N5R is not the Government of Ontario, and I am not saying N5R is an approved training provider.",
    ],
  },
  {
    code: "BC",
    regionName: "British Columbia",
    programName: "B.C. Employer Training Grant",
    mode: "quotable",
    officialUrl: "https://www.workbc.ca/employers-industry/funding-programs/bc-employer-training-grant",
    sentences: [
      "The B.C. Employer Training Grant can reimburse 80 percent of eligible training costs, up to $10,000 per participant and $300,000 per employer each fiscal year from April 1 to March 31. The employer pays the other 20 percent.",
      "Training has to lead to a better job, more job security, or a job for an unemployed person. An application can be returned unassessed. Funding is not guaranteed.",
      "Training may begin before a decision. If it begins and the application is denied, the employer pays the full cost.",
      "N5R is not the Government of British Columbia, and I am not saying N5R is an eligible trainer.",
    ],
  },
  {
    code: "AB",
    regionName: "Alberta",
    programName: "Canada-Alberta Productivity Grant",
    mode: "quotable",
    officialUrl: "https://www.alberta.ca/canada-alberta-productivity-grant",
    sentences: [
      "The Canada-Alberta Productivity Grant can cover 75 percent of eligible training costs, up to $5,000 per employed trainee in a fiscal year and $100,000 per employer in a fiscal year. The employer pays the other 25 percent.",
      "The employer completes the application before training starts. Employee wages and consultant services are not eligible costs.",
      "Alberta lists AI for Business and Generative AI Applications as examples of digital skills courses. That list does not make N5R training eligible.",
      "N5R is not the Government of Alberta, and I am not saying N5R is an eligible trainer.",
    ],
  },
  {
    code: "MB",
    regionName: "Manitoba",
    programName: "Building Up Manitoba Program",
    mode: "quotable",
    officialUrl: "https://www.manitoba.ca/jec/busdev/financial/bump/index.html",
    sentences: [
      "The Building Up Manitoba Program can reimburse 50 percent of eligible employee-training costs, up to $10,000 per employee, for employers with fewer than 500 employees.",
      "The combined maximum across its two streams is $100,000. A funding agreement cannot run past March 31 of the fiscal year in which the employer applies.",
      "Employers with 500 or more employees are not eligible. The Canada-Manitoba Job Grant has been discontinued.",
      "N5R is not the Government of Manitoba, and I am not saying N5R is an eligible trainer.",
    ],
  },
  {
    code: "QC",
    regionName: "Quebec",
    programName: "Programme de formation de la main-d'oeuvre",
    mode: "unquotable",
    officialUrl:
      "https://www.quebec.ca/entreprises-et-travailleurs-autonomes/administrer-gerer/embauche-gestion-personnel/former-main-oeuvre/developper-competences",
    sentences: [
      "Quebec does not run the Ontario Job Grant. Services Québec sets any direct training subsidy case by case, with no per-trainee cap on the public page. Productivité-Compétences funds collective training projects and is not that employer grant. I will not quote a dollar amount. N5R is not the Government of Quebec, and I am not saying N5R is an approved provider.",
    ],
  },
  {
    code: "NB",
    regionName: "New Brunswick",
    programName: "Labour Force Training",
    mode: "unquotable",
    officialUrl: "https://www.gnb.ca/en/news/n-b.2026.09.new-brunswick-supports-local-business-tariffs-escalate.html",
    sentences: [
      "New Brunswick's WorkingNB Labour Force Training program exists. The September 10, 2026 notice said caps were raised and did not publish the new amounts, so I will not quote a dollar figure. N5R is not the Government of New Brunswick, and I am not saying N5R is an approved provider.",
    ],
  },
  {
    code: "NS",
    regionName: "Nova Scotia",
    programName: "Workplace Innovation and Productivity Skills Incentive",
    mode: "quotable",
    officialUrl: "https://novascotia.ca/programs/workplace-innovation-productivity-skills-incentive/",
    sentences: [
      "Nova Scotia's Workplace Innovation and Productivity Skills Incentive may fund up to 75 percent of eligible training costs. The public page does not publish a per-trainee dollar cap.",
      "The applicant pays the remaining cost. An application is assessed, and funding is not guaranteed.",
      "N5R is not the Government of Nova Scotia, and I am not saying N5R is an approved provider.",
    ],
    deadlineSentence: {
      through: "2026-10-18",
      text: "The Fall 2026 intake opened on September 28, 2026 and closes at midnight on October 18, 2026.",
    },
  },
  {
    code: "PE",
    regionName: "Prince Edward Island",
    programName: "Workplace Skills Training",
    mode: "quotable",
    officialUrl: "https://www.princeedwardisland.ca/en/service/workplace-skills-training",
    sentences: [
      "Prince Edward Island's Workplace Skills Training page says SkillsPEI can contribute up to 50 percent of direct training costs, and the employer pays the rest. That page was published on May 19, 2023, so the current rule has to be confirmed before anyone applies.",
      "Training that is part of normal business operations is not eligible. Training starts after SkillsPEI confirms approval. Funding is not guaranteed.",
      "N5R is not the Government of Prince Edward Island, and I am not saying N5R is an approved provider.",
    ],
  },
  {
    code: "NL",
    regionName: "Newfoundland and Labrador",
    programName: "Canada-Newfoundland and Labrador Job Grant",
    mode: "closed",
    officialUrl: "https://www.gov.nl.ca/jgrd/empservices/foremployers/canada-nl-job-grant/",
    sentences: [
      "The Canada-Newfoundland and Labrador Job Grant is suspended until further notice, and new applications are not being accepted. I will not quote its former dollar amounts as available funding. N5R is not the Government of Newfoundland and Labrador.",
    ],
  },
  {
    code: "SK",
    regionName: "Saskatchewan",
    programName: "Canada-Saskatchewan Job Grant",
    mode: "unquotable",
    officialUrl:
      "https://www.saskatchewan.ca/government/news-and-media/2025/march/19/delivering-essential-skills-training-despite-federal-government-cuts",
    sentences: [
      "On March 19, 2025, Saskatchewan said the Canada-Saskatchewan Job Grant would be eliminated. I do not have a verified open replacement with a published cap, so I will not quote a training grant. N5R is not the Government of Saskatchewan.",
    ],
  },
  {
    code: "NT",
    regionName: "Northwest Territories",
    programName: "Employee Training Program",
    mode: "quotable",
    officialUrl: "https://www.ece.gov.nt.ca/en/services/career-employment-and-training-services/employee-training-program",
    sentences: [
      "The Northwest Territories Employee Training Program says assistance will not exceed $13,000 per individual client per 52 weeks.",
      "Training must be short term, from an eligible third-party institution, and the employer must have a job for the person at the end. The employer applies within three months of that person starting the position.",
      "That cap is a maximum, not a promise of funding. N5R is not the Government of the Northwest Territories, and I am not saying N5R is an eligible trainer.",
    ],
  },
  {
    code: "NU",
    regionName: "Nunavut",
    programName: "Grant for Nunavut Employers",
    mode: "unquotable",
    officialUrl: "https://www.gov.nu.ca/en/forms/456-grant-nunavut-employers-application-package-gne",
    sentences: [
      "Nunavut has a Grant for Nunavut Employers. Its application package and department policy do not state the same cap, so I will not quote a dollar amount. N5R is not the Government of Nunavut, and I am not saying N5R is an approved provider.",
    ],
  },
  {
    code: "YT",
    regionName: "Yukon",
    programName: "Staffing UP",
    mode: "quotable",
    officialUrl: "https://yukon.ca/en/staffing-up-program-guidelines",
    sentences: [
      "Yukon's Staffing UP program negotiates a portion of eligible project costs, up to 50 percent. Funding is not guaranteed even when a project meets the eligibility criteria.",
      "The training costs it describes are for third-party courses that result in a certificate, diploma, or credential. It is not a per-trainee Ontario Job Grant.",
      "N5R is not the Government of Yukon, and I am not saying N5R is an eligible provider.",
    ],
  },
];

const BY_CODE = new Map(PROGRAMS.map((program) => [program.code, program]));

const ALIASES: Record<string, ProvinceCode> = {
  ab: "AB",
  alberta: "AB",
  bc: "BC",
  "british columbia": "BC",
  mb: "MB",
  manitoba: "MB",
  nb: "NB",
  "new brunswick": "NB",
  nl: "NL",
  nfld: "NL",
  newfoundland: "NL",
  "newfoundland and labrador": "NL",
  ns: "NS",
  "nova scotia": "NS",
  nt: "NT",
  nwt: "NT",
  "northwest territories": "NT",
  nu: "NU",
  nunavut: "NU",
  on: "ON",
  ontario: "ON",
  pe: "PE",
  pei: "PE",
  "prince edward island": "PE",
  qc: "QC",
  quebec: "QC",
  québec: "QC",
  sk: "SK",
  saskatchewan: "SK",
  yt: "YT",
  yukon: "YT",
};

const COPIED_ONTARIO_CLAIM = /every province|all canadian business|grant program like ontario|same as ontario/i;

function normalizeKey(input: string): string {
  return input.trim().toLowerCase().replace(/\./g, "").replace(/\s+/g, " ");
}

function exactSentence(input: string): string {
  return input.trim().replace(/\s+/g, " ");
}

export function listGrantPrograms(): readonly GrantProgram[] {
  return PROGRAMS;
}

export function normalizeProvince(input: string): ProvinceCode | null {
  return ALIASES[normalizeKey(input)] ?? null;
}

export function grantProgram(code: ProvinceCode): GrantProgram {
  const program = BY_CODE.get(code);
  if (!program) throw new GrantClaimError("Unknown Canadian region.");
  return program;
}

export function spokenGrantSentences(region: string, asOf: string): readonly string[] {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(asOf)) {
    throw new GrantClaimError("A grant claim needs the date it will be spoken.");
  }
  const code = normalizeProvince(region);
  if (!code) return [UNKNOWN_REGION_SENTENCE];
  const program = grantProgram(code);
  const sentences = [...program.sentences];
  if (program.deadlineSentence && asOf <= program.deadlineSentence.through) {
    sentences.push(program.deadlineSentence.text);
  }
  return sentences;
}

export function assertNotANationalOntarioCopy(sentence: string): void {
  if (COPIED_ONTARIO_CLAIM.test(sentence)) {
    throw new GrantClaimError("Ontario's grant rules cannot be copied onto another province.");
  }
}

export function assertSpokenGrantClaim(region: string, sentence: string, asOf: string): void {
  assertNotANationalOntarioCopy(sentence);
  const allowed = spokenGrantSentences(region, asOf).map(exactSentence);
  if (!allowed.includes(exactSentence(sentence))) {
    throw new GrantClaimError("That grant sentence is not approved for this region.");
  }
}

export function assertProspectDispatchAllowed(): void {
  if (CANADA_GRANT_OUTBOUND_ENABLED) return;
  throw new GrantClaimError("Canadian grant prospect calls, texts, and email stay off.");
}
