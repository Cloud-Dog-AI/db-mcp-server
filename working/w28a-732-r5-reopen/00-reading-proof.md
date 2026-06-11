# W28A-732-R5 (reopen) — Reading proof

- Instruction re-read: `cloud-dog-ai-platform-standards/working/instructions/W28A-732-R5-DBMCP-LOGIN-CONTRACT-REOPEN-2026-06-11.md` (REOPENED / SAME-LANE CORRECTION).
- Required correction understood: deliver the platform flat-login WebUI contract — anonymous username/password form; admin/read-write/read-only username/password logins all work live; `/runtime-config.js` must NOT advertise `AUTH_MODE:"api_key"`; read-only write -> 403; anon protected/write -> 401; live deployed digest matches the pushed image from current origin/main; committed source + ui/dist on origin/main; browser evidence proves the live route.
- Return gate: HAVE_ALL_REQUIREMENTS_BEEN_MET: YES only after live dbmcpserver0 username/password login proven for all three roles and the API-key WebUI mode is gone.
- RULES re-read: NO Vault writes from a lane; sanctioned remote Docker daemon is tcp://server0.viewdeck.com:2375 only.

origin/main at close = 8455944fe7a6eb42b5700634478fdf3eaee138d9
RULES_REREAD: YES
INSTRUCTION_REREAD: YES
