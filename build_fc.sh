#!/bin/bash
set -e
cd ~/zero-idle-research
gcc -O2 -static -no-pie -o serverfc.elf serverfc.c
wget -q https://s3.amazonaws.com/spec.ccfc.min/img/hello/kernel/hello-vmlinux.bin
dd if=/dev/zero of=fc-rootfs.ext4 bs=1M count=64
mkfs.ext4 -q fc-rootfs.ext4
sudo mkdir -p /mnt/fcroot
sudo mount -o loop fc-rootfs.ext4 /mnt/fcroot
sudo cp serverfc.elf /mnt/fcroot/init
sudo chmod 755 /mnt/fcroot/init
sudo mkdir -p /mnt/fcroot/dev
sudo mknod /mnt/fcroot/dev/console c 5 1
sudo mknod /mnt/fcroot/dev/null c 1 3
sudo mknod /mnt/fcroot/dev/ttyS0 c 4 64
sudo chmod 600 /mnt/fcroot/dev/console
sudo umount /mnt/fcroot
ls -l hello-vmlinux.bin fc-rootfs.ext4 serverfc.elf
