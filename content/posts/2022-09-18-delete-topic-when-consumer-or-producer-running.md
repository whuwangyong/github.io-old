---
title: "在producer consumer运行时删除topic会怎么样"
date: 2022-09-18
tags: ["kafka"]
categories: ["kafka"]
---

broker端有个参数（kafka_2.13-3.2.1/config/server.properties），`auto.create.topics.enable`，默认为true。意思是，当生产者、消费者读写一个不存在的topic时，是否自动创建该topic。

我们使用kafka自带的脚本（kafka_2.13-3.2.1/bin）进行测试。为了方便使用，我把这些脚本封装了一下，放在[kafka-mate/scripts at master · whuwangyong/kafka-mate (github.com)](https://github.com/whuwangyong/kafka-mate/tree/master/scripts)。

## 1 auto.create.topics.enable=true

### 1.1 消费不存在的topic

（1）初始化环境，然后使用list-topics.sh，可见没有任何topic：

```bash
wy@ship:~/dev/kafka-mate/scripts$ ./reset.sh 
kill kafka and zookeeper...
rm -rf /tmp/kafka-logs /tmp/zookeeper
start...
zookeeper started
waiting kafka starting...
waiting kafka starting...
waiting kafka starting...
waiting kafka starting...
waiting kafka starting...
kafka started
wy@ship:~/dev/kafka-mate/scripts$ ./list-topics.sh

```

（2）消费`test` topic，可见打出了一堆警告（行数不确定，2~10行）：`LEADER_NOT_AVAILABLE`

```bash
wy@ship:~/dev/kafka-mate/scripts$ ./consume-from.sh test
[2022-09-18 02:52:16,148] WARN [Consumer clientId=console-consumer, groupId=console-consumer-27797] Error while fetching metadata with correlation id 2 : {test=LEADER_NOT_AVAILABLE} (org.apache.kafka.clients.NetworkClient)
[2022-09-18 02:52:16,256] WARN [Consumer clientId=console-consumer, groupId=console-consumer-27797] Error while fetching metadata with correlation id 4 : {test=LEADER_NOT_AVAILABLE} (org.apache.kafka.clients.NetworkClient)
[2022-09-18 02:52:16,403] WARN [Consumer clientId=console-consumer, groupId=console-consumer-27797] Error while fetching metadata with correlation id 6 : {test=LEADER_NOT_AVAILABLE} (org.apache.kafka.clients.NetworkClient)
[2022-09-18 02:52:16,559] WARN [Consumer clientId=console-consumer, groupId=console-consumer-27797] Error while fetching metadata with correlation id 8 : {test=LEADER_NOT_AVAILABLE} (org.apache.kafka.clients.NetworkClient)
[2022-09-18 02:52:16,668] WARN [Consumer clientId=console-consumer, groupId=console-consumer-27797] Error while fetching metadata with correlation id 10 : {test=LEADER_NOT_AVAILABLE} (org.apache.kafka.clients.NetworkClient)
[2022-09-18 02:52:16,774] WARN [Consumer clientId=console-consumer, groupId=console-consumer-27797] Error while fetching metadata with correlation id 12 : {test=LEADER_NOT_AVAILABLE} (org.apache.kafka.clients.NetworkClient)

```

（3）此时新开一个终端再次list-topics.sh，会发现`test` topic已经被kafka自动创建了。（如果该topic没有的话，上述消费线程将会一直打印`Error while fetching metadata with correlation id ...`）

（4）那么消费线程是否正常？此时通过`./produce-to.sh`往`test` topic发消息，发现consumer能收到，说明该消费者仍正常工作

### 1.2 生产者写不存在的topic

（1）清理环境

```bash
wy@ship:~/dev/kafka-mate/scripts$ ./reset.sh 
kill kafka and zookeeper...
rm -rf /tmp/kafka-logs /tmp/zookeeper
start...
zookeeper started
waiting kafka starting...
waiting kafka starting...
waiting kafka starting...
waiting kafka starting...
waiting kafka starting...
waiting kafka starting...
kafka started
```

（2）往不存在的`test`topic发送消息：

```bash
wy@ship:~/dev/kafka-mate/scripts$ ./produce-to.sh test
>1
[2022-09-18 03:08:35,111] WARN [Producer clientId=console-producer] Error while fetching metadata with correlation id 4 : {test=LEADER_NOT_AVAILABLE} (org.apache.kafka.clients.NetworkClient)
[2022-09-18 03:08:35,220] WARN [Producer clientId=console-producer] Error while fetching metadata with correlation id 5 : {test=LEADER_NOT_AVAILABLE} (org.apache.kafka.clients.NetworkClient)
[2022-09-18 03:08:35,328] WARN [Producer clientId=console-producer] Error while fetching metadata with correlation id 6 : {test=LEADER_NOT_AVAILABLE} (org.apache.kafka.clients.NetworkClient)
>2
>

```

注意细节，敲完`./produce-to.sh test`回车后，未报警告。只有当输入`1`，然后回车，在真正发送消息时，才会打印`Error while fetching metadata with correlation id ...`

（3）验证消息是否发送成功：

```bash
wy@ship:~/dev/kafka-mate/scripts$ ./consume-from.sh test
1
2

```

可见发送成功了。

### 1.3 消费过程中删除topic

```bash
wy@ship:~/dev/kafka-mate/scripts$ ./consume-from.sh test
1
2
[2022-09-18 03:22:51,090] WARN [Consumer clientId=console-consumer, groupId=console-consumer-14043] Received unknown topic or partition error in fetch for partition test-0 (org.apache.kafka.clients.consumer.internals.Fetcher)
[2022-09-18 03:22:51,101] WARN [Consumer clientId=console-consumer, groupId=console-consumer-14043] Error while fetching metadata with correlation id 141 : {test=LEADER_NOT_AVAILABLE} (org.apache.kafka.clients.NetworkClient)
[2022-09-18 03:22:51,250] WARN [Consumer clientId=console-consumer, groupId=console-consumer-14043] Error while fetching metadata with correlation id 143 : {test=LEADER_NOT_AVAILABLE} (org.apache.kafka.clients.NetworkClient)
[2022-09-18 03:22:51,357] WARN [Consumer clientId=console-consumer, groupId=console-consumer-14043] Error while fetching metadata with correlation id 145 : {test=LEADER_NOT_AVAILABLE} (org.apache.kafka.clients.NetworkClient)
```

topic删除后，consumer立即打印了几行警告日志。

### 1.4 生产过程中删除topic

删除topic时，producer暂时没反应。在下次send消息时，才会打印警告日志。而且，通过再起一个consumer进行验证，发现这个消息是发送成功了。

```bash
>11
>[2022-09-18 03:26:09,786] WARN [Producer clientId=console-producer] Got error produce response with correlation id 13 on topic-partition test-0, retrying (2 attempts left). Error: UNKNOWN_TOPIC_OR_PARTITION (org.apache.kafka.clients.producer.internals.Sender)
[2022-09-18 03:26:09,787] WARN [Producer clientId=console-producer] Received unknown topic or partition error in produce request on partition test-0. The topic-partition may not exist or the user may not have Describe access to it (org.apache.kafka.clients.producer.internals.Sender)
[2022-09-18 03:26:09,810] WARN [Producer clientId=console-producer] Error while fetching metadata with correlation id 14 : {test=LEADER_NOT_AVAILABLE} (org.apache.kafka.clients.NetworkClient)
```

### 1.5 警告为什么有多行？

猜测：不论是producer.send()还是consumer.poll，当topic不存在时，会进行多次尝试，间隔100ms，每次失败就打印一行日志。另一边，broker在创建该topic。当topic创建好后，producer或consumer可以正常使用该topic，则不再打印警告日志。

那么，topic不存在时，producer或consumer会尝试多少次，或者尝试多久呢？下面，将`auto.create.topics.enable`置为false，进行测试。

## 2 auto.create.topics.enable=false

### 2.1 消费不存在的topic

消费者将持续不断的尝试，我测试一小时后还在尝试。这估计是因为`consumer.poll`逻辑写在`while(true)`里面的。

### 2.2 生产者写不存在的topic

生产者在尝试6分钟后停止。

kafka自带测试脚本的生产者和消费者的代码在`kafka-3.2.1-src\core\src\main\scala\kafka\tools\ConsoleConsumer.scala` 和 `ConsoleProducer.scala`。可见ConsoleProducer.scala里面是有3次重试的。

我自己写的测试代码，1分钟后停止尝试。

### 2.3 消费过程中删除topic

由于不会自动创建topic，删了就没有了，consumer将一直包括。

### 2.4 生产过程中删除topic

同上。

## 3 是否启用自动创建topic

个人建议，不要启用。topic应该严格管理，是运维操作。类似数据库里面的表，不能说读写表时，表不存在我就自动创建吧。

再者，自动创建的topic，其分区数为1，可能并不符合预期。不应该在不符合预期的topic上运行，应该尽早报错，failfast。

## 附：测试代码

```java
@Service
public class KafkaMate {

    private static final String SERVER = "192.168.191.128:9092";

    @PostConstruct
    public void init() {
//        consume();
        produce();
    }

    Properties consumerProperties() {
        Properties props = new Properties();
        props.setProperty("bootstrap.servers", SERVER);
        props.setProperty("group.id", "test-g-1");
        props.setProperty("enable.auto.commit", "true");
        props.setProperty("auto.commit.interval.ms", "1000");
        props.setProperty("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
        props.setProperty("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
        return props;
    }

    Properties producerProperties() {
        Properties props = new Properties();
        props.setProperty("bootstrap.servers", SERVER);
        props.put("linger.ms", 1);
        props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        return props;
    }

    void consume() {
        try (KafkaConsumer<String, String> consumer = new KafkaConsumer<>(consumerProperties())) {
            consumer.subscribe(Collections.singleton("test"));
            while (true) {
                ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(1000));
            }
        }
    }

    void produce() {
        try (KafkaProducer<String, String> producer = new KafkaProducer<>(producerProperties())) {
            ProducerRecord<String, String> record = new ProducerRecord<>("test", "hello" + System.currentTimeMillis());
            producer.send(record);
        }
    }

}
```