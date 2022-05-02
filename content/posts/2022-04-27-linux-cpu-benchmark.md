---
title: "Linux CPU 性能测试"
date: 2022-04-27
tags: ["sysbench", "7z"]
categories: ["linux","性能测试"]
---

## sysbench

Sysbench is mainly intended for doing database benchmarking. However it includes options to test CPU, memory and file throughput as well.

### 安装

```bash
sudo apt install sysbench
```

### 使用

```bash
ubuntu@instance:~$ sysbench cpu --threads=3 run
sysbench 1.0.18 (using system LuaJIT 2.1.0-beta3)

Running the test with following options:
Number of threads: 3
Initializing random number generator from current time


Prime numbers limit: 10000

Initializing worker threads...

Threads started!

CPU speed:
    events per second: 10519.03

General statistics:
    total time:                          10.0003s
    total number of events:              105208

Latency (ms):
         min:                                    0.28
         avg:                                    0.28
         max:                                    5.22
         95th percentile:                        0.29
         sum:                                29976.02

Threads fairness:
    events (avg/stddev):           35069.3333/81.99
    execution time (avg/stddev):   9.9920/0.00
```

events per second，值越大，性能越强。

上面是一个Oracle主机的测试结果，3个OCPU，每秒事件10519。单个OCPU每秒事件数为3484。i7-7700 CPU，单核每秒事件数1438，8核每秒事件数8469。可见Oracle主机的OCPU性能很强，单核性能是 i7-7700 的2.4倍。

## 7z

7z是个压缩/解压工具，压缩/解压天然吃CPU，用来测试性能顺理成章。而且官方还给出了一些CPU型号的测试结果排名：[7-Zip LZMA Benchmark (7-cpu.com)](https://www.7-cpu.com/)

### 安装

```bash
sudo apt install p7zip-full
```

### 使用

语法：

```plaintext
7z b [number_of_iterations] [-mmt{N}] [-md{N}] [-mm={Method}]
```

* number_of_iterations 迭代次数，测试多少轮，可用于检查内存错误
* mmt 线程数

举例：

```bash
# 单线程
$ 7z b -mmt1
# 多线程
$ 7z b
```

结果说明：

```plaintext
ubuntu@instance:~$ 7z b

7-Zip [64] 16.02 : Copyright (c) 1999-2016 Igor Pavlov : 2016-05-21
p7zip Version 16.02 (locale=C.UTF-8,Utf16=on,HugeFiles=on,64 bits,3 CPUs LE)

LE
CPU Freq: - - - - - - 512000000 - -

RAM size:   17954 MB,  # CPU hardware threads:   3
RAM usage:    441 MB,  # Benchmark threads:      3

                       Compressing  |                  Decompressing
Dict     Speed Usage    R/U Rating  |      Speed Usage    R/U Rating
         KiB/s     %   MIPS   MIPS  |      KiB/s     %   MIPS   MIPS

22:       8642   175   4813   8407  |      98748   199   4227   8431
23:       8612   187   4695   8775  |      97477   200   4228   8438
24:       8438   196   4622   9073  |      95682   200   4201   8400
25:       8151   198   4694   9307  |      93742   200   4176   8344
----------------------------------  | ------------------------------
Avr:             189   4706   8891  |              200   4208   8403
Tot:             194   4457   8647
```

上面是Orace OCPU的测试结果，单核4706。i7-7700单核3768。

* **Dict**：字典大小，22表示2^21=4MB
* **Usage**：cpu总利用率。我有3个核，这里最多只用到200%，这是因为7z似乎只能使用`2N`个核（来源“When you specify (N*2) threads for test, the program creates N copies of LZMA encoder, and each LZMA encoder instance compresses separated block of test data.”——[7-Zip LZMA Benchmark (7-cpu.com)](https://www.7-cpu.com/)）
* **MIPS：**million instructions per second
* **R/U MIPS**：单核性能。
* **Rating MIPS**：约等于`Usage * (R/U MIPS)`

更多介绍，查看帮助文档。`man 7z`，在最下面会看到：

> HTML Documentation  
>        /usr/share/doc/p7zip-full/DOC/MANUAL/start.htm
>

用vim或者浏览器打开此页面进入帮助文档主页。或直接打开以下页面查看benchmark相关内容：

```bash
chrome /usr/share/doc/p7zip/DOC/MANUAL/cmdline/commands/bench.htm
```

## 数值运算

比如写个python脚本：

```python
import math
import time

t0 = time.time()
for i in range(0, 10000000):
    math.pow(47,39)
print(time.time() - t0)
```

将该脚本在不同的CPU上执行，通过对比运行时间，估计待测CPU的性能。


