# Authentication and Authorization

**Category**: security
**Source**: OAuth.net, IETF RFC 7519, Auth0
**Use Case**: Architect Agent uses this when designing auth in technical spec.

---

## 1. Overview: AuthN vs AuthZ

**Authentication (AuthN)** answers the question "who are you?"—the process of verifying that a request comes from a specific identity. **Authorization (AuthZ)** answers the question "what can you do?"—the process of deciding whether the authenticated identity is allowed to perform the requested action. The two are conceptually distinct: a system can authenticate a user perfectly and still authorize them incorrectly, and vice versa. Conflating the two is one of the most common sources of security defects.

A typical request flow makes the distinction concrete. The user presents credentials (a password, a token, a passkey assertion), and the system verifies them—**authentication**. The system then determines whether the now-authenticated user is permitted to perform the specific action requested—**authorization**. The first decision is "is this person who they claim to be?" The second is "given that we know who they are, are they allowed to do this?"

Both decisions are security-critical, and both are routinely implemented poorly. Authentication failures expose the system to impersonation; authorization failures expose data and operations across user boundaries. The 2021 OWASP Top 10 lists **Broken Access Control** as the #1 web application risk and **Identification and Authentication Failures** as #7—two related but distinct concerns, both common, both consequential.

This document covers the major authentication methods, the trade-off between JWTs and server-stored sessions, the dominant authorization models (RBAC, ABAC, ReBAC, PBAC), the security best practices that prevent the most common breaches, and a concrete authentication and authorization design for an educational coding app whose users include children, with the corresponding compliance constraints.

---

## 2. AuthN Methods

| Method | How it works | Pros | Cons |
|---|---|---|---|
| **Password + email** | User registers with email and password; server stores a hash; subsequent logins compare hashed candidate against stored hash. | Universally familiar; works without third-party dependencies; full control. | Users reuse passwords across sites; vulnerable to credential stuffing; requires careful hashing, rate limiting, and password-reset flows. |
| **OAuth 2.0** | Delegated authorization protocol. The user authenticates with a trusted provider (Google, GitHub, Microsoft) and the provider issues tokens that the application verifies. | Eliminates password storage; users avoid creating yet another credential; familiar UX. | Adds dependency on identity providers; requires careful redirect-URI validation; less control over the auth experience. |
| **OIDC (OpenID Connect)** | Identity layer on top of OAuth 2.0. Adds an `id_token` (a JWT) that carries verified user identity claims, enabling "sign in with X" flows in addition to authorization. | Standardized "sign in with" flow; built on OAuth 2.0 infrastructure; mature ecosystem. | Same dependency concerns as OAuth; implementation requires care around token validation and claim verification. |
| **SAML** | Enterprise single-sign-on protocol; XML-based assertions exchanged between identity providers and service providers. | Long-established in enterprise; supports federation across organizations. | XML-based and verbose; complex to implement; declining outside enterprise SSO contexts in favor of OIDC. |
| **Passkeys / WebAuthn** | Public-key credentials stored on the user's device (or hardware key), used to sign a challenge from the server. No password ever leaves the device. | Phishing-resistant; eliminates password reuse; hardware-backed; the rising standard for consumer authentication. | Requires modern browser/OS support; recovery and cross-device sync are more complex than passwords. |
| **Magic link** | Server sends a one-time link via email; clicking it logs the user in. | No password to remember; simple UX. | Email security becomes the auth factor; latency on each login; vulnerable if email is compromised. |
| **MFA / 2FA** | Second factor on top of any of the above: TOTP (Google Authenticator, Authy), SMS (deprecated for security), push notifications, hardware keys. | Substantial increase in security against credential theft. | Friction; recovery flows are complex; SMS specifically is vulnerable to SIM swapping and should be avoided where alternatives exist. |

The practical guidance for new applications:

- **For consumer applications**, use **email + password with optional OAuth/OIDC** ("Sign in with Google") and add **passkey support** as it matures. Add **TOTP-based MFA** for sensitive accounts.
- **For enterprise applications**, support **OIDC** and likely **SAML** for SSO with customer identity providers.
- **Avoid SMS-based MFA** as a primary second factor; use it as a fallback at most.
- **Avoid building custom auth from scratch.** Use established providers (Auth0, Clerk, Firebase Auth, Supabase Auth, AWS Cognito) or well-maintained framework libraries. Custom auth is among the categories of code most likely to ship with serious vulnerabilities.

---

## 3. JWT vs Sessions

Once a user is authenticated, the application needs to remember that fact across subsequent requests. Two approaches dominate.

**Server-stored sessions.** The server creates a session record (typically in a database or shared cache like Redis), generates a session ID, and sends the ID to the client as an HTTP cookie. On every request, the cookie carries the ID, and the server looks up the session record to retrieve the authenticated user's identity and any associated state.

- *Pros*: Easy to revoke (delete the session record). Server holds the source of truth. Cookie can be small. Session state is server-controlled.
- *Cons*: Requires a shared session store across multiple servers (Redis is the typical choice). Adds a database/cache lookup on every authenticated request. Less convenient for cross-domain or service-to-service communication.

**JSON Web Tokens (JWT).** Defined in **RFC 7519**, a JWT is a self-contained, signed token that includes the user's identity and any claims directly in the token. The token has three Base64-encoded parts separated by dots: a **Header** (algorithm), a **Payload** (claims), and a **Signature** (a cryptographic signature over the header and payload).

```
eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyXzEyMyIsImV4cCI6MTcwMDAwMDAwMH0.signature
```

The server signs the token at issue time; on subsequent requests, the server verifies the signature without consulting any database. The token is **stateless**—everything needed to authenticate the request is in the token itself.

- *Pros*: No server-side session store needed. Scales horizontally without shared state. Works naturally across services and across domains. Convenient for APIs.
- *Cons*: **Hard to revoke** before expiry without adding a denylist mechanism (which reintroduces server state). Larger than session IDs (often hundreds of bytes vs. tens). If a JWT leaks, the attacker has access until it expires. Must be carefully validated (algorithm verification, expiration check, audience and issuer checks).

**The standard pattern in modern applications:**

- Issue a **short-lived access token** (JWT, 15 minutes to 1 hour) for actual API requests.
- Issue a **long-lived refresh token** (days to weeks) used only to obtain new access tokens.
- Store both tokens in **HttpOnly, Secure, SameSite cookies**, not in `localStorage` (which is vulnerable to XSS).
- **Rotate refresh tokens** on each use (issue a new refresh token, invalidate the old one) so that a leaked refresh token has a bounded useful lifetime.
- Maintain a **token-revocation mechanism** (blocklist by token ID) for explicit logout and security incidents.

The split between access and refresh tokens captures most of the benefits of both approaches: stateless access tokens for the high-frequency request path, server-controlled refresh tokens for revocation and lifecycle management.

For applications with strict revocation requirements (banking, healthcare, child-safety contexts), **server-stored sessions** remain the safer default; the convenience of JWTs is harder to justify when an emergency lockout might need to take effect within seconds.

---

## 4. AuthZ Models: RBAC, ABAC, ReBAC, PBAC

Authorization—deciding what an authenticated user can do—is modeled in several increasingly expressive ways.

**RBAC (Role-Based Access Control).** Users are assigned roles, and roles are granted permissions. A user with the `admin` role has all permissions associated with that role; a user with the `editor` role has a different set. RBAC is simple, well-understood, and adequate for most applications. The data model is two tables: `users → roles` and `roles → permissions`.

*Strengths*: simplicity, ease of implementation, ease of audit ("who has this role?").
*Weaknesses*: insufficiently granular for some use cases. "Editor in workspace A but viewer in workspace B" requires either many roles or extension to a richer model.

**ABAC (Attribute-Based Access Control).** Authorization decisions are computed from attributes of the user, the resource, the action, and the context. A policy might read: "User can edit a document if `user.department == document.department AND time.hour BETWEEN 9 AND 17`." ABAC is more flexible than RBAC and supports decisions that depend on relationships between user and resource.

*Strengths*: flexibility, supports context-dependent decisions, handles fine-grained sharing.
*Weaknesses*: complexity, harder to audit ("can Alice edit this document?" may require evaluating a policy rather than checking a role list).

**ReBAC (Relationship-Based Access Control).** Authorization decisions are based on relationships between entities. The canonical example is **Google Zanzibar**, the system that powers Google Drive's sharing model: "Alice can read this document because she is a member of a group that has been granted access to a folder containing the document." Modern open-source and commercial implementations include **OpenFGA** (from Auth0), **SpiceDB**, and **Permify**.

*Strengths*: handles complex sharing graphs (folders, teams, nested groups) elegantly. Scales to billions of permission edges.
*Weaknesses*: operational complexity; the model requires careful design and dedicated infrastructure.

**PBAC (Policy-Based Access Control).** Authorization decisions are expressed as explicit policies, evaluated by a policy engine. The dominant tool is **Open Policy Agent (OPA)** with its Rego policy language. Policies live separately from application code and can be reviewed, versioned, and tested independently.

*Strengths*: separation of policy from application code. Clear audit trail. Useful for centralizing decisions across many services.
*Weaknesses*: introduces a new language and tooling. Overkill for small applications.

The practical guidance: **start with RBAC**. Most applications never need more. Move to ABAC when context-dependent decisions become common. Move to ReBAC when sharing graphs become complex (file sharing, team-based products, multi-tenant collaboration). Adopt PBAC when authorization needs to be centralized across many services.

---

## 5. Best Practices

- **Hash passwords with a modern slow hash.** Use **bcrypt**, **scrypt**, or **Argon2id**, never MD5, SHA-1, or SHA-256. The slowness of these algorithms is a feature: it makes brute-force attacks computationally expensive even after a database breach.
- **Salt every password uniquely.** Modern password-hashing libraries handle salting automatically; the salt is stored alongside the hash. Salts prevent rainbow-table attacks and ensure that two users with the same password have different stored hashes.
- **Rate-limit login attempts.** Cap attempts per IP, per email, and per account. Lock accounts temporarily after repeated failures. Notify users on suspicious activity.
- **Require MFA for sensitive actions.** Even if not required for routine login, MFA should gate operations like password changes, payment-method updates, and admin actions.
- **HTTPS everywhere.** TLS 1.2 minimum, TLS 1.3 preferred. Cookies must use the `Secure` flag (HTTPS only), `HttpOnly` flag (not accessible to JavaScript), and an appropriate `SameSite` attribute (`Strict` or `Lax`).
- **Rotate refresh tokens.** Each refresh produces a new refresh token and invalidates the old one. Detection of a reused old token signals possible token theft and should trigger session invalidation.
- **Validate JWTs carefully.** Verify the signature with the correct public key. Verify the algorithm matches the expected one (the `alg: none` attack is an old but real concern). Verify expiration, issuer, and audience claims. Reject tokens that fail any check.
- **Store secrets outside source control.** API keys, signing keys, OAuth client secrets—all in environment variables or secret-management services, never in repository files.
- **Distinguish authentication from authorization in code.** A function that has authenticated a user has not authorized them to do anything specific; the authorization check is a separate explicit step. Conflating the two is a common source of access-control bugs.
- **Apply principle of least privilege.** Tokens should grant only the permissions needed for their intended use. Service accounts should have only the access required for the service. Roles should reflect actual job functions, not aspirational ones.
- **Audit authorization decisions.** Log who attempted to access what and whether the access was granted or denied. The logs are essential for detecting probing and for forensic investigation.

---

## 6. Example: Auth Design for Educational Coding App for Kids

Consider the auth design for **CodeCub**, an educational Python coding app for children aged 6–12, with parent buyers, child users, and a planned teacher and admin layer for the school channel. The application is subject to **COPPA** (Children's Online Privacy Protection Act) in the US and equivalent regulations elsewhere, which impose specific constraints on authentication and data handling for under-13 users.

**Authentication design:**

- **Parents authenticate with email + password** as the primary method. The system stores password hashes using **Argon2id** with a per-user salt. **OAuth via Google** is offered as an alternative for convenience ("Sign in with Google"); Google's identity is treated as authoritative for the parent's email but is not a substitute for the parent's account record in the application's own database.
- **Children do not have independent password-based accounts** in the initial product. A parent logs in, then selects a child profile from within their account. This avoids requiring children to create credentials and avoids the COPPA complications of collecting passwords from minors. The child profile is identified by a non-sensitive display name chosen by the parent; it is not an email address.
- **MFA is offered for parent accounts**, particularly for accounts in the school channel where teacher logins coexist with parent logins. TOTP is the primary second factor; SMS is not offered.
- **Teachers authenticate** through a separate flow, often via the school's own identity provider (OIDC integration with Google Workspace for Education or similar). Direct teacher-account creation is also supported with email + password and required MFA.
- **Admin accounts** (CodeCub internal staff) require MFA without exception and use a separate admin authentication path with stricter session policies (shorter timeouts, IP allow-lists for sensitive operations).

**Session management:**

- **Server-stored sessions in Redis** for the parent and teacher web applications. Session IDs sit in `HttpOnly`, `Secure`, `SameSite=Lax` cookies. Sessions expire after 30 days of inactivity, with sliding renewal on each request.
- For the API layer that mobile clients will use (planned post-launch), short-lived **JWT access tokens (15 minutes)** paired with **refresh tokens (30 days, rotated on use)** are added. Refresh tokens are invalidated on logout, password change, and detected reuse.
- All sessions can be revoked centrally; an administrative endpoint allows immediate logout of all sessions for a given parent (essential for COPPA-related parental data-deletion requests).

**Authorization design (RBAC):**

The roles at launch:

- **`child`**: can access their own learner profile, attempt lessons, view their own progress.
- **`parent`**: can access their own profile, billing, and child profiles linked to their account.
- **`teacher`**: can access their assigned classes and the learner profiles enrolled in those classes.
- **`admin`** (internal staff): can access the admin tooling, with sub-roles (`admin_support`, `admin_curriculum`, `admin_finance`) restricting which operations within the admin surface they can perform.

Authorization is enforced at the API boundary on every endpoint. Every endpoint that returns child-specific data verifies the requester's relationship to the child (parent owns the child profile, or teacher has the child enrolled in an assigned class). The IDOR risk is acute and is mitigated by explicit ownership checks rather than reliance on URL obscurity.

A future iteration may move to **ReBAC** if the school-channel sharing graph (districts, schools, classes, students, teachers, parents) outgrows what RBAC handles cleanly. For launch, RBAC is sufficient and substantially simpler.

**COPPA-specific considerations:**

- **Verifiable parental consent** is required before any data is collected on a child beyond what is strictly necessary for in-app function. The application implements a parental-consent flow (credit-card verification or signed consent form) before enabling any optional features that collect additional data.
- **No behavioral advertising to under-13 users.** No third-party tracking, no behavioral ad networks, no analytics that profile children individually beyond what is needed for educational adaptation.
- **Data-minimization**: child profiles store the minimum information needed (display name, age band, progress data). No real names, addresses, or contact information for children.
- **Parental data-access and deletion**: the parent can review all data the system holds about their child and request deletion. The deletion workflow is automated and produces an audit record.
- **No child-to-child messaging or social features without parental approval.** Sharing of child-built projects is gated by parental opt-in and goes through moderation.

**Security operations:**

- **Login-attempt rate limiting** at multiple layers (per IP, per email, per session).
- **Account-lockout** after repeated failed attempts, with email notification to the affected parent.
- **Password requirements** aligned with NIST guidance: minimum length, no forced periodic rotation, dictionary checks against breached-password lists.
- **Session revocation logs** retained for forensic investigation, in compliance with applicable retention regulations.
- **Annual penetration testing** focused on authentication and authorization flows once the product reaches meaningful scale.

The design is deliberately conservative. The combination of children as users, parents as buyers, schools as a future channel, and COPPA compliance as a baseline requires that auth be unambiguous, auditable, and easy to reason about. Simpler patterns (RBAC over ReBAC, server sessions over JWTs for the web app, established providers over custom auth code) are chosen where they are sufficient, with explicit upgrade paths if requirements grow.

---

## 7. Common Pitfalls

- **Storing JWTs in `localStorage`.** Vulnerable to XSS: any script running on the page (including third-party scripts) can read the token. Use `HttpOnly` cookies instead.
- **Long-lived JWTs without refresh tokens.** A 30-day JWT that is not revocable is a 30-day backdoor if it leaks. Use short-lived access tokens with rotated refresh tokens, or use server sessions.
- **Insufficient password policies.** Allowing 6-character passwords or skipping breached-password checks leaves users vulnerable to credential stuffing. NIST guidance is the modern standard.
- **Confusing AuthN with AuthZ in code.** A function that has authenticated a user has not authorized them to do anything; treating "logged in" as sufficient for any action produces access-control bugs.
- **Predictable identifiers.** Sequential integer IDs in URLs (`/users/1`, `/users/2`) make IDOR exploitation trivial. Use UUIDs or other non-enumerable identifiers.
- **Verbose error messages.** "Username not found" vs "wrong password" tells attackers which usernames exist in the system. Use a single generic message: "Email or password is incorrect."
- **Custom crypto.** Implementing password hashing, token signing, or MFA from scratch produces vulnerable implementations far more often than not. Use established libraries.
- **Forgetting to invalidate sessions on logout, password change, or security events.** A logout that does not actually revoke the session is theatre.
- **Logging tokens or secrets.** Auth flows touch sensitive material; debug logs that include tokens, passwords, or full headers leak credentials. Audit logs for redaction.
- **No MFA recovery plan.** Users who lose their second factor must have a recovery flow that does not undermine the security MFA was supposed to provide. SMS fallbacks reintroduce SIM-swap risk; recovery codes handed out at MFA enrollment are a better pattern.
- **Treating COPPA (or equivalents) as a checkbox.** Children's-data regulation is genuinely stricter than adult consumer regulation, and shortcuts produce both legal and reputational exposure. Build compliance in from the start; retrofitting it is expensive.

---

## 8. References

- OAuth 2.0: https://oauth.net/2/
- IETF RFC 7519 — JSON Web Token (JWT): https://datatracker.ietf.org/doc/html/rfc7519
- Auth0 — Authentication: https://auth0.com/learn/authentication