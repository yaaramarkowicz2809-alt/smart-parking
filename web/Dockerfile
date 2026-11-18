# ---- Web image: Nginx serving the dashboard + reverse proxy to the API ----
FROM nginx:1.27-alpine

# Replace the default site config with ours
COPY nginx.conf /etc/nginx/conf.d/default.conf

# The static dashboard
COPY index.html /usr/share/nginx/html/index.html

EXPOSE 80
# CMD is inherited from the base image: nginx -g 'daemon off;'
