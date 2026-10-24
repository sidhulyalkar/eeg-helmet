# Security and medical data boundary

The research server listens on **127.0.0.1**, serves only fixed assets, and exposes synthetic-data GET endpoints and one parameter-only POST endpoint. It is deliberately NOT an internet-facing production backend. Do not expose it via a tunnel, deploy it with identifiable data, bypass input validation or use it as a medical device.

The `access_allowed` library function is a testable policy decision, not real authentication, authorization middleware, cryptographic storage, audit logging or consent persistence. Consent revocation is demonstrated at the decision layer only. Production research requires identity provider integration, explicit scopes, consent withdrawal, revocation propagation, encrypted storage, trusted timestamps, audit review, data retention/deletion, governance and security assessment.

To report a vulnerability, do not post patient data or secrets in public issues. Contact the project maintainer privately after a repository owner and coordinated disclosure channel have been established.
