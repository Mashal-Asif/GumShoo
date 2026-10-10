# Security Limitations - URL Fetching

## SSRF Protection Status

The `core/readers.py` module implements multiple layers of SSRF protection:

### ✓ Protections in Place

1. **URL Scheme Validation** - Only HTTP/HTTPS allowed (case-insensitive)
2. **DNS Resolution Validation** - Resolves hostnames and validates IPs before fetch
3. **IP Range Blocking** - Blocks private, loopback, link-local, multicast, unspecified, and reserved addresses
4. **IPv4-Mapped IPv6 Detection** - Handles `::ffff:x.x.x.x` addresses
5. **Redirect Validation** - Validates final redirect destination
6. **Resource Limits** - Timeout (10s) and content size (5MB) enforcement

### ⚠ Known Limitation: DNS Rebinding TOCTOU

**Status:** NOT FULLY MITIGATED

**Issue:** Time-Of-Check-Time-Of-Use (TOCTOU) race condition exists between DNS validation and HTTP connection.

**Attack Scenario:**
1. Attacker controls DNS for `evil.example.com`
2. Initial DNS resolution (validation) returns public IP → validation passes
3. DNS record changes to private IP (e.g., 192.168.1.1)
4. `requests.get()` resolves DNS again → connects to private IP

**Current Implementation:**
```python
# Step 1: Validate hostname (resolves DNS)
InputReader._validate_url_host(url)  # DNS resolution #1

# Step 2: Fetch URL (resolves DNS again)
response = requests.get(url, ...)     # DNS resolution #2
```

**Why Not Fixed:**
- Python `requests` library doesn't expose low-level socket control
- True fix requires connecting to validated IP directly, not hostname
- Would need custom HTTP client with socket-level control

**Attack Requirements:**
- Attacker must control authoritative DNS server
- Precise timing to hit validation window (typically < 1 second)
- Coordination between DNS server and target timing

**Practical Risk Assessment:**
- **Low** for typical usage (social media content analysis)
- **Medium** if exposed to adversarial/untrusted URLs
- **High** if used in security-critical context with nation-state adversaries

**Mitigations in Place:**
- Validation happens immediately before request (small window)
- DNS TTL caching reduces re-resolution frequency
- Multiple validation layers provide defense-in-depth
- All user-supplied URLs should be treated as untrusted

**Production Recommendations:**
1. **Network-Level Controls:** Implement egress filtering at firewall/proxy level
2. **Rate Limiting:** Limit external URL fetch frequency per user/session
3. **Monitoring:** Log and alert on blocked SSRF attempts
4. **User Trust:** Only accept URLs from authenticated, trusted users
5. **Alternative:** Use dedicated SSRF-resistant HTTP library if higher assurance needed

## Other Security Considerations

### Timeout Granularity
- **Status:** Acceptable
- **Details:** Timeout applies to connection; slow response reading mitigated by size limits

### Compression Bombs
- **Status:** Acceptable
- **Details:** Size checking on decompressed stream; memory limits provide defense

### Content Disclosure
- **Status:** Protected
- **Details:** All content processed in-memory; not written to disk; not included in logs

## Conclusion

The URL fetching implementation provides **good** SSRF protection for the intended use case (social media content analysis). One known limitation (DNS rebinding) requires sophisticated attacker capabilities and is documented for production deployment planning.

**Recommendation:** Suitable for current application with awareness of limitations.
