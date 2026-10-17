# Canadian training programs are not one Ontario grant

Checked October 16, 2026. No prospect was called, texted, or emailed. The installed N5R voice agent was not changed. Outbound stays off.

The premise that every province has a grant program like Ontario does is false. Each government publishes its own program, its own cap, and its own trainer rules. Some programs are suspended or were announced for elimination. Territories are included because the request was all Canadian businesses.

The only sentences that may be spoken are the ones returned by `spokenGrantSentences` in `services/salesperson-worker/src/grants.ts`. A sentence that copies Ontario onto another region is rejected. `assertProspectDispatchAllowed` still refuses prospect calls, texts, and email.

N5R is not claimed as an approved or eligible provider in any province or territory. That question is unverified everywhere.

## What may be said

| Region | Program checked | What the gate allows |
| --- | --- | --- |
| Ontario | [Ontario Job Grant](https://www.ontario.ca/page/ontario-job-grant), public page updated October 16, 2026 | Up to $10,000 per trainee, not per employee. Employers with 100 or more pay half. Employers with fewer than 100 pay at least one-sixth. A small employer training a previously unemployed new hire may qualify for up to $15,000 with no minimum contribution. That is not free training for the current team. Third-party training in Ontario. Vendor product training and business consulting are excluded. Current individual-employer intake is 25 or fewer participants, one application at a time. Meeting the rules does not guarantee funding. |
| British Columbia | [B.C. Employer Training Grant](https://www.workbc.ca/employers-industry/funding-programs/bc-employer-training-grant) | 80 percent of eligible costs, up to $10,000 per participant and $300,000 per employer each fiscal year from April 1 to March 31. The employer pays 20 percent. Training may begin before a decision, and a denial leaves the employer with the full cost. Applications can be returned unassessed. |
| Alberta | [Canada-Alberta Productivity Grant](https://www.alberta.ca/canada-alberta-productivity-grant) | 75 percent of eligible costs, up to $5,000 per employed trainee and $100,000 per employer in a fiscal year. The employer pays 25 percent and applies before training starts. Wages and consultant services are not eligible. Alberta's examples include AI for Business and Generative AI Applications. Those examples do not make N5R eligible. |
| Manitoba | [Building Up Manitoba Program](https://www.manitoba.ca/jec/busdev/financial/bump/index.html) | 50 percent, up to $10,000 per employee, for employers with fewer than 500 employees. Combined cap $100,000. The agreement cannot run past the fiscal year of the application. The [Canada-Manitoba Job Grant has been discontinued](https://www.gov.mb.ca/jec/busdev/financial/cmjg/). |
| Quebec | [Programme de formation de la main-d'oeuvre](https://www.quebec.ca/entreprises-et-travailleurs-autonomes/administrer-gerer/embauche-gestion-personnel/former-main-oeuvre/developper-competences), page updated March 31, 2026 | No dollar amount. Services Québec decides a direct subsidy case by case. Productivité-Compétences funds collective projects. It is not an employer grant with a published per-trainee cap. |
| New Brunswick | [September 10, 2026 WorkingNB notice](https://www.gnb.ca/en/news/n-b.2026.09.new-brunswick-supports-local-business-tariffs-escalate.html) | The Labour Force Training program exists and the notice said caps were raised. It did not publish the new amounts. No dollar amount. The program page itself did not return rules on this check. |
| Nova Scotia | [Workplace Innovation and Productivity Skills Incentive](https://novascotia.ca/programs/workplace-innovation-productivity-skills-incentive/) | Up to 75 percent of eligible training costs. No per-trainee cap was published. The Fall 2026 intake closes at midnight on October 18, 2026. The gate stops speaking that date on October 19. |
| Prince Edward Island | [Workplace Skills Training](https://www.princeedwardisland.ca/en/service/workplace-skills-training), page dated May 19, 2023 | Up to 50 percent of direct training costs, with the published date spoken so the rule is confirmed before anyone applies. Normal business operations are excluded. Training starts after SkillsPEI confirms approval. |
| Newfoundland and Labrador | [Canada-Newfoundland and Labrador Job Grant](https://www.gov.nl.ca/jgrd/empservices/foremployers/canada-nl-job-grant/) | Suspended. New applications are not being accepted. Former dollar amounts are not spoken as available funding. |
| Saskatchewan | [March 19, 2025 announcement](https://www.saskatchewan.ca/government/news-and-media/2025/march/19/delivering-essential-skills-training-despite-federal-government-cuts) | The province said the Canada-Saskatchewan Job Grant would be eliminated. No open replacement with a published cap was verified. No dollar amount. Older Saskatchewan pages still describe the old grant. Those pages are not a quote source. |
| Northwest Territories | [Employee Training Program](https://www.ece.gov.nt.ca/en/services/career-employment-and-training-services/employee-training-program) | Assistance will not exceed $13,000 per individual client per 52 weeks. That is a maximum, not a promise. Third-party training, a job at the end, and an application within three months of the person starting the position. |
| Nunavut | [Grant for Nunavut Employers application package](https://www.gov.nu.ca/en/forms/456-grant-nunavut-employers-application-package-gne) | A program exists. The application package and the department policy do not state the same cap, so no dollar amount is spoken. |
| Yukon | [Staffing UP guidelines](https://yukon.ca/en/staffing-up-program-guidelines), file updated May 28, 2026 | Negotiated funding up to 50 percent of eligible project costs. Not guaranteed. Training costs it describes are for third-party courses that result in a certificate, diploma, or credential. Not a per-trainee Ontario Job Grant. |

Federal Job Bank still lists older names, including the Canada-Alberta Job Grant, the Canada-Saskatchewan Job Grant, and the Canada-Manitoba Job Grant. Do not quote Job Bank over the provincial page.

## What stays in place

The installed Ontario voice script on `agent_9601` was not edited. It still ends a grant path outside Ontario. Do not point that agent at the rest of Canada, and do not move the US Twilio number onto a Canadian campaign.

The national draft is `docs/sales-ops/prompts/live/n5r-canada-grant-hook-voice.md`. It is not installed on ElevenLabs or Tavus.

The October 16, 2026 Ontario overview does not state that training cannot start before approval. The national gate therefore does not speak that sentence. British Columbia's page says the opposite: training may begin before a decision, and a denial leaves the employer with the cost. The installed N5R meeting prompt still says Ontario training cannot start before approval. That file was not edited in this pass.

CASL and the CRTC unsolicited-telecommunications rules still apply in every province and territory. Synthesized-voice solicitation still needs express seller-specific consent. The earlier Ontario consent query returned no contacts. Do not set consent to true. The HubSpot sample is still not a province-coded calling list.

WisdomTwin stays off this hook. No service price is added. No grant is guaranteed.
