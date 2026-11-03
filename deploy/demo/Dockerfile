FROM nginx:alpine
COPY deploy/demo/nginx.conf /etc/nginx/conf.d/default.conf
COPY web/out/ /usr/share/nginx/html/
EXPOSE 80
