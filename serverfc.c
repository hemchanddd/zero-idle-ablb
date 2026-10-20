#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <netinet/in.h>
#include <arpa/inet.h>

static const char body[] = "{\"status\":\"ok\",\"message\":\"hello from firecracker baseline\"}";

static void bring_up(int fd, const char *name, const char *addr) {
    struct ifreq ifr;
    memset(&ifr, 0, sizeof(ifr));
    strncpy(ifr.ifr_name, name, IFNAMSIZ - 1);
    if (addr != NULL) {
        struct sockaddr_in *sin = (struct sockaddr_in *)&ifr.ifr_addr;
        sin->sin_family = AF_INET;
        inet_pton(AF_INET, addr, &sin->sin_addr);
        ioctl(fd, SIOCSIFADDR, &ifr);
        sin = (struct sockaddr_in *)&ifr.ifr_netmask;
        sin->sin_family = AF_INET;
        inet_pton(AF_INET, "255.255.255.0", &sin->sin_addr);
        ioctl(fd, SIOCSIFNETMASK, &ifr);
    }
    ioctl(fd, SIOCGIFFLAGS, &ifr);
    ifr.ifr_flags |= IFF_UP | IFF_RUNNING;
    ioctl(fd, SIOCSIFFLAGS, &ifr);
}

int main(int argc, char **argv, char **envp) {
    const char *ip = "10.0.0.2";
    for (int i = 0; envp[i] != NULL; i++) {
        if (strncmp(envp[i], "guestip=", 8) == 0)
            ip = envp[i] + 8;
    }
    int fd = socket(AF_INET, SOCK_DGRAM, 0);
    bring_up(fd, "lo", "127.0.0.1");
    bring_up(fd, "eth0", ip);
    close(fd);
    int s = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in a;
    memset(&a, 0, sizeof(a));
    a.sin_family = AF_INET;
    a.sin_port = htons(8080);
    a.sin_addr.s_addr = htonl(INADDR_ANY);
    bind(s, (struct sockaddr *)&a, sizeof(a));
    listen(s, 8);
    write(1, "READY\n", 6);
    for (;;) {
        int c = accept(s, NULL, NULL);
        if (c < 0)
            continue;
        char req[1024];
        ssize_t n = read(c, req, sizeof(req) - 1);
        if (n > 0) {
            char header[256];
            int hlen = snprintf(header, sizeof(header),
                "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: %zu\r\nConnection: close\r\n\r\n",
                sizeof(body) - 1);
            write(c, header, hlen);
            write(c, body, sizeof(body) - 1);
        }
        close(c);
    }
    return 0;
}
