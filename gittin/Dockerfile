FROM alpine:3.20

RUN apk add --no-cache git openssh bash \
    && adduser -D -h /home/git -s /bin/sh git \
    && mkdir -p /home/git/.ssh /repos /var/run/sshd /ssh \
    && chown -R git:git /home/git /repos /ssh

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY gittin-shell.sh /usr/local/bin/gittin-shell.sh
RUN chmod 0755 /usr/local/bin/entrypoint.sh /usr/local/bin/gittin-shell.sh

EXPOSE 22
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
