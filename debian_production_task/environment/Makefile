PREFIX ?= /usr
DESTDIR ?=

all: hello_bin

hello_bin: hello.c
	$(CC) $(CFLAGS) $(LDFLAGS) -o hello_bin hello.c

install: hello_bin
	install -D -m 0755 hello_bin $(DESTDIR)$(PREFIX)/bin/hello_bin

clean:
	rm -f hello_bin

.PHONY: all install clean
