#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#define PORT 8080
#define BUFFER_SIZE 1024
#define MAX_PATH_LEN 256

// Structure to pass client socket to thread
typedef struct {
    int client_sock;
    struct sockaddr_in client_addr;
} client_info_t;

// Parse HTTP request and extract the path
void parse_request(const char *request, char *path) {
    char method[16];
    char version[16];

    // Parse the request line: METHOD PATH VERSION
    sscanf(request, "%s %s %s", method, path, version);
}

// Send HTTP response
void send_response(int client_sock, const char *path) {
    char response[BUFFER_SIZE];

    // Simple response based on path
    if (strcmp(path, "/") == 0) {
        snprintf(response, sizeof(response),
                 "HTTP/1.1 200 OK\r\n"
                 "Content-Type: text/html\r\n"
                 "Content-Length: 51\r\n"
                 "\r\n"
                 "<html><body><h1>Hello World!</h1></body></html>");
    } else {
        snprintf(response, sizeof(response),
                 "HTTP/1.1 200 OK\r\n"
                 "Content-Type: text/plain\r\n"
                 "Content-Length: 13\r\n"
                 "\r\n"
                 "Path: %s", path);
    }

    send(client_sock, response, strlen(response), 0);
}

// Thread function to handle client connection
void *handle_client(void *arg) {
    client_info_t *client = (client_info_t *)arg;
    char buffer[BUFFER_SIZE];
    char path[MAX_PATH_LEN];  // Fixed size buffer - vulnerable to overflow

    memset(buffer, 0, BUFFER_SIZE);
    memset(path, 0, MAX_PATH_LEN);

    // Receive request
    ssize_t bytes_received = recv(client->client_sock, buffer, BUFFER_SIZE - 1, 0);

    if (bytes_received > 0) {
        buffer[bytes_received] = '\0';

        printf("[INFO] Received request from %s:%d\n",
               inet_ntoa(client->client_addr.sin_addr),
               ntohs(client->client_addr.sin_port));

        // Parse the request - THIS IS WHERE THE BUG IS
        parse_request(buffer, path);

        // Send response
        send_response(client->client_sock, path);
    }

    close(client->client_sock);
    free(client);

    return NULL;
}

int main() {
    int server_sock, client_sock;
    struct sockaddr_in server_addr, client_addr;
    socklen_t client_len = sizeof(client_addr);
    pthread_t thread_id;

    // Create socket
    server_sock = socket(AF_INET, SOCK_STREAM, 0);
    if (server_sock < 0) {
        perror("Socket creation failed");
        exit(EXIT_FAILURE);
    }

    // Set socket options to reuse address
    int opt = 1;
    if (setsockopt(server_sock, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
        perror("Setsockopt failed");
        exit(EXIT_FAILURE);
    }

    // Configure server address
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT);

    // Bind socket
    if (bind(server_sock, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("Bind failed");
        exit(EXIT_FAILURE);
    }

    // Listen for connections
    if (listen(server_sock, 10) < 0) {
        perror("Listen failed");
        exit(EXIT_FAILURE);
    }

    printf("[INFO] Server listening on port %d\n", PORT);

    // Accept and handle connections
    while (1) {
        client_sock = accept(server_sock, (struct sockaddr *)&client_addr, &client_len);

        if (client_sock < 0) {
            perror("Accept failed");
            continue;
        }

        // Allocate memory for client info
        client_info_t *client_info = malloc(sizeof(client_info_t));
        if (!client_info) {
            perror("Memory allocation failed");
            close(client_sock);
            continue;
        }

        client_info->client_sock = client_sock;
        client_info->client_addr = client_addr;

        // Create thread to handle client
        if (pthread_create(&thread_id, NULL, handle_client, client_info) != 0) {
            perror("Thread creation failed");
            free(client_info);
            close(client_sock);
            continue;
        }

        // Detach thread so it cleans up automatically
        pthread_detach(thread_id);
    }

    close(server_sock);
    return 0;
}
