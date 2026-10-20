#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>

static const char body[] = "{\"status\":\"ok\",\"message\":\"hello from zero-idle unikernel\"}";

int main(void) {
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
