#!/bin/sh
# Substitute $PORT into the nginx config and start nginx
envsubst '$PORT' < /etc/nginx/nginx-template.conf > /etc/nginx/conf.d/default.conf
echo "Nginx listening on port: $PORT"
exec nginx -g 'daemon off;'
