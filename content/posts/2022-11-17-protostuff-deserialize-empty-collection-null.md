---
title: "protostuff deserialize empty collection null"
date: 2022-11-17
tags: ["protostuff","反序列化","null"]
categories: ["protostuff"]
---

protostuff反序列化空集合为null。

## 问题描述

有一个class A，含一个集合字段。创建对象时，如果集合字段赋值empty（不是null），那么反序列化后该字段变为null。

```java
public class A {
    List<Object> lo;
    String name;
}

A a = new A();
a.setLo(new ArrarList<>());
a.setName("a");

var b = serialize(a);
var c = deserialize(b);
// c.lo is null
```

## 原因分析

这是因为protostuff默认不序列collection本身，只序列化collection里面的元素。

解决1：

```java
private List<String> foo = new ArrayList<String>();
```

解决2：

You can use this scheme，an empty List after deserialization

```java

IdStrategy strategy = new DefaultIdStrategy(IdStrategy.DEFAULT_FLAGS 
    | IdStrategy.COLLECTION_SCHEMA_ON_REPEATED_FIELDS ,null,0); 
schema = RuntimeSchema.createFrom(originClazz, strategy);

```

解决3：

If you are to purely use this to replace java serialization (no compatibility with protobuf), set the following system properties:

```plaintext
-Dprotostuff.runtime.always_use_sun_reflection_factory=true
-Dprotostuff.runtime.preserve_null_elements=true
-Dprotostuff.runtime.morph_collection_interfaces=true
-Dprotostuff.runtime.morph_map_interfaces=true
-Dprotostuff.runtime.morph_non_final_pojos=true
```


## Reference

1. [Can not correctly deserialize empty List · Issue #219 · protostuff/protostuff (github.com)](https://github.com/protostuff/protostuff/issues/219)
2. [protostuff/RuntimeEnv.java at master · protostuff/protostuff (github.com)](https://github.com/protostuff/protostuff/blob/master/protostuff-runtime/src/main/java/io/protostuff/runtime/RuntimeEnv.java)
3. [Empty ArrayList data member being deserialized back as null (google.com)](https://groups.google.com/g/protostuff/c/tYOdTSUvg_Q/m/eHJr6HwmbmoJ?pli=1)