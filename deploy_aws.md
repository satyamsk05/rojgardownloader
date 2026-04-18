# AWS Deployment Guide for ROJGER Downloader 🚀

This guide explains how to deploy the **ROJGER Downloader** on an AWS EC2 instance using Docker.

## 1. Create an AWS EC2 Instance

1. Log in to your [AWS Management Console](https://console.aws.amazon.com/).
2. Navigate to **EC2** and click **Launch Instance**.
3. **Name**: `Rojger-Downloader-Server`
4. **OS**: Choose **Ubuntu 22.04 LTS**.
5. **Instance Type**: `t2.micro` (Free Tier) or `t3.small` (Recommended for better performance).
6. **Key Pair**: Create or select an existing key pair to SSH into your server.
7. **Security Group**: Allow the following ports:
   - `22` (SSH)
   - `80` (HTTP)
   - `443` (HTTPS)

## 2. Connect and Install Docker

Once the instance is running, SSH into it:

```bash
ssh -i your-key.pem ubuntu@your-instance-ip
```

Then, run these commands to install Docker and Docker Compose:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker $USER
# Logout and log back in for group changes to take effect
```

## 3. Deploy the App

1. Clone your repository:
   ```bash
   git clone https://github.com/satyamsk05/rojgardownloader.git
   cd rojgardownloader
   ```

2. Start the application using Docker Compose:
   ```bash
   sudo docker-compose up -d --build
   ```

## 4. Access Your Site

The app will now be running on port 80 of your instance's public IP.
Visit: `http://your-instance-ip`

---

## 🔒 4. Link Custom Domain (rojgar.site) & Add SSL

To make your app accessible at `https://rojgar.site`, follow these steps:

### Step A: DNS Configuration (Where you bought the domain)
1. Go to your domain registrar (GoDaddy, Hostinger, Cloudflare, etc.).
2. Go to **DNS Settings**.
3. Add a new **A Record**:
   - **Name/Host**: `@`
   - **Value/Points To**: `<Your-AWS-Public-IP>`
   - **TTL**: Auto or 1 hour
4. Add another **A Record** for `www` (Optional but recommended):
   - **Name/Host**: `www`
   - **Value/Points To**: `<Your-AWS-Public-IP>`

### Step B: Update Docker Compose
We need Docker to run on an internal port so Nginx can handle the public ports (80 and 443).
Edit `docker-compose.yml` on your server to map `8000:8000` instead of `80:8000`.

### Step C: Install Nginx & Certbot on AWS
Run these commands on your EC2 instance:
```bash
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx
```

### Step D: Configure Nginx
Create a new Nginx config file for your domain:
```bash
sudo nano /etc/nginx/sites-available/rojgar.site
```
Paste this configuration inside:
```nginx
server {
    listen 80;
    server_name rojgar.site www.rojgar.site;

    location / {
        proxy_pass http://127.0.0.0:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
Save and exit (`Ctrl+X`, then `Y`, then `Enter`).

Enable the configuration:
```bash
sudo ln -s /etc/nginx/sites-available/rojgar.site /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step E: Generate Free SSL Certificate (HTTPS)
Run Certbot to secure your site:
```bash
sudo certbot --nginx -d rojgar.site -d www.rojgar.site
```
Follow the prompts, and Certbot will automatically configure HTTPS for you.

Congratulations! Your app is now live at `https://rojgar.site` 🚀

