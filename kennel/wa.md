These are the keys we need to insert.  For API servers to work, we need to ensure that the following are set - these are test keys for the test environment only, and are not 'secrets'.  

in ~/.hermes.env

GATEWAY_ALLOW_ALL_USERS=true

OPENROUTER_API_KEY=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

we also need to pass the command:

hermes config set model openrouter/free

on startup for all hermes environments.

