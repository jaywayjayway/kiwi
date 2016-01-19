# Kiwi, Kubernetes IP 管理工具

这是一个将 Kubernetes 分配的IP地址配置到网络接口并生产防火墙规则的管理服务

`kiwi` 服务将监听 Kubernetes API, 监听对 Service 的新增和删除, 通过包含的 `deprecatedPublicIPs` 的值做以下事情: 

- 将该值配置在网络接口上, 如果这个 IP 还未被分配
- 创建 `mangle` 表中对入栈流量设置 mark

Kiwi 使用 etcd 来配置协调多个节点之间的 IP 分配. 如果一个节点上的 Kiwi 停止运行, 任何活跃的 Kiwi 都将继续分配可用的 IP.

## 打包 kiwi 

    python setup.py  install

## 使用 Kiwi

使用 Kiwi 最快的方法是使用 docker image:

    docker run --privileged --net=host larsks/kiwi --interface br0 --verbose

Kiwi 需要 `--net=host` 和 `--privileged` 参数, 因为它需要修改节点的网络接口配置以及 iptables 规则.

## 例如

假如在 Kubernetes 中定义一个 service:

    kind: Service
    apiVersion: v1
    metadata:
      name: web
    spec:
      ports:
      - port: 8080
        targetport: 80
        protocol: TCP
      selector:
        name: web
      externalIPs:
        - 192.168.1.41
        - 172.16.1.41  
如果你这样运行 `kiwi` (kiwi是个启动脚本，位于`bin`目录下)

    kiwi --interface=em1  --cidr-range  192.168.0.0/16 --kube-endpoint http://localhost:8080 --etcd-endpoint http://localhost:2379 


也可使用`systemd`来管理`wiki`:

1. 把`kwi.service`拷贝到Centos7的`/usr/lib/systemd/system/`目录下
2. 把`conf/kiwi.conf`拷贝到Centos7的 `/etc/`目录
3. 配置`/etc/kiwi.conf`相关选项
4. 注册`kiwi.service`服务到`systemd`
        systemctl  daemon-reload
5. 使用`systemd`来启动`kiwi`
        systemctl start  kiwi
6. 日志文件位于`/var/log/kiki/kiwi.log`

    
然后创建 Kubernetes services:

    kubectl create -f web-service.yaml

然后 `kuwi` 将做如下操作:

- 添加 IP 地址 192.168.1.42/32 到设备 `em1`:

        # ip addr show em1 | grep 192.168.1.41
        inet 192.168.1.41/32 scope global em1:kube

- 添加以下规则到 `mangle` 表中的 `KUBE-PUBLIC`
  table:

        -A KUBE-PUBLIC -d 192.168.1.41/32 -p tcp -m tcp --dport 8080 -m comment --comment web -j MARK --set-mark 1

- Kiwi 将会忽略 `172.16.1.41` 因为它不符合然后有效的 CIDR 范围.

- **在我们的系统里，关闭在宿主机上网段设置，不再指定 `--cidr-range`,public IP由管理分配，不再验证**





如果 service 被删除, 这些改变也将被移除

当 `kiwi` 退出时, 它将删除它在运行时创建的任何地址和防火墙规则.

## 技术细节

Kiwi 通过监听 Kubernetes API `/api/v1/watch/services`. 当一个新的 services 被创建, Kiwi 将迭代 IP 地址列表并且尝试将其保存在 etcd `/kiwi/publicips`.

如果它能够成功创建该记录, 本地的 Kiwi 将会在本地声明这个地址.

地址将会被设置一个 TTL(默认10秒). 本地的 kiwi 将会维护这个地址记录的心跳. 如果这个 agent 停止运行, `/kiwi/publicips/x.x.x.x` 记录将最终过期, 其他的节点将会尝试接管它.

