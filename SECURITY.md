# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅        |

## Reporting a Vulnerability

If you discover a security vulnerability in HermesMesh, please report it privately:

1. **Email**: security@hermesmesh.dev
2. **Do NOT** open a public GitHub issue
3. Include detailed reproduction steps
4. Allow 48 hours for initial response

## Security Measures

- Enrollment tokens are single-use and expire after 24 hours
- All API communications should use TLS in production
- Role-based access control (ADMIN, OPERATOR, VIEWER)
- Complete audit logging of administrative actions
- No secrets stored in plain text
- Database credentials hashed

## Dependencies

We regularly audit dependencies for known vulnerabilities:

```bash
pip install safety
safety check
```

## Security Best Practices

When deploying HermesMesh:

1. Always use TLS in production
2. Use strong API keys
3. Restrict controller access with firewall rules
4. Enable audit logging
5. Rotate enrollment tokens frequently
6. Keep the software updated
