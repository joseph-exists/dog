FROM gogs/gogs:next-latest

COPY --chmod=0755 entrypoint.sh /usr/local/bin/entrypoint.sh

EXPOSE 3000 2222
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
