#!/usr/bin/env bash

# shellcheck disable=SC2154

export DEBIAN_FRONTEND="noninteractive"
sudo apt update -y
sudo apt install python3.8* git nginx python-certbot-nginx python3-pip -y
cd /tmp || exit
sudo certbot --noninteractive --nginx --agree-tos --email akhilnarang@thescriptgroup.in --domain hades.thescriptgroup.in
cat << EOF | sudo tee /etc/nginx/sites-available/hades.thescriptgroup.in
server {
    listen 80;
    server_name hades.thescriptgroup.in;
    location ^~ /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://hades.thescriptgroup.in$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name hades.thescriptgroup.in;
    ssl_certificate /etc/letsencrypt/live/hades.thescriptgroup.in/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/hades.thescriptgroup.in/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location /static {
        root /home/akhil/Hades/hades;
        try_files $uri $uri/ =404;
    }

    location ^~ / {
        proxy_pass        http://127.0.0.1:5500;
        proxy_redirect    off;

        proxy_set_header   Host                 \$host;
        proxy_set_header   X-Real-IP            \$remote_addr;
        proxy_set_header   X-Forwarded-For      \$proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto    \$scheme;
    }
}

EOF
sudo ln -s /etc/nginx/sites-available/hades.thescriptgroup.in /etc/nginx/sites-enabled/hades.thescriptgroup.in
sudo rm -fv /etc/nginx/sites-{available,enabled}/default
sudo nginx -s reload
echo '30 2 * * * /usr/bin/certbot renew --noninteractive --renew-hook "/usr/sbin/nginx -s reload" >> /var/log/le-renew.log' > /tmp/cron
sudo crontab /tmp/cron
rm -v /tmp/cron
cd - || exit
git clone https://github.com/The-SCRIPT-Group/hades.git
cd hades || exit
pip3 install -r requirements.txt
echo "Setup your configuration file and run the application! (make sure its running on port 5000, should be the default with waitress)"
