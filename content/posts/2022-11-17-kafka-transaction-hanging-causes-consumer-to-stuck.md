---
title: "Kafka transaction hanging causes consumer to stuck"
date: 2022-11-17
tags: ["kafka","kafka事务"]
categories: ["kafka"]
---

Kafka事务未关闭导致消费者无法消费消息。

## 背景

最近遇到一个问题：有一个公用topic，很多应用都读写这个topic。从某个时间点开始，所有消费该topic的消费者（read_committed级别）都拉不到消息了。随机看了一些应用的日志，未发现生产者报错，仍然能正常发消息并提交事务，消费者也未报错。打开运维工具，用`read_uncommitted`​级别的消费者查看该topic里面的消息，发现LSO（last stable offset）一直卡在某个offset，LEO（log end offset）仍在持续增加。

## 原因

1. 生产者开启了事务，由于程序bug，在异常退出的情况下，producer的**commit、abort**都没执行到，后果就是**事务未关闭**。
2. 事务除了手动commit、abort两种方式进行主动关闭外，还可以通过**超时**​被动关闭。

    > broker 端事务超时时间配置：transaction.max.timeout.ms，默认15分钟
    >
    > producer 端事务超时时间配置：transaction.timeout.ms，默认1分钟
    >
3. 但是我们将事务超时时间设置得非常大，5小时。未关闭的事务将会等待5小时才能被动关闭。这5小时内，后续的消息都无法被消费。注意，虽然无法消费，但是**不同事务Id**​的其他生产者却能继续往该topic提交事务。但是这些已提交的消息是不能被消费的，这是通过LastStableOffset（LSO）进行控制的。LSO 的定义是，`smallest offset of any open transaction`​，已开启的事务里面offset最小的那一个值，可消费的offset是小于LSO的。
4. 为什么后续已提交事务的消息也无法被消费呢？因为Kafka要保证**partition内的消息是有序**的。当前序事务未结束，如果先消费了后续消息，此时前序事务即使提交也无意义了，因为消费者不能将offset倒回去消费它。如果倒回去消费，顺序就乱了。所以，前序事务必须结束，不管是主动commit/abort，还是超时被动abort，总之必须结束，后续消息才能被消费。

## 复现方案及延申测试

创建2个事务生产者tx-producer-1、tx-producer-2，创建1个非事务的生产者nontx-producer，创建1个隔离级别（`isolation.level`​）为read_committed的rc-consumer，1个隔离级别为`read_uncommitted`​的runc-consumer。

* nontx-producer每秒发一个消息
* tx-producer-1每秒提交一个事务，一个事务里面发送2条消息
* tx-producer-2每秒提交一个事务，一个事务里面发送2条消息；但是，在做第三个事务时，发了2条消息后，不提交，长时间sleep
* rc-comsumer和runc-consumer持续消费，打印消费的消息

每个生产者、消费者在自己的线程运行，互不影响。使用Kafka_2.13-3.3.1版本。

kafka使用默认配置。

### producer.close会立即关闭事务吗-会

结论：会

代码：

```java
for (int i = 1000; i < 2000; i += 2) {
    try {
        producer.beginTransaction();

        producer.send(new ProducerRecord<>(testTopic, "msg-" + i));
        log.info("[tx-producer-2]sent tx msg-" + i);
        producer.send(new ProducerRecord<>(testTopic, "msg-" + (i + 1)));
        log.info("[tx-producer-2]sent tx msg-" + (i + 1));

        // 挂起事务
        if (i == 1004) {
            log.warn("tx-producer-2 hanging tx");
            TimeUnit.SECONDS.sleep(5);
            log.warn("tx-producer-2 close");
            producer.close();
            return;
        }

        producer.commitTransaction();
    } catch (Exception e) {
        producer.abortTransaction();
        log.warn("tx-producer-2 abort tx");
    }
}
```

操作：在IDEA运行应用即可

应用日志：

```plaintext
2022-11-17 09:56:39.757  WARN 2288 --- [pool-5-thread-1] cn.whu.wy.kafkamate.service.KafkaTxTest  : tx-producer-2 close
2022-11-17 09:56:39.757  INFO 2288 --- [pool-5-thread-1] o.a.k.clients.producer.KafkaProducer     : [Producer clientId=producer-tx-producer-2, transactionalId=tx-producer-2] Closing the Kafka producer with timeoutMillis = 9223372036854775807 ms.
2022-11-17 09:56:39.757 DEBUG 2288 --- [r-tx-producer-2] o.a.k.clients.producer.internals.Sender  : [Producer clientId=producer-tx-producer-2, transactionalId=tx-producer-2] Beginning shutdown of Kafka producer I/O thread, sending remaining records.
2022-11-17 09:56:39.757  INFO 2288 --- [r-tx-producer-2] o.a.k.clients.producer.internals.Sender  : [Producer clientId=producer-tx-producer-2, transactionalId=tx-producer-2] Aborting incomplete transaction due to shutdown
2022-11-17 09:56:39.758 DEBUG 2288 --- [r-tx-producer-2] o.a.k.c.p.internals.TransactionManager   : [Producer clientId=producer-tx-producer-2, transactionalId=tx-producer-2] Transition from state IN_TRANSACTION to ABORTING_TRANSACTION
2022-11-17 09:56:39.758 DEBUG 2288 --- [r-tx-producer-2] o.a.k.c.p.internals.TransactionManager   : [Producer clientId=producer-tx-producer-2, transactionalId=tx-producer-2] Enqueuing transactional request EndTxnRequestData(transactionalId='tx-producer-2', producerId=2, producerEpoch=0, committed=false)
2022-11-17 09:56:39.758 DEBUG 2288 --- [r-tx-producer-2] o.a.k.clients.producer.internals.Sender  : [Producer clientId=producer-tx-producer-2, transactionalId=tx-producer-2] Sending transactional request EndTxnRequestData(transactionalId='tx-producer-2', producerId=2, producerEpoch=0, committed=false) to node ship:9092 (id: 0 rack: null) with correlation ID 40
2022-11-17 09:56:39.758 DEBUG 2288 --- [r-tx-producer-2] org.apache.kafka.clients.NetworkClient   : [Producer clientId=producer-tx-producer-2, transactionalId=tx-producer-2] Sending END_TXN request with header RequestHeader(apiKey=END_TXN, apiVersion=3, clientId=producer-tx-producer-2, correlationId=40) and timeout 30000 to node 0: EndTxnRequestData(transactionalId='tx-producer-2', producerId=2, producerEpoch=0, committed=false)
2022-11-17 09:56:39.761 DEBUG 2288 --- [r-tx-producer-2] org.apache.kafka.clients.NetworkClient   : [Producer clientId=producer-tx-producer-2, transactionalId=tx-producer-2] Received END_TXN response from node 0 for request with header RequestHeader(apiKey=END_TXN, apiVersion=3, clientId=producer-tx-producer-2, correlationId=40): EndTxnResponseData(throttleTimeMs=0, errorCode=0)
2022-11-17 09:56:39.761 DEBUG 2288 --- [r-tx-producer-2] o.a.k.c.p.internals.TransactionManager   : [Producer clientId=producer-tx-producer-2, transactionalId=tx-producer-2] Transition from state ABORTING_TRANSACTION to READY
2022-11-17 09:56:39.762 DEBUG 2288 --- [r-tx-producer-2] o.a.k.clients.producer.internals.Sender  : [Producer clientId=producer-tx-producer-2, transactionalId=tx-producer-2] Shutdown of Kafka producer I/O thread has completed.
2022-11-17 09:56:39.762  INFO 2288 --- [pool-5-thread-1] org.apache.kafka.common.metrics.Metrics  : Metrics scheduler closed
2022-11-17 09:56:39.762  INFO 2288 --- [pool-5-thread-1] org.apache.kafka.common.metrics.Metrics  : Closing reporter org.apache.kafka.common.metrics.JmxReporter
2022-11-17 09:56:39.762  INFO 2288 --- [pool-5-thread-1] org.apache.kafka.common.metrics.Metrics  : Metrics reporters closed
2022-11-17 09:56:39.763  INFO 2288 --- [pool-5-thread-1] o.a.kafka.common.utils.AppInfoParser     : App info kafka.producer for producer-tx-producer-2 unregistered
```

“Aborting incomplete transaction due to shutdown”，可见在producer.close()会关闭未完成的事务。

kafka server.log：

只有初始化事务的日志，没有结束事务的日志

```plaintext
[2022-11-17 09:15:03,988] INFO [TransactionCoordinator id=0] Initialized transactionalId tx-producer-2 with producerId 2 and producer epoch 0 on partition __transaction_state-2 (kafka.coordinator.transaction.TransactionCoordinator)
[2022-11-17 09:15:03,995] INFO [TransactionCoordinator id=0] Initialized transactionalId tx-producer-1 with producerId 1 and producer epoch 0 on partition __transaction_state-1 (kafka.coordinator.transaction.TransactionCoordinator)
```

### 应用进程退出会立即关闭事务吗-不会

结论：不会

代码：

```java
for (int i = 1000; i < 2000; i += 2) {
    try {
        producer.beginTransaction();

        producer.send(new ProducerRecord<>(testTopic, "msg-" + i));
        log.info("[tx-producer-2]sent tx msg-" + i);
        producer.send(new ProducerRecord<>(testTopic, "msg-" + (i + 1)));
        log.info("[tx-producer-2]sent tx msg-" + (i + 1));

        // 挂起事务
        if (i == 1004) {
            log.warn("tx-producer-2 hanging tx");
            TimeUnit.MINUTES.sleep(60); // 长时间sleep
        }

        producer.commitTransaction();
    } catch (Exception e) {
        producer.abortTransaction();
        log.warn("tx-producer-2 abort tx");
    }
}
```

操作：在IDEA里面运行应用，在sleep过程中点击停止

应用日志：

```plaintext
Started MateApp in 1.702 seconds (JVM running for 2.123)
2022-11-16 21:05:58.582  INFO 14572 --- [pool-2-thread-1] cn.whu.wy.kafkamate.service.KafkaTxTest  : runc pool...
2022-11-16 21:05:58.582  INFO 14572 --- [pool-1-thread-1] cn.whu.wy.kafkamate.service.KafkaTxTest  : rc pool...
2022-11-16 21:05:58.609  INFO 14572 --- [pool-3-thread-1] cn.whu.wy.kafkamate.service.KafkaTxTest  : [nontx-producer]sent msg-0
2022-11-16 21:05:59.104  INFO 14572 --- [pool-5-thread-1] cn.whu.wy.kafkamate.service.KafkaTxTest  : [tx-producer-2]sent tx msg-1000
2022-11-16 21:06:00.192  INFO 14572 --- [pool-1-thread-1] cn.whu.wy.kafkamate.service.KafkaTxTest  : consumer[rc] received: msg-1000
2022-11-16 21:06:00.192  INFO 14572 --- [pool-1-thread-1] cn.whu.wy.kafkamate.service.KafkaTxTest  : consumer[rc] received: msg-1001
...
...
2022-11-16 21:06:02.160  WARN 14572 --- [pool-5-thread-1] cn.whu.wy.kafkamate.service.KafkaTxTest  : tx-producer-2 hanging tx
2022-11-16 21:06:02.254  INFO 14572 --- [pool-2-thread-1] cn.whu.wy.kafkamate.service.KafkaTxTest  : runc pool...
2022-11-16 21:06:02.256  INFO 14572 --- [pool-1-thread-1] cn.whu.wy.kafkamate.service.KafkaTxTest  : consumer[rc] received: msg-2004
2022-11-16 21:06:02.256  INFO 14572 --- [pool-1-thread-1] cn.whu.wy.kafkamate.service.KafkaTxTest  : consumer[rc] received: msg-2005
2022-11-16 21:06:02.256  INFO 14572 --- [pool-1-thread-1] cn.whu.wy.kafkamate.service.KafkaTxTest  : rc pool...
2022-11-16 21:06:02.290  INFO 14572 --- [pool-2-thread-1] cn.whu.wy.kafkamate.service.KafkaTxTest  : consumer[read_uncommitted] received: msg-2006
2022-11-16 21:06:02.290  INFO 14572 --- [pool-2-thread-1] cn.whu.wy.kafkamate.service.KafkaTxTest  : consumer[read_uncommitted] received: msg-2007
...
...
2022-11-16 21:06:08.265  INFO 14572 --- [pool-2-thread-1] cn.whu.wy.kafkamate.service.KafkaTxTest  : consumer[read_uncommitted] received: msg-2018
2022-11-16 21:06:08.265  INFO 14572 --- [pool-2-thread-1] cn.whu.wy.kafkamate.service.KafkaTxTest  : consumer[read_uncommitted] received: msg-2019
2022-11-16 21:06:08.265  INFO 14572 --- [pool-2-thread-1] cn.whu.wy.kafkamate.service.KafkaTxTest  : runc pool...
2022-11-16 21:06:08.292  INFO 14572 --- [pool-1-thread-1] cn.whu.wy.kafkamate.service.KafkaTxTest  : rc pool...

Process finished with exit code 130

```

在事务挂起后，consumer[rc]就再也消费不到消息了，只有consumer[read_uncommitted]还能消费到。

kafka server.log:

```plaintext
[2022-11-16 21:06:00,359] INFO [TransactionCoordinator id=0] Initialized transactionalId tx-producer-2 with producerId 2 and producer epoch 0 on partition __transaction_state-2 (kafka.coordinator.transaction.TransactionCoordinator)
...
[2022-11-16 21:07:03,861] INFO [TransactionCoordinator id=0] Completed rollback of ongoing transaction for transactionalId tx-producer-2 due to timeout (kafka.coordinator.transaction.TransactionCoordinator)

```

可见，tx-producer-2的事务在init1分钟后自动rollback。应用在21:06:13停止，事务在21:07:03回滚。应用停止时事务并未立即回滚。

### System.exit会立即关闭事务吗-不会

结论：不会

代码：

```java
for (int i = 1000; i < 2000; i += 2) {
    try {
        producer.beginTransaction();

        producer.send(new ProducerRecord<>(testTopic, "msg-" + i));
        log.info("[tx-producer-2]sent tx msg-" + i);
        producer.send(new ProducerRecord<>(testTopic, "msg-" + (i + 1)));
        log.info("[tx-producer-2]sent tx msg-" + (i + 1));

        // 挂起事务
        if (i == 1004) {
            log.warn("tx-producer-2 system exit");
            System.exit(-1);
        }

        producer.commitTransaction();
    } catch (Exception e) {
        producer.abortTransaction();
        log.warn("tx-producer-2 abort tx");
    }
}
```

应用日志：

```plaintext
...
2022-11-17 10:18:49.195  WARN 10736 --- [pool-5-thread-1] cn.whu.wy.kafkamate.service.KafkaTxTest  : tx-producer-2 system exit
...
Process finished with exit code -1
```

kafka server.log

```plaintext
[2022-11-17 10:18:46,106] INFO [TransactionCoordinator id=0] Initialized transactionalId tx-producer-1 with producerId 1 and producer epoch 0 on partition __transaction_state-1 (kafka.coordinator.transaction.TransactionCoordinator)
[2022-11-17 10:18:46,176] INFO [TransactionCoordinator id=0] Initialized transactionalId tx-producer-2 with producerId 2 and producer epoch 0 on partition __transaction_state-2 (kafka.coordinator.transaction.TransactionCoordinator)

[2022-11-17 10:19:52,492] INFO [TransactionCoordinator id=0] Completed rollback of ongoing transaction for transactionalId tx-producer-1 due to timeout (kafka.coordinator.transaction.TransactionCoordinator)
[2022-11-17 10:19:52,496] INFO [TransactionCoordinator id=0] Completed rollback of ongoing transaction for transactionalId tx-producer-2 due to timeout (kafka.coordinator.transaction.TransactionCoordinator)
```

看起来应用System.exit(-1) 3秒后事务就回滚了。再做一次

```plaintext
# 应用日志
2022-11-17 10:27:00.366  WARN 20524 --- [pool-5-thread-1] cn.whu.wy.kafkamate.service.KafkaTxTest  : tx-producer-2 system exit

# kafka server 日志
[2022-11-17 10:26:53,406] INFO [TransactionCoordinator id=0] Initialized transactionalId tx-producer-1 with producerId 2 and producer epoch 0 on partition __transaction_state-1 (kafka.coordinator.transaction.TransactionCoordinator)
[2022-11-17 10:26:53,406] INFO [TransactionCoordinator id=0] Initialized transactionalId tx-producer-2 with producerId 1 and producer epoch 0 on partition __transaction_state-2 (kafka.coordinator.transaction.TransactionCoordinator)

[2022-11-17 10:28:02,428] INFO [TransactionCoordinator id=0] Completed rollback of ongoing transaction for transactionalId tx-producer-1 due to timeout (kafka.coordinator.transaction.TransactionCoordinator)
[2022-11-17 10:28:02,432] INFO [TransactionCoordinator id=0] Completed rollback of ongoing transaction for transactionalId tx-producer-2 due to timeout (kafka.coordinator.transaction.TransactionCoordinator)

```

这次相差一分钟。

‍

### Thread.stop会立即关闭事务吗-不会

结论：不会

代码：

```java
for (int i = 1000; i < 2000; i += 2) {
    try {
        producer.beginTransaction();

        producer.send(new ProducerRecord<>(testTopic, "msg-" + i));
        log.info("[tx-producer-2]sent tx msg-" + i);
        producer.send(new ProducerRecord<>(testTopic, "msg-" + (i + 1)));
        log.info("[tx-producer-2]sent tx msg-" + (i + 1));

        // 挂起事务
        if (i == 1004) {
            log.info("tx-producer-1 stop");
            Thread.currentThread().stop();
        }

        producer.commitTransaction();
    } catch (Exception e) {
        producer.abortTransaction();
        log.warn("tx-producer-2 abort tx");
    }
}
```

应用日志：

```plaintext
2022-11-17 10:45:22.239  INFO 7504 --- [pool-5-thread-1] cn.whu.wy.kafkamate.service.KafkaTxTest  : tx-producer-1 stop
```

kafka server.log：

```plaintext
[2022-11-17 10:45:15,340] INFO [TransactionCoordinator id=0] Initialized transactionalId tx-producer-2 with producerId 2 and producer epoch 0 on partition __transaction_state-2 (kafka.coordinator.transaction.TransactionCoordinator)
[2022-11-17 10:46:22,035] INFO [TransactionCoordinator id=0] Completed rollback of ongoing transaction for transactionalId tx-producer-2 due to timeout (kafka.coordinator.transaction.TransactionCoordinator)
```

生产者线程stop后一分钟，broker回滚事务。

## 总结

1. `transaction.timeout.ms`​（producer）、`transaction.max.timeout.ms`​（broker）、`request.timeout.ms`​（broker）三个参数尤其重要，不能配得太大。
2. 异常处理要完备，确保commit、abort、close方法能被执行到

## 如何检测挂起的事务

这个不消费的问题我排查了很久，知道原因后自然而然想到，有没有手段可以检测到未关闭的事务呢？[KIP-664](https://cwiki.apache.org/confluence/display/KAFKA/KIP-664%3A+Provide+tooling+to+detect+and+abort+hanging+transactions) 正在讨论这个问题。

在这个特性发布之前，我们可以用一些其他方式勉强实现这个功能。创建一个`read_uncommitted`​的消费者，消费同样的topic partition，然后比较end offset。如果`read_uncommitted`​的end offset 逐渐增加，`read_committed`​的end offset 长时间未增加，则说明位于`end offset + 1`​的事务未提交。`read_uncommitted`​的`end offset+1`​就是 LSO。

## 如何关闭挂起的事务

一般来讲，如果应用异常退出，未提交的事务就只有一个结局了：就是回滚，要么由producer发起，要么超时时间到了由broker自动执行。

有时应用崩了，一时半会儿也无法运行起来，它开启的事务无法主动关闭，只能等超时。如果超时时间很久，对其他应用影响很大。此时，可以使用上一节描述的方法，将挂起的事务检测出来。LSO这个offset上的消息，就是第一个未关闭事务的第一条消息。查看该消息的内容可以知道是哪个应用发送了这条消息，进而得出发送该消息的应用的事务Id。然后使用该Id创建一个producer，再执行`producer.initTransactions()`​，之前的“旧”事务就会被关闭。

‍

## Reference

1. [KIP-664: Provide tooling to detect and abort hanging transactions - Apache Kafka - Apache Software Foundation](https://cwiki.apache.org/confluence/display/KAFKA/KIP-664%3A+Provide+tooling+to+detect+and+abort+hanging+transactions)
2. [[KAFKA-12671] Out of order processing with a transactional producer can lead to a stuck LastStableOffset - ASF JIRA (apache.org)](https://issues.apache.org/jira/browse/KAFKA-12671)
3. [[KAFKA-5880] Transactional producer and read committed consumer causes consumer to stuck - ASF JIRA (apache.org)](https://issues.apache.org/jira/browse/KAFKA-5880)
4. [Is it possible to force abort a Kafka transaction? - Stack Overflow](https://stackoverflow.com/questions/69596665/is-it-possible-to-force-abort-a-kafka-transaction)

##  附：测试代码

```java
package cn.whu.wy.kafkamate.service;

import cn.whu.wy.kafkamate.bean.TopicInfo;
import lombok.extern.slf4j.Slf4j;
import org.apache.kafka.clients.consumer.Consumer;
import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.kafka.clients.consumer.KafkaConsumer;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.Producer;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.common.KafkaException;
import org.apache.kafka.common.errors.AuthorizationException;
import org.apache.kafka.common.errors.OutOfOrderSequenceException;
import org.apache.kafka.common.errors.ProducerFencedException;
import org.springframework.beans.factory.InitializingBean;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.Collections;
import java.util.Properties;
import java.util.Set;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/**
 * kafka事务测试。测试未关闭的事务，对消费者的影响
 *
 * @author WangYong
 * Date 2022/11/15
 * Time 22:05
 */
@Service
@Slf4j
public class KafkaTxTest implements InitializingBean {

    private final String bootstrapServers = "192.168.136.128:9092";

    @Autowired
    private TopicManager topicManager;


    @Override
    public void afterPropertiesSet() throws Exception {
        final String testTopic = "test-tx";

        TopicInfo topicInfo = new TopicInfo(testTopic, 1, (short) 1);
        topicManager.createTopics(Set.of(topicInfo));

        Executors.newSingleThreadExecutor().execute(() -> {
            try (Consumer<String, String> consumer = genRcConsumer("rc-consumer")) {
                consumer.subscribe(Collections.singleton(testTopic));
                while (true) {
                    ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(1000));
                    records.forEach(r -> log.info("consumer[rc] received: {}", r.value()));
                    log.info("rc pool...");
                }
            }
        });

        Executors.newSingleThreadExecutor().execute(() -> {
            try (Consumer<String, String> consumer = genRuncConsumer("runc-consumer")) {
                consumer.subscribe(Collections.singleton("test-tx"));
                while (true) {
                    ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(1000));
                    records.forEach(r -> log.info("consumer[read_uncommitted] received: {}", r.value()));
                    log.info("runc pool...");
                }
            }
        });


        // 每秒发1个消息，10条消息
        Executors.newSingleThreadExecutor().execute(() -> {
            try (Producer<String, String> producer = genProducer()) {
                for (int i = 0; i < 10; i++) {
                    producer.send(new ProducerRecord<>(testTopic, "msg-" + i));
                    TimeUnit.SECONDS.sleep(1);
                    log.info("[nontx-producer]sent msg-" + i);
                }
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        });

        // 每秒一个事务，每个事务发2条消息，10个事务，20条消息
        Executors.newSingleThreadExecutor().execute(() -> {
            Producer<String, String> producer = genTxProducer("tx-producer-1");
            producer.initTransactions();

            for (int i = 2000; i < 2020; i += 2) {
                try {
                    producer.beginTransaction();

                    producer.send(new ProducerRecord<>(testTopic, "msg-" + i));
                    log.info("[tx-producer-1]sent tx msg-" + i);
                    producer.send(new ProducerRecord<>(testTopic, "msg-" + (i + 1)));
                    log.info("[tx-producer-1]sent tx msg-" + (i + 1));

                    TimeUnit.SECONDS.sleep(1);
                    producer.commitTransaction();
                } catch (ProducerFencedException | OutOfOrderSequenceException | AuthorizationException e) {
                    // We can't recover from these exceptions, so our only option is to close the producer and exit.
                    producer.close();
                    log.error("tx-producer-1 closed", e);
                } catch (KafkaException e) {
                    // For all other exceptions, just abort the transaction and try again.
                    producer.abortTransaction();
                    log.warn("tx-producer-1 abort tx");
                } catch (InterruptedException e) {
                    throw new RuntimeException(e);
                }
            }
        });

        // 每秒1个事务，每个事务发2条消息
        // 在2个事务后sleep。即，commit了4条消息，未commit的有2条
        Executors.newSingleThreadExecutor().execute(() -> {
            Producer<String, String> producer = genTxProducer("tx-producer-2");
            producer.initTransactions();

            for (int i = 1000; i < 2000; i += 2) {
                try {
                    producer.beginTransaction();
                    producer.send(new ProducerRecord<>(testTopic, "msg-" + i));
                    log.info("[tx-producer-2]sent tx msg-" + i);

                    producer.send(new ProducerRecord<>(testTopic, "msg-" + (i + 1)));
                    log.info("[tx-producer-2]sent tx msg-" + (i + 1));

                    TimeUnit.SECONDS.sleep(1);


                    // 挂起事务
                    if (i == 1004) {
//                        log.warn("tx-producer-2 hanging tx");
                        TimeUnit.SECONDS.sleep(5);
//                        log.warn("tx-producer-2 system exit");
//                        System.exit(-1);
//                        TimeUnit.MINUTES.sleep(60);
                        log.info("tx-producer-1 stop");
                        Thread.currentThread().stop();
                    }

                    producer.commitTransaction();
                } catch (ProducerFencedException | OutOfOrderSequenceException | AuthorizationException e) {
                    // We can't recover from these exceptions, so our only option is to close the producer and exit.
                    producer.close();
                    log.error("tx-producer-2 closed", e);
                } catch (KafkaException e) {
                    // For all other exceptions, just abort the transaction and try again.
                    producer.abortTransaction();
                    log.warn("tx-producer-2 abort tx");
                } catch (InterruptedException e) {
                    throw new RuntimeException(e);
                }
            }
            log.info("thread tx-producer-2 exit");
        });


        // 10 秒后，使用挂起线程的事务id，创建一个producer，强制结束之前挂起的事务
//        Executors.newSingleThreadExecutor().execute(() -> {
//            try {
//                TimeUnit.SECONDS.sleep(10);
//            } catch (InterruptedException e) {
//                throw new RuntimeException(e);
//            }
//            Producer<String, String> producer = genTxProducer("tx-producer-1");
//            log.info("tx-producer-1 init again");
//            producer.initTransactions();
//        });

    }


    Producer<String, String> genTxProducer(String txId) {
        Properties props = new Properties();
        props.put("bootstrap.servers", bootstrapServers);
        props.put("linger.ms", 1);
        props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        props.put("transactional.id", txId);
//        props.put(ProducerConfig.TRANSACTION_TIMEOUT_CONFIG, 10000); // 10 min
        return new KafkaProducer<>(props);
    }

    Producer<String, String> genProducer() {
        Properties props = new Properties();
        props.put("bootstrap.servers", bootstrapServers);
        props.put("linger.ms", 1);
        props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        return new KafkaProducer<>(props);
    }

    Consumer<String, String> genRuncConsumer(String gid) {
        Properties props = new Properties();
        props.setProperty("bootstrap.servers", bootstrapServers);
        props.setProperty("group.id", gid);
        props.setProperty("enable.auto.commit", "true");
        props.setProperty("auto.commit.interval.ms", "1000");
        props.setProperty("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
        props.setProperty("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
        return new KafkaConsumer<>(props);
    }

    Consumer<String, String> genRcConsumer(String gid) {
        Properties props = new Properties();
        props.setProperty("bootstrap.servers", bootstrapServers);
        props.setProperty("group.id", gid);
        props.setProperty("enable.auto.commit", "true");
        props.setProperty("auto.commit.interval.ms", "1000");
        props.setProperty("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
        props.setProperty("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
        props.setProperty(ConsumerConfig.ISOLATION_LEVEL_CONFIG, "read_committed");
        return new KafkaConsumer<>(props);
    }

}

```
