# Capsize Social repository instructions

Capsize Social is a private FastAPI service for credential-backed Bluesky and
Discord account operations. Keep provider-specific moderation, posting,
credential encryption, database migrations, and deployment behavior local to
this service.

Use the root `justfile` recipes:

- `just setup` resolves the development environment.
- `just lint`, `just format`, and `just typecheck` run the configured Python
  checks.
- `just test` runs the service suite.
- `just build` builds the distribution.
- `just ci` runs the complete validation sequence.

The private workflow runs on the workstation queue with the scoped
`capsize-social-ci` label and uses the managed local Python/uv toolchain. Do
not move it to a hosted runner or add credentials to the workflow.

`capsize-commons`, `capsize-bluesky`, and the shared health routes provide
documented contracts. Do not broaden those packages with provider-specific
behavior that belongs to this service.
