---
title: "在consumer producer运行时停止kafka服务端会怎样"
date: 2022-09-18
tags: ["kafka"]
categories: ["kafka"]
---

## 结论

服务端停止时，客户端程序会报错；

服务端启动后，客户端程序能继续运行。也就是，消费者线程并未异常退出。

## 实验步骤

（1）停止后，consumer和producer会报错。

消费者：

```plaintext

  .   ____          _            __ _ _
 /\\ / ___'_ __ _ _(_)_ __  __ _ \ \ \ \
( ( )\___ | '_ | '_| | '_ \/ _` | \ \ \ \
 \\/  ___)| |_)| | | | | || (_| |  ) ) ) )
  '  |____| .__|_| |_|_| |_\__, | / / / /
 =========|_|==============|___/=/_/_/_/
 :: Spring Boot ::                (v2.6.4)

2022-09-18 16:54:59.676  INFO 16572 --- [           main] cn.whu.wy.kafkamate.MateApp              : Starting MateApp using Java 11.0.10 on R7-4750G with PID 16572 (D:\IdeaProjects\kafka-mate\build\classes\java\main started by whuwa in D:\IdeaProjects\kafka-mate)
2022-09-18 16:54:59.678  INFO 16572 --- [           main] cn.whu.wy.kafkamate.MateApp              : No active profile set, falling back to 1 default profile: "default"
2022-09-18 16:55:00.245  INFO 16572 --- [           main] o.s.b.w.embedded.tomcat.TomcatWebServer  : Tomcat initialized with port(s): 8080 (http)
2022-09-18 16:55:00.251  INFO 16572 --- [           main] o.apache.catalina.core.StandardService   : Starting service [Tomcat]
2022-09-18 16:55:00.252  INFO 16572 --- [           main] org.apache.catalina.core.StandardEngine  : Starting Servlet engine: [Apache Tomcat/9.0.58]
2022-09-18 16:55:00.315  INFO 16572 --- [           main] o.a.c.c.C.[Tomcat].[localhost].[/]       : Initializing Spring embedded WebApplicationContext
2022-09-18 16:55:00.316  INFO 16572 --- [           main] w.s.c.ServletWebServerApplicationContext : Root WebApplicationContext: initialization completed in 606 ms
2022-09-18 16:55:00.828  INFO 16572 --- [           main] o.s.b.w.embedded.tomcat.TomcatWebServer  : Tomcat started on port(s): 8080 (http) with context path ''
2022-09-18 16:55:00.835  INFO 16572 --- [           main] cn.whu.wy.kafkamate.MateApp              : Started MateApp in 1.393 seconds (JVM running for 1.933)
2022-09-18 16:55:41.079  INFO 16572 --- [pool-1-thread-1] cn.whu.wy.kafkamate.core.KafkaMate       : receive: msg-1
2022-09-18 16:55:41.080  INFO 16572 --- [pool-1-thread-1] cn.whu.wy.kafkamate.core.KafkaMate       : receive: msg-2
2022-09-18 16:56:06.961  WARN 16572 --- [| adminclient-1] org.apache.kafka.clients.NetworkClient   : [AdminClient clientId=adminclient-1] Connection to node 0 (ship/192.168.191.128:9092) could not be established. Broker may not be available.
2022-09-18 16:56:07.088  WARN 16572 --- [pool-1-thread-1] org.apache.kafka.clients.NetworkClient   : [Consumer clientId=consumer-test-g-1-1, groupId=test-g-1] Connection to node 0 (ship/192.168.191.128:9092) could not be established. Broker may not be available.
2022-09-18 16:56:09.126  WARN 16572 --- [| adminclient-1] org.apache.kafka.clients.NetworkClient   : [AdminClient clientId=adminclient-1] Connection to node 0 (ship/192.168.191.128:9092) could not be established. Broker may not be available.
2022-09-18 16:56:09.233  WARN 16572 --- [pool-1-thread-1] org.apache.kafka.clients.NetworkClient   : [Consumer clientId=consumer-test-g-1-1, groupId=test-g-1] Connection to node 0 (ship/192.168.191.128:9092) could not be established. Broker may not be available.
2022-09-18 16:56:11.279  WARN 16572 --- [| adminclient-1] org.apache.kafka.clients.NetworkClient   : [AdminClient clientId=adminclient-1] Connection to node 0 (ship/192.168.191.128:9092) could not be established. Broker may not be available.
2022-09-18 16:56:11.452  WARN 16572 --- [pool-1-thread-1] org.apache.kafka.clients.NetworkClient   : [Consumer clientId=consumer-test-g-1-1, groupId=test-g-1] Connection to node 0 (ship/192.168.191.128:9092) could not be established. Broker may not be available.
2022-09-18 16:56:13.544  WARN 16572 --- [| adminclient-1] org.apache.kafka.clients.NetworkClient   : [AdminClient clientId=adminclient-1] Connection to node 0 (ship/192.168.191.128:9092) could not be established. Broker may not be available.
2022-09-18 16:56:14.026  WARN 16572 --- [pool-1-thread-1] org.apache.kafka.clients.NetworkClient   : [Consumer clientId=consumer-test-g-1-1, groupId=test-g-1] Connection to node 0 (ship/192.168.191.128:9092) could not be established. Broker may not be available.
2022-09-18 16:56:16.030  WARN 16572 --- [| adminclient-1] org.apache.kafka.clients.NetworkClient   : [AdminClient clientId=adminclient-1] Connection to node 0 (ship/192.168.191.128:9092) could not be established. Broker may not be available.
2022-09-18 16:56:16.795  WARN 16572 --- [pool-1-thread-1] org.apache.kafka.clients.NetworkClient   : [Consumer clientId=consumer-test-g-1-1, groupId=test-g-1] Connection to node 0 (ship/192.168.191.128:9092) could not be established. Broker may not be available.
2022-09-18 16:56:19.061  WARN 16572 --- [| adminclient-1] org.apache.kafka.clients.NetworkClient   : [AdminClient clientId=adminclient-1] Connection to node 0 (ship/192.168.191.128:9092) could not be established. Broker may not be available.
2022-09-18 16:56:19.947  WARN 16572 --- [pool-1-thread-1] org.apache.kafka.clients.NetworkClient   : [Consumer clientId=consumer-test-g-1-1, groupId=test-g-1] Connection to node 0 (ship/192.168.191.128:9092) could not be established. Broker may not be available.
2022-09-18 16:56:21.983  WARN 16572 --- [| adminclient-1] org.apache.kafka.clients.NetworkClient   : [AdminClient clientId=adminclient-1] Connection to node 0 (ship/192.168.191.128:9092) could not be established. Broker may not be available.
2022-09-18 16:56:23.043  WARN 16572 --- [pool-1-thread-1] org.apache.kafka.clients.NetworkClient   : [Consumer clientId=consumer-test-g-1-1, groupId=test-g-1] Connection to node 0 (ship/192.168.191.128:9092) could not be established. Broker may not be available.
2022-09-18 16:56:25.229  WARN 16572 --- [| adminclient-1] org.apache.kafka.clients.NetworkClient   : [AdminClient clientId=adminclient-1] Connection to node 0 (ship/192.168.191.128:9092) could not be established. Broker may not be available.
2022-09-18 16:56:26.118  WARN 16572 --- [pool-1-thread-1] org.apache.kafka.clients.NetworkClient   : [Consumer clientId=consumer-test-g-1-1, groupId=test-g-1] Connection to node 0 (ship/192.168.191.128:9092) could not be established. Broker may not be available.
2022-09-18 16:56:28.152  WARN 16572 --- [| adminclient-1] org.apache.kafka.clients.NetworkClient   : [AdminClient clientId=adminclient-1] Connection to node 0 (ship/192.168.191.128:9092) could not be established. Broker may not be available.
2022-09-18 16:56:29.008  WARN 16572 --- [pool-1-thread-1] org.apache.kafka.clients.NetworkClient   : [Consumer clientId=consumer-test-g-1-1, groupId=test-g-1] Connection to node 0 (ship/192.168.191.128:9092) could not be established. Broker may not be available.
2022-09-18 16:56:31.835  WARN 16572 --- [pool-1-thread-1] org.apache.kafka.clients.NetworkClient   : [Consumer clientId=consumer-test-g-1-1, groupId=test-g-1] Error while fetching metadata with correlation id 119 : {test=UNKNOWN_TOPIC_OR_PARTITION}
2022-09-18 16:56:31.906  WARN 16572 --- [pool-1-thread-1] o.a.k.c.consumer.internals.Fetcher       : [Consumer clientId=consumer-test-g-1-1, groupId=test-g-1] Received unknown topic ID error in fetch for partition test-0
2022-09-18 16:56:31.973  WARN 16572 --- [pool-1-thread-1] org.apache.kafka.clients.NetworkClient   : [Consumer clientId=consumer-test-g-1-1, groupId=test-g-1] Error while fetching metadata with correlation id 121 : {test=UNKNOWN_TOPIC_OR_PARTITION}
2022-09-18 16:56:32.085  WARN 16572 --- [pool-1-thread-1] org.apache.kafka.clients.NetworkClient   : [Consumer clientId=consumer-test-g-1-1, groupId=test-g-1] Error while fetching metadata with correlation id 123 : {test=UNKNOWN_TOPIC_OR_PARTITION}
2022-09-18 16:56:32.195  WARN 16572 --- [pool-1-thread-1] org.apache.kafka.clients.NetworkClient   : [Consumer clientId=consumer-test-g-1-1, groupId=test-g-1] Error while fetching metadata with correlation id 125 : {test=UNKNOWN_TOPIC_OR_PARTITION}
2022-09-18 16:56:32.306  WARN 16572 --- [pool-1-thread-1] org.apache.kafka.clients.NetworkClient   : [Consumer clientId=consumer-test-g-1-1, groupId=test-g-1] Error while fetching metadata with correlation id 127 : {test=UNKNOWN_TOPIC_OR_PARTITION}
2022-09-18 16:56:32.414  WARN 16572 --- [pool-1-thread-1] org.apache.kafka.clients.NetworkClient   : [Consumer clientId=consumer-test-g-1-1, groupId=test-g-1] Error while fetching metadata with correlation id 129 : {test=UNKNOWN_TOPIC_OR_PARTITION}
2022-09-18 16:56:32.523  WARN 16572 --- [pool-1-thread-1] org.apache.kafka.clients.NetworkClient   : [Consumer clientId=consumer-test-g-1-1, groupId=test-g-1] Error while fetching metadata with correlation id 131 : {test=UNKNOWN_TOPIC_OR_PARTITION}
2022-09-18 16:56:32.650  WARN 16572 --- [pool-1-thread-1] o.a.k.c.c.internals.ConsumerCoordinator  : [Consumer clientId=consumer-test-g-1-1, groupId=test-g-1] Offset commit failed on partition test-0 at offset 3: The coordinator is loading and hence can't process requests.

```

生产者

```plaintext
wy@ship:~/dev/kafka-mate/scripts$ ./produce-to.sh test
>msg-1
>msg-2
>[2022-09-18 08:56:05,745] WARN [Producer clientId=console-producer] Connection to node 0 (ship/127.0.1.1:9092) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:05,845] WARN [Producer clientId=console-producer] Connection to node 0 (ship/127.0.1.1:9092) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:06,050] WARN [Producer clientId=console-producer] Connection to node 0 (ship/127.0.1.1:9092) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:06,560] WARN [Producer clientId=console-producer] Connection to node 0 (ship/127.0.1.1:9092) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:07,379] WARN [Producer clientId=console-producer] Connection to node 0 (ship/127.0.1.1:9092) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:08,350] WARN [Producer clientId=console-producer] Connection to node 0 (ship/127.0.1.1:9092) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:09,219] WARN [Producer clientId=console-producer] Connection to node 0 (ship/127.0.1.1:9092) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:10,244] WARN [Producer clientId=console-producer] Connection to node 0 (ship/127.0.1.1:9092) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:11,111] WARN [Producer clientId=console-producer] Connection to node 0 (ship/127.0.1.1:9092) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:12,029] WARN [Producer clientId=console-producer] Connection to node 0 (ship/127.0.1.1:9092) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:12,998] WARN [Producer clientId=console-producer] Connection to node 0 (ship/127.0.1.1:9092) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:13,865] WARN [Producer clientId=console-producer] Connection to node 0 (ship/127.0.1.1:9092) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:14,841] WARN [Producer clientId=console-producer] Connection to node 0 (ship/127.0.1.1:9092) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:15,866] WARN [Producer clientId=console-producer] Connection to node 0 (ship/127.0.1.1:9092) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:17,038] WARN [Producer clientId=console-producer] Connection to node 0 (ship/127.0.1.1:9092) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:18,010] WARN [Producer clientId=console-producer] Connection to node 0 (ship/127.0.1.1:9092) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:18,829] WARN [Producer clientId=console-producer] Connection to node 0 (ship/127.0.1.1:9092) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:19,695] WARN [Producer clientId=console-producer] Connection to node 0 (ship/127.0.1.1:9092) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:20,918] WARN [Producer clientId=console-producer] Connection to node 0 (ship/127.0.1.1:9092) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:21,888] WARN [Producer clientId=console-producer] Connection to node 0 (ship/127.0.1.1:9092) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:22,861] WARN [Producer clientId=console-producer] Connection to node 0 (ship/127.0.1.1:9092) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:23,775] WARN [Producer clientId=console-producer] Connection to node 0 (ship/127.0.1.1:9092) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:24,691] WARN [Producer clientId=console-producer] Connection to node 0 (ship/127.0.1.1:9092) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:25,605] WARN [Producer clientId=console-producer] Connection to node 0 (ship/127.0.1.1:9092) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:26,771] WARN [Producer clientId=console-producer] Connection to node 0 (ship/127.0.1.1:9092) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:27,888] WARN [Producer clientId=console-producer] Connection to node 0 (ship/127.0.1.1:9092) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:28,910] WARN [Producer clientId=console-producer] Connection to node 0 (ship/127.0.1.1:9092) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:30,080] WARN [Producer clientId=console-producer] Connection to node 0 (ship/127.0.1.1:9092) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:31,247] WARN [Producer clientId=console-producer] Connection to node 0 (ship/127.0.1.1:9092) could not be established. Broker may not be available. (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:32,537] WARN [Producer clientId=console-producer] Error while fetching metadata with correlation id 10 : {test=UNKNOWN_TOPIC_OR_PARTITION} (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:32,689] WARN [Producer clientId=console-producer] Error while fetching metadata with correlation id 11 : {test=UNKNOWN_TOPIC_OR_PARTITION} (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:32,793] WARN [Producer clientId=console-producer] Error while fetching metadata with correlation id 12 : {test=UNKNOWN_TOPIC_OR_PARTITION} (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:32,899] WARN [Producer clientId=console-producer] Error while fetching metadata with correlation id 13 : {test=UNKNOWN_TOPIC_OR_PARTITION} (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:33,004] WARN [Producer clientId=console-producer] Error while fetching metadata with correlation id 14 : {test=UNKNOWN_TOPIC_OR_PARTITION} (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:33,108] WARN [Producer clientId=console-producer] Error while fetching metadata with correlation id 15 : {test=UNKNOWN_TOPIC_OR_PARTITION} (org.apache.kafka.clients.NetworkClient)
[2022-09-18 08:56:33,213] WARN [Producer clientId=console-producer] Error while fetching metadata with correlation id 16 : {test=UNKNOWN_TOPIC_OR_PARTITION} (org.apache.kafka.clients.NetworkClient)
```


（2）再次启动服务端后，验证consumer和produce微软手否能继续运行：

生产者：

```plaintext
>msg-3
>msg-4
>
```

消费者：

```plaintext
2022-09-18 16:56:52.578  INFO 16572 --- [pool-1-thread-1] cn.whu.wy.kafkamate.core.KafkaMate       : receive: msg-3
2022-09-18 16:56:59.688  INFO 16572 --- [pool-1-thread-1] cn.whu.wy.kafkamate.core.KafkaMate       : receive: msg-4
```



## 附：测试代码

```java
@Service
@Slf4j
public class KafkaMate {

    private static final String SERVER = "192.168.191.128:9092";

    @PostConstruct
    public void init() {
        Executors.newSingleThreadExecutor().execute(this::consume);
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

    void consume() {
        try (KafkaConsumer<String, String> consumer = new KafkaConsumer<>(consumerProperties())) {
            consumer.subscribe(Collections.singleton("test"));
            while (true) {
                ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(1000));
                Iterator<ConsumerRecord<String, String>> iterator = records.iterator();
                while (iterator.hasNext()) {
                    log.info("receive: {}", iterator.next().value());
                }
            }
        }
    }

}
```