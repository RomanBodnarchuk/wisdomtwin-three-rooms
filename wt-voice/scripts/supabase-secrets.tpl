# Runtime secrets for the edge function. Rendered in memory by `op inject` and piped to `supabase secrets set`.
# After this step the values live in Supabase's secret store (policy exception; see RUNBOOK decision D1).
ELEVENLABS_API_KEY={{ op://WisdomTwin/ElevenLabs API/credential }}
ELEVENLABS_WEBHOOK_SECRET={{ op://WisdomTwin/ElevenLabs Post-Call Webhook/secret }}
HUBSPOT_SERVER_TOKEN={{ op://WisdomTwin/HubSpot Voice Server Private App/token }}
TWILIO_ACCOUNT_SID={{ op://WisdomTwin/Twilio/account_sid }}
TWILIO_API_KEY={{ op://WisdomTwin/Twilio/api_key_sid }}
TWILIO_API_SECRET={{ op://WisdomTwin/Twilio/api_key_secret }}
TWILIO_AUTH_TOKEN={{ op://WisdomTwin/Twilio/auth_token }}
WT_TRIGGER_SECRET={{ op://WisdomTwin/WT Voice Trigger/secret }}
WT_AGENT_ID={{ op://WisdomTwin/WT Voice Config/agent_id }}
WT_AGENT_PHONE_NUMBER_ID={{ op://WisdomTwin/WT Voice Config/phone_number_id }}
WT_CALLBACK_SPOKEN={{ op://WisdomTwin/WT Voice Config/callback_spoken }}
WT_PUBLIC_BASE_URL={{ op://WisdomTwin/WT Voice Config/backend_url }}
# Policy (non-secret). Safe defaults: nothing dials.
WT_DIAL_MODE=disabled
WT_PRODUCTION_ENABLED=false
WT_TEST_ALLOWLIST=
WT_TEST_AUTHORIZED_UNTIL=
WT_RELEASED_AGENT_VERSION=blocked
WT_CALLING_ENTITY=WisdomTwin, Inc.
WT_CALL_PURPOSE=product_follow_up
WT_ALLOWED_JURISDICTIONS=
WT_ALLOWED_SEGMENTS=
WT_CAMPAIGN_ID=
WT_CAMPAIGN_APPROVED=false
WT_CONSENT_MAX_AGE_DAYS=365
WT_DNC_MAX_AGE_DAYS=31
