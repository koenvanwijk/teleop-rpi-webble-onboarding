# Security model

This project uses a one-time **setup token** (printed as a QR code on the device).
The Web Bluetooth page requires that token to unlock provisioning commands.
Tokens can be rotated/regenerated. Keep them secret and unique per device.

**Threats considered**
- Opportunistic pairing from nearby phones: mitigated by token gating.
- Passive eavesdropping on BLE: credentials are only sent after token validation.
  (Consider rotating Wi‑Fi password after onboarding in sensitive environments.)

**Hardening options**
- Use a short validity window for BLE (default 5 minutes after boot, unless Wi‑Fi is missing).
- Enable SMP/Bonding with Passkey in BlueZ and display the passkey on a connected screen or LED pattern.
- Sign the configuration (JSON + HMAC) with a device secret to protect integrity.
