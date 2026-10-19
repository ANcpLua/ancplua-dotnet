# Hot-path review

Start from a caller/workload or label the result a source-review hypothesis.
Rank work by measured frequency, allocation or wait cost; syntax hit counts do
not establish severity or a speedup.

| Signal | Check before changing it |
| --- | --- |
| `.Result`, `.Wait()`, blocking I/O in async paths | Synchronization context, pool starvation and ownership of async propagation. Wrapping blocking work in `Task.Run` does not make I/O asynchronous. |
| Repeated LINQ/enumeration, parsing or lookup construction | Whether work can be reused without changing ordering, deferred side effects, exceptions or mutation visibility. |
| String slicing, concatenation, casing, regex | Allocation profile, culture/comparison semantics and regex options/timeouts. Choose span or generated-regex APIs only when their contracts fit. |
| `ValueTask`, pooling or borrowed buffers | Synchronous-completion rate, single-consumption rules, lifetime across awaits and return/disposal ownership. Extra machinery must repay its cost. |
| Read-mostly dictionaries | Actual immutability and construction amortization before choosing frozen collections. |
| Serialization or HTTP hot paths | Reusable options/metadata and client/handler ownership; preserve wire formats, timeouts and cancellation. |

Prefer framework operations that already optimize the workload before custom
unsafe/SIMD code. Check the consumer's actual TFM/API surface. Measure the changed
path with equivalent inputs; retained memory, throughput and tail latency may
trade against one another. Report the tradeoff rather than a blanket style rule.
