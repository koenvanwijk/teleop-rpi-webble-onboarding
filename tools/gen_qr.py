#!/usr/bin/env python3
import argparse, os, qrcode

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", required=True)
    ap.add_argument("--url", required=True, help="HTTPS URL of the Web UI")
    ap.add_argument("--outdir", default="qrcodes")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    payload = {"token": args.token, "url": args.url}
    # Encode as simple URL with query params for convenience
    qr_text = f"{args.url}?token={args.token}"
    img = qrcode.make(qr_text)
    out = os.path.join(args.outdir, f"teleop-{args.token}.png")
    img.save(out)
    print("Saved", out)

if __name__ == "__main__":
    main()
