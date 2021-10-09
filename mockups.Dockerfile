FROM lipanski/docker-static-website:latest


# Copy your static files
COPY . .

VOLUME /home/static

# Need a Cache-Control:max-age=0 header (thttpd option '-M 0') on all responses.
CMD ["/thttpd", "-D", "-h", "0.0.0.0", "-p", "3000", "-d", "/home/static", "-u", "static", "-l", "-", "-M", "0"]
