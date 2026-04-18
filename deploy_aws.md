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

## 🔒 Optional: Add SSL (HTTPS)

For a professional site, you should add a domain and SSL. You can use **Nginx** and **Certbot** on the same instance to proxy traffic to the Docker container.

### Simple Nginx Config:
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```
