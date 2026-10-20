FROM scratch
COPY server.elf /server.elf
ENTRYPOINT ["/server.elf"]
