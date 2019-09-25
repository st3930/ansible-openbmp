## Intoroduction
"BGP Monitoring Protocol" collector server by snas

https://www.snas.io/

required complex operation,

docker install operation are easy setup by ansible and docker-compose

## Requirements
- does not work some script behind proxy
- large resource usese, ex) internet full route<br>
  openbmp_aio  => 10T/CPU, 18GB/Mem, 60GB/Storage<br>
  openbmp_psql =>  8T/CPU, 48GB/Mem, 1TB/Storage<br>

- Please run tests for large memory tuning to openbmp_psql<br>
  large swap size is Required.<br>
  `(0.5 * RAM) + (overcommit_ratio(%) * RAM) = Recommended Swap Size`

  https://access.redhat.com/documentation/ja-jp/red_hat_enterprise_linux/5/html/virtualization/sect-virtualization-tips_and_tricks-overcommitting_with_kvm

  ```
  $ sudo echo "vm.vfs_cache_pressure=500" >> /etc/sysctl.conf
  $ sudo echo "vm.min_free_kbytes=1000000" >> /etc/sysctl.conf
  $ sudo echo "vm.swappiness=10" >> /etc/sysctl.conf
  $ sudo echo "vm.overcommit_memory=2" >> /etc/sysctl.conf
  $ sudo echo "vm.overcommit_ratio=95" >> /etc/sysctl.conf
  $ sudo sysctl -p /etc/sysctl.conf

  $ sudo echo never > /sys/kernel/mm/transparent_hugepage/enabled
  $ sudo echo never > /sys/kernel/mm/transparent_hugepage/defrag
  $ sudo sync && sudo echo 3 > /proc/sys/vm/drop_caches
  $ reboot
  ```

## Confirmed version
- OS: CentOS7.4
- Ansible: 2.8.4

### Ansible install
```
$ sudo yum install sshpass gcc python-devel python-crypto libffi-devel openssl-devel git python2-pip
$ sudo pip install --upgrade pip
$ sudo pip install ansible --version
$ ansible --version
ansible 2.8.4
```

### Git clone ansible-playbook list

```
$ cd ${WORK_DIR}
$ git clone https://github.com/st3930/ansible-openbmp.git
```

### Docker-ce install, if yet
1. easy ansible install and setup
```
$ ansible-playbook install_docker_ce.yml [ --ask-become-pass ]
```

### Openbmp docker easy setup
1. changing parameter

- default use memory size<br>
openbmp_aio  => 3GB<br>
openbmp_psql => 8GB<br>
change to memory setting by install, not enough memory for internet fullroute.

$ vim ./roles/docker/vars/openbmp.yml

2. easy ansible install
```
$ ansible-playbook install_openbmp.yml [ --ask-become-pass ]
```

3. webui access

http://openbmp_ui.local/  : snas_ui<br>
- defaults
```
account: "openbmp"
password: "CiscoRA"
* password change after initial login.
```

http://grafana.local/    : grafana_ui<br>
- defaults
```
account: "openbmp"
password: "Snas123"
* password change after initial login.
```

4. and more...
- bmp router setup

#### chnage log
##### 2019-09-24 initial by st3930
