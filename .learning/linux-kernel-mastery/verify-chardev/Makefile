# Makefile for chardev verification module

obj-m += chardev.o

PWD := $(CURDIR)

all:
	$(MAKE) -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules

clean:
	$(MAKE) -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean

# 验证测试命令
load:
	sudo insmod chardev.ko
	sleep 1
	@echo "Major number:"
	@cat /proc/devices | grep mychardev | awk '{print $$1}'
	sudo mknod -m 666 /dev/mychardev c $$(cat /proc/devices | grep mychardev | awk '{print $$1}') 0 || true

dmesg:
	sudo dmesg | tail -20

test:
	@echo "=== Test 1: Write to device ==="
	echo "Hello from test" | sudo tee /dev/mychardev
	@echo ""
	@echo "=== Test 2: Read from device ==="
	sudo cat /dev/mychardev
	@echo ""
	@echo "=== Test 3: Concurrent open (should fail) ==="
	@sudo cat /dev/mychardev &
	@sleep 0.5
	@echo "Trying second open..."
	@sudo cat /dev/mychardev 2>&1 || echo "Expected: Device busy"
	@wait

unload:
	sudo rm -f /dev/mychardev
	sudo rmmod chardev

verify: load test unload
	@echo "=== Verification Complete ==="
