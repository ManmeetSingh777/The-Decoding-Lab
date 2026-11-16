# 19 — Runware account: model identification and safe adapter

The user reports having prepaid credit on a Runware API key and calls the intended model 'FLUX Klein 7B'. **Do not assume that exact name is a documented Runware model.** In the currently inspected official docs, FLUX.2 [klein] 4B is `runware:400@4` and FLUX.2 [klein] 9B is `runware:400@2`; an exact 'Klein 7B' variant was not confirmed. There may be newer or different models available to the account. Verify at runware.ai/docs/models and model-specific API reference, or obtain the user's actual Runware model selection before submitting any paid tasks. Runware credit typically applies to the API account, not one silently selected model, but confirm restrictions from the provider/account.

## Provider adapter handshake

1. Load API key from environment `RUNWARE_API_KEY` (never prompt transcript, source files, audit zip or logs).
2. Configure provider `runware` and explicit **user-confirmed** `model_air_id`; do not auto-select `auto` for paid tests unless user explicitly approves.
3. From model docs/account obtain supported `taskType`, positive prompt maximum, reference-image count, output formats, width/height limits and increments, supported edit/image-to-image route, estimated cost and request UUID rules. Store current dated capability snapshot.
4. Implement offline `dry_run` showing exact compiled payload without network access. Reject unsupported capabilities before sending.
5. Before any actual request require `ProviderAuthorization` with approved model, spend ceiling, exact approved task categories, and for source reference images separate third-party upload consent. Code must enforce cap with measured/estimated cost and stop on uncertainty.
6. For first consented operation, make the **smallest useful real provider probe**: text-to-image original artwork, then controlled reference-guided edit if supported and separately authorized. Save actual returned images, model/seed/cost and response. Check provider features rather than trusting a successful HTTP status.
7. Do not claim that 4B/9B necessarily meets professional illustration quality or delivers native layers; user-visible first art will decide.

## Example technical envelope, not a hardcoded promise

Official Klein 4B reference: https://runware.ai/docs/models/bfl-flux-2-klein-4b . Supported output formats include PNG and WEBP as documented; model-specific dimensions (multiples of 16) and up to four reference images are described there. **Format only** cannot create actual separate body parts/masks. Asset design/extraction routes are specified in `16` and `17`.
