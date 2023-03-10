---
title: "【常识系列】HashMap的查询性能（百万级每秒）"
date: 2023-03-10
tags: ["hashmap","性能"]
categories: ["常识系列"]
---

> **常识系列**旨在让程序员对一些常见的计算机知识有一个数值上的理解，比如，mysql的一个insert耗时是多少，ssd的顺序写速度是多少，HashMap每秒可以做多少次查询？有了这些常识，在设计系统或者算法的时候，能更准确的预估其上限和下限。
>
> [点此](https://whuwangyong.github.io/categories/%E5%B8%B8%E8%AF%86%E7%B3%BB%E5%88%97/)查看所有该系列的所有文章。

## 测试目的

一个2000万数据的Map，k-v均为String，执行contains测试，每秒可以执行多少次？

## 测试代码

```java
import java.util.Map;
import java.util.HashMap;
import java.util.UUID;

public class M {
	public static void main(String[] args) {
        int size = 2000_0000; // 2千万测试数据，大约需要3.5G内存
        String prefix = UUID.randomUUID().toString();
        Map<String, String> map = new HashMap<>(size);

        for (int i = 0; i < size; i++) {
            map.put(prefix + i, System.currentTimeMillis() + "");
        }

        long start = System.currentTimeMillis();
        long queryTimes = 0;
        long hit = 0;
        long unhit = 0;
        for (int i = 0; i < size * 1.3; i += 47) {
            queryTimes++;
            if (map.containsKey(prefix + i)) {
                hit++;
            } else {
                unhit++;
            }
        }
        long end = System.currentTimeMillis();

        System.out.println("total query times:" + queryTimes);
        System.out.println("hit:" + hit);
        System.out.println("unhit:" + unhit);
        assert queryTimes == hit + unhit;
        System.out.println("query times per second(tps):" + queryTimes / (end - start) * 1000);
    }
}
```

## 测试结果

384万次/秒。

```plaintext
PS C:\Users\2022\Desktop> javac M.java
PS C:\Users\2022\Desktop> java -Xms3g -Xmx4g M
total query times:553192
hit:425532
unhit:127660
query times per second(tps):3841000
```

## 测试环境

```plaintext
PC: MECHREVO WUJIE 14 笔记本
OS: Windows 11 x64
CPU: i7-12700H
RAM: 16 GB (英睿达 DDR4 3200MHz 8GB x 2)
SSD: Intel SSD PEKNW512G8
```

在其他机器上也进行了测试，每秒查询次数在200万~400万。