# Deploying ClaimLens on Vultr (HackGlobal 2026)

Goal: a public demo URL served from a Vultr Compute instance.

## 1. Create the instance

1. Log in at vultr.com with the account that received the HackGlobal credits.
2. Products > Deploy New Instance > Cloud Compute (shared CPU is fine).
3. Location: Singapore (closest to Indonesia).
4. Image: Ubuntu 24.04 LTS. Plan: the smallest plan is enough for this demo.
5. Set a hostname such as `claimlens`, add your SSH key if you have one
   (or use the root password Vultr emails you), then Deploy.

## 2. Install and upload

SSH into the instance, then:

```bash
apt update && apt install -y python3-pip python3-venv git
git clone https://github.com/nugrohoriziq127-prog/claimlens.git
cd claimlens
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## 3. Run it as a service

```bash
cat > /etc/systemd/system/claimlens.service <<'EOF'
[Unit]
Description=ClaimLens
After=network.target

[Service]
User=root
WorkingDirectory=/root/claimlens
ExecStart=/root/claimlens/.venv/bin/gunicorn -w 2 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now claimlens
systemctl status claimlens
```

## 4. Open the firewall and verify

- In the Vultr dashboard, make sure the instance firewall (if attached)
  allows inbound TCP 5000, or attach no firewall group for the demo.
- Open `http://<instance-ip>:5000` in a browser.
- Test the three example chips: microchip (DEBUNKED), BRICS (MATCHES
  VERIFIED FACT), coffee (UNCERTAIN).

That public URL is what goes into the Vultr Community submission form
("Demo URL" / repository link fields), together with the GitHub repo.
