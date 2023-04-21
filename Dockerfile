FROM richarvey/nginx-php-fpm:latest
COPY Application /var/www/html/
COPY scgi_params /etc/nginx/scgi_params
COPY nginx.conf /etc/nginx/nginx.conf
# COPY php-fpm /usr/local/etc/php-fpm.conf