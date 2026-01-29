CC = gcc
CFLAGS = -Wall -Wextra -pthread -g -O0
TARGET = server

all: $(TARGET)

$(TARGET): server.c
	$(CC) $(CFLAGS) -o $(TARGET) server.c

clean:
	rm -f $(TARGET)

.PHONY: all clean
