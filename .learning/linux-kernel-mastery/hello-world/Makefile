# Makefile for hello-world kernel module
# 技巧8应用: 标准kbuild模板

obj-m += hello-world.o

PWD := $(CURDIR)

all:
	$(MAKE) -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules

clean:
	$(MAKE) -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean

# 辅助命令
load:
	sudo insmod hello-world.ko
	sudo dmesg | tail -5

unload:
	sudo rmmod hello-world
	sudo dmesg | tail -5

reload: unload load

info:
	modinfo hello-world.ko
