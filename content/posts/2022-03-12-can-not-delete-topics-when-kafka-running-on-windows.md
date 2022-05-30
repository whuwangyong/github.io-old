---
title: "kafka在Windows上无法动态删除topic"
date: 2022-03-12
tags: ["kafka", "kafka topic"]
categories: ["kafka"]
---
## 问题描述

删除topic时导致集群崩溃，报错：

> ERROR Shutdown broker because all log dirs in D:\tmp\kafka-logs have failed.

测试了kafka_2.11-1.1.0、kafka_2.13-2.5.0、kafka_2.13-2.6.2、kafka_2.13-2.7.0四个版本，都有这个问题。

搜索了网络，发现这个bug很早之前就提出了，但至今没解决。

* [https://issues.apache.org/jira/browse/KAFKA-10419](https://issues.apache.org/jira/browse/KAFKA-10419)
* [https://issues.apache.org/jira/browse/KAFKA-9458](https://issues.apache.org/jira/browse/KAFKA-9458)
* [https://github.com/apache/kafka/pull/6329](https://github.com/apache/kafka/pull/6329)
* [https://stackoverflow.com/questions/50755827/accessdeniedexception-when-deleting-a-topic-on-windows-kafka](https://stackoverflow.com/questions/50755827/accessdeniedexception-when-deleting-a-topic-on-windows-kafka)

> Linux上无此问题。

使用如下命令即可复现：

```powershell
D:\kafka_2.13-2.6.2>bin\windows\kafka-topics.bat --bootstrap-server 127.0.0.1:9092 --create --topic testwy
Created topic testwy.

D:\kafka_2.13-2.6.2>bin\windows\kafka-topics.bat --bootstrap-server 127.0.0.1:9092 --list
testwy

D:\kafka_2.13-2.6.2>bin\windows\kafka-topics.bat --bootstrap-server 127.0.0.1:9092 --delete --topic testwy
```

此时集群崩溃，zookeeper日志：

```powershell
[2021-07-05 16:32:52,965] WARN Exception causing close of session 0x1003d29550c0000: 远程主机强迫关闭了一个现有的连接。 (org.apache.zookeeper.server.NIOServerCnxn)
[2021-07-05 16:33:11,170] INFO Expiring session 0x1003d29550c0000, timeout of 18000ms exceeded (org.apache.zookeeper.server.ZooKeeperServer)
```

但zk仍然在运行。

kafka server日志：

```powershell
[2021-07-05 16:32:52,574] INFO [GroupCoordinator 0]: Removed 0 offsets associated with deleted partitions: testwy-0. (kafka.coordinator.group.GroupCoordinator)
[2021-07-05 16:32:52,599] INFO [ReplicaFetcherManager on broker 0] Removed fetcher for partitions Set(testwy-0) (kafka.server.ReplicaFetcherManager)
[2021-07-05 16:32:52,600] INFO [ReplicaAlterLogDirsManager on broker 0] Removedfetcher for partitions Set(testwy-0) (kafka.server.ReplicaAlterLogDirsManager)
[2021-07-05 16:32:52,607] INFO [ReplicaFetcherManager on broker 0] Removed fetcher for partitions Set(testwy-0) (kafka.server.ReplicaFetcherManager)
[2021-07-05 16:32:52,608] INFO [ReplicaAlterLogDirsManager on broker 0] Removedfetcher for partitions Set(testwy-0) (kafka.server.ReplicaAlterLogDirsManager)
[2021-07-05 16:32:52,615] ERROR Error while renaming dir for testwy-0 in log dir D:\tmp\kafka-logs (kafka.server.LogDirFailureChannel)
java.nio.file.AccessDeniedException: D:\tmp\kafka-logs\testwy-0 -> D:\tmp\kafka-logs\testwy-0.a61ed5f8a99e4df58e8bf86c6c5e537c-delete
        at java.base/sun.nio.fs.WindowsException.translateToIOException(WindowsException.java:89)
        at java.base/sun.nio.fs.WindowsException.rethrowAsIOException(WindowsException.java:103)
        at java.base/sun.nio.fs.WindowsFileCopy.move(WindowsFileCopy.java:395)
        at java.base/sun.nio.fs.WindowsFileSystemProvider.move(WindowsFileSystemProvider.java:288)
        at java.base/java.nio.file.Files.move(Files.java:1421)
        at org.apache.kafka.common.utils.Utils.atomicMoveWithFallback(Utils.java:917)
        at kafka.log.Log.$anonfun$renameDir$2(Log.scala:1012)
        at kafka.log.Log.renameDir(Log.scala:2387)
        at kafka.log.LogManager.asyncDelete(LogManager.scala:973)
        at kafka.log.LogManager.$anonfun$asyncDelete$3(LogManager.scala:1008)
        at kafka.log.LogManager.$anonfun$asyncDelete$2(LogManager.scala:1006)
        at kafka.log.LogManager.$anonfun$asyncDelete$2$adapted(LogManager.scala:1004)
        at scala.collection.mutable.HashSet$Node.foreach(HashSet.scala:435)
        at scala.collection.mutable.HashSet.foreach(HashSet.scala:361)
        at kafka.log.LogManager.asyncDelete(LogManager.scala:1004)
        at kafka.server.ReplicaManager.stopReplicas(ReplicaManager.scala:481)
        at kafka.server.KafkaApis.handleStopReplicaRequest(KafkaApis.scala:271)
        at kafka.server.KafkaApis.handle(KafkaApis.scala:142)
        at kafka.server.KafkaRequestHandler.run(KafkaRequestHandler.scala:74)
        at java.base/java.lang.Thread.run(Thread.java:834)
        Suppressed: java.nio.file.AccessDeniedException: D:\tmp\kafka-logs\testwy-0 -> D:\tmp\kafka-logs\testwy-0.a61ed5f8a99e4df58e8bf86c6c5e537c-delete
                at java.base/sun.nio.fs.WindowsException.translateToIOException(WindowsException.java:89)
                at java.base/sun.nio.fs.WindowsException.rethrowAsIOException(WindowsException.java:103)
                at java.base/sun.nio.fs.WindowsFileCopy.move(WindowsFileCopy.java:309)
                at java.base/sun.nio.fs.WindowsFileSystemProvider.move(WindowsFileSystemProvider.java:288)
                at java.base/java.nio.file.Files.move(Files.java:1421)
                at org.apache.kafka.common.utils.Utils.atomicMoveWithFallback(Utils.java:914)
                ... 14 more
[2021-07-05 16:32:52,630] WARN [ReplicaManager broker=0] Stopping serving replicas in dir D:\tmp\kafka-logs (kafka.server.ReplicaManager)
[2021-07-05 16:32:52,641] WARN [ReplicaManager broker=0] Broker 0 stopped fetcher for partitions  and stopped moving logs for partitions  because they are in the failed log directory D:\tmp\kafka-logs. (kafka.server.ReplicaManager)
[2021-07-05 16:32:52,643] WARN Stopping serving logs in dir D:\tmp\kafka-logs (kafka.log.LogManager)
[2021-07-05 16:32:52,647] ERROR Shutdown broker because all log dirs in D:\tmp\kafka-logs have failed (kafka.log.LogManager)
```

kafka server直接关闭了。

## 解决办法

直接重启kafka-sever依然会报错。需先删除`tmp`目录下的全部log文件，然后再重启。