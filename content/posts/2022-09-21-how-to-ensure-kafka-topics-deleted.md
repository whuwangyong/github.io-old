---
title: "如何确保kafka topic已经删除"
date: 2022-09-21
tags: ["kafka"]
categories: ["kafka"]
---

## 问题描述

> TopicExistsException: Topic 'xxx' is marked for deletion.

在写kafka工具时，有两个方法：批量创建topic和批量删除topic。

运维操作一般是，批量删除一堆topic，然后再重建删除的那些topic。在创建时，可能会遇到如下错误：

```plaintext
2022-09-19 08:37:55.150  INFO 20376 --- [nio-8080-exec-4] c.w.w.k.service.TopicManagerImpl         : input topics num: 100, deleted topics num: 100
java.util.concurrent.ExecutionException: org.apache.kafka.common.errors.TopicExistsException: Topic 'test-16' is marked for deletion.
	at java.base/java.util.concurrent.CompletableFuture.reportGet(CompletableFuture.java:395)
	at java.base/java.util.concurrent.CompletableFuture.get(CompletableFuture.java:1999)
	at org.apache.kafka.common.internals.KafkaFutureImpl.get(KafkaFutureImpl.java:165)
	at cn.whu.wy.kafkamate.service.TopicManagerImpl.createTopics(TopicManagerImpl.java:56)
	at cn.whu.wy.kafkamate.restapi.TopicController.createTopics(TopicController.java:24)
Caused by: org.apache.kafka.common.errors.TopicExistsException: Topic 'test-16' is marked for deletion.

```

这是因为，AdminClient仅仅是将删除topic的请求发送到服务端就返回了，服务端执行删除topic是一个异步的复杂的过程。在服务端还没真正删除topic时，再次创建同名的topic，就会遇到上述错误。

StackOverflow上有相关问题，但暂无答案：

[java - How can I make sure that a Kafka topic has been deleted? - Stack Overflow](https://stackoverflow.com/questions/73109687/how-can-i-make-sure-that-a-kafka-topic-has-been-deleted)

这篇文章讲了topic的删除过程：

[16 | TopicDeletionManager： Topic是怎么被删除的？ (geekbang.org)](https://time.geekbang.org/column/article/241066)


## 一些尝试

### 1 在批量删除topic之后再创建一个foo topic，试图触发kafka的删除机制

```java
public Object deleteTopics(Set<String> topics) throws ExecutionException, InterruptedException {
    Object o = doDeleteTopics(topics);
    createFooTopic4TriggeringDelete();
    return o;
}

/**
 * 由于kafka删除topic不会立即生效，只是标记为删除。
 * 该方法创建一个临时topic，然后将其删除，试图快速触发kafka的删除机制
 */
private void createFooTopic4TriggeringDelete() throws ExecutionException, InterruptedException {
    NewTopic foo = new NewTopic("foo_" + System.currentTimeMillis(), 1, (short) 1);
    adminClient.createTopics(Collections.singleton(foo)).all().get();
    adminClient.deleteTopics(Collections.singleton(foo.name())).all().get();
}
```

该方法有一定效果，或许是因为`createFooTopic4TriggeringDelete()`方法消耗了一些时间，topic在这段时间内正好被彻底删除了。

测试逻辑：每次先删除500个topic，然后再创建500个。

测试结果：可以坚持到第4轮。

```plaintext
delete topics: input size=500, actually deleted size=376, use 2256 ms.
create topics: input size=500, actually created size=500, use 7956 ms.

delete topics: input size=500, actually deleted size=500, use 1707 ms.
create topics: input size=500, actually created size=500, use 8164 ms.

delete topics: input size=500, actually deleted size=500, use 2131 ms.
create topics: input size=500, actually created size=500, use 8641 ms.

delete topics: input size=500, actually deleted size=500, use 1708 ms.
create topics:
java.util.concurrent.ExecutionException: org.apache.kafka.common.errors.TopicExistsException: Topic 'test-217' is marked for deletion.

delete topics: input size=500, actually deleted size=351, use 1705 ms.
```

未使用该方法时，在第1轮就报错了：

```plaintext
delete topics: input size=500, actually deleted size=500, use 2464 ms.
create topics: 
java.util.concurrent.ExecutionException: org.apache.kafka.common.errors.TopicExistsException: Topic 'test-145' is marked for deletion.

```

### 2 创建foo topic + sleep

在前面的基础上，增加sleep 2s。测试发现，重复删除/创建500个topic 30轮，未出现异常。

```java
public Object deleteTopics(Set<String> topics) throws ExecutionException, InterruptedException {
    Object o = doDeleteTopics(topics);
    createFooTopic4TriggeringDelete();
    TimeUnit.SECONDS.sleep(2);
    return o;
}
```


### 3 使用topic uuid进行删除

毫无效果。

```java
private Object doDeleteTopics(Set<String> topics) throws ExecutionException, InterruptedException {
    long start = System.currentTimeMillis();
    Collection<TopicListing> existTopics = listTopics(false);
    List<Uuid> topicsToDelete = existTopics.stream()
            .filter(t -> topics.contains(t.name()))
            .map(TopicListing::topicId)
            .collect(Collectors.toList());
    adminClient.deleteTopics(TopicCollection.ofTopicIds(topicsToDelete)).all().get();
    long now = System.currentTimeMillis();
    String info = String.format("delete topics: input size=%d, actually deleted size=%d, use %d ms.",
            topics.size(), topicsToDelete.size(), now - start);
    log.info(info);
    return info;
}
```

## 结论

我看了前文提到的TopicDeletionManager，这是服务端的类，scala语言写的。在客户端这边，我没有找到与这个类相关的API。我期望的是客户端这边有一个回调方法，如onTopicDeleted()，当服务端确保topic删除后，可以回调此方法。可惜没找到。

如有大佬知道怎么做，还请指教。