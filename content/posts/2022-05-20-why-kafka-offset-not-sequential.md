---
title: "kafka offset为什么不连续"
date: 2022-05-20
tags: ["kafka", "kafka offset"]
categories: ["kafka"]
---

## why kafka offset not sequential

* 未使用事务时，至少一次语义，消息重发时，会占用offset
* 使用事务时，每次事务的commit/abort，都会往topic（每个分区？）写一个标志，这个标志会占用offset
* 官方并未提及offset是连续的



## Reference

1. [[Solved] Kafka Streams does not increment offset by 1 when producing to topic - Local Coder](https://localcoder.org/kafka-streams-does-not-increment-offset-by-1-when-producing-to-topic)