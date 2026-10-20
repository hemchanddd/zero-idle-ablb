#!/bin/bash
qemu-system-x86_64 -machine q35 -device pcie-root-port,port=0x10,chassis=1,id=pci.1,bus=pcie.0,multifunction=on,addr=0x3 -device pcie-root-port,port=0x11,chassis=2,id=pci.2,bus=pcie.0,addr=0x3.0x6 -device pcie-root-port,port=0x12,chassis=3,id=pci.4,bus=pcie.0,addr=0x3.0x4 -device virtio-scsi-pci,bus=pci.2,addr=0x0,id=scsi0 -device scsi-hd,bus=scsi0.0,drive=hd0 -vga none -smp 1 -m 64M -device virtio-rng-pci -machine accel=kvm:tcg -cpu host -drive file=/home/hemchand/.ops/images/server,format=raw,if=none,id=hd0 -device virtio-net,bus=pci.4,addr=0x0,netdev=n0,mac=52:54:00:00:00:01 -netdev user,id=n0,hostfwd=tcp::8080-:8080 -display none -serial null -snapshot &
sleep 2
curl -s http://127.0.0.1:8080/
echo
pkill -f qemu-system
