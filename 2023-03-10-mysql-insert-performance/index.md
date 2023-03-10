# 【常识系列】MySQL insert 性能（单条1ms）


> **常识系列**旨在让程序员对一些常见的计算机知识有一个数值上的理解，比如，mysql的一个insert耗时是多少，ssd的顺序写速度是多少，HashMap每秒可以做多少次查询？有了这些常识，在设计系统或者算法的时候，能更准确的预估其上限和下限。
>
> [点此](https://whuwangyong.github.io/categories/%E5%B8%B8%E8%AF%86%E7%B3%BB%E5%88%97/)查看所有该系列的所有文章。


## 测试目的

测试mysql单条insert和批量insert的性能。本次测试，没有网络IO，实际性能应该更低。

## 测试代码

见 [whuwangyong/db-test (github.com)](https://github.com/whuwangyong/db-test)

## 测试结果

* 逐条insert 10000条，cost=8969ms，tps=1114/s
* 批量insert 110000条，batchSize=1000，cost=2921，tps=37658/s

一个insert，差不多需要1ms。如果有网络IO，会低于1ms。

## 测试环境

```plaintext
PC: MECHREVO WUJIE 14 笔记本
OS: Windows 11 x64
CPU: i7-12700H
RAM: 16 GB (英睿达 DDR4 3200MHz 8GB x 2)
SSD: Intel SSD PEKNW512G8
```

---

> 作者: [Wang Yong](https://github.com/whuwangyong)  
> URL: https://whuwangyong.github.io/2023-03-10-mysql-insert-performance/  

