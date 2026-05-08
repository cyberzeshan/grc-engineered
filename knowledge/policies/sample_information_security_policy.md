# Information Security Policy

**Version:** 2.1 | **Effective Date:** 2025-01-01 | **Owner:** Head of GRC

## 1. Purpose
This policy establishes the framework for protecting Acme Corp's information assets against unauthorized access, disclosure, modification, or destruction.

## 2. Scope
This policy applies to all employees, contractors, consultants, and third parties who access Acme Corp information systems.

## 3. Access Control
3.1 Access to systems and data is granted based on business need and the principle of least privilege.
3.2 User access reviews are conducted quarterly for all production systems.
3.3 Multi-factor authentication (MFA) is required for all remote access and privileged accounts.
3.4 Access rights are revoked within 24 hours of employee termination.

## 4. Vulnerability Management
4.1 All systems are scanned for vulnerabilities monthly using approved scanning tools.
4.2 Critical and High severity vulnerabilities must be remediated within 30 and 60 days respectively.
4.3 Vulnerability scan results are reviewed by the Security team and tracked to closure.

## 5. Incident Response
5.1 Security incidents must be reported to security@acmecorp.com within 1 hour of discovery.
5.2 The Incident Response Plan (IRP) defines escalation procedures, containment steps, and communication requirements.
5.3 Post-incident reviews are conducted for all P1 and P2 incidents within 5 business days.

## 6. Data Classification
6.1 Information is classified as: Public, Internal, Confidential, or Restricted.
6.2 Restricted data includes PII, financial records, and authentication credentials.
6.3 Restricted data must be encrypted at rest and in transit using AES-256 and TLS 1.2+.

## 7. Third-Party Risk
7.1 All new vendors with data access undergo a risk assessment before onboarding.
7.2 Vendors are tiered (Critical/High/Medium/Low) based on data access and business impact.
7.3 Critical and High vendors are reviewed annually; Medium vendors bi-annually.

## 8. Compliance
Non-compliance with this policy may result in disciplinary action up to and including termination.

## Change Log
| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2025-01-01 | 2.1 | Added MFA requirement for all remote access | J. Smith |
| 2024-06-01 | 2.0 | Major revision for ISO 27001:2022 alignment | J. Smith |
