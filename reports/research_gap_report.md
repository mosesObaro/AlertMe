# Research Gap Analysis Report

*Generated: 2026-10-02*

**Papers analyzed:** 10  
**Research problems identified:** 10  
**Research-gap clusters:** 1  
**Candidate research directions:** 8  

---

## Research Problems

### Investigating (8)

#### Deploying deep learning models on resource-constrained edge devices faces acute memory and latency bottlenecks
- **Research Area:** Edge Computing
- **Cluster:** 
- **Frequency:** 1
- **Status:** investigating
- **Known Limitations:**
  - However, the limitation is that the framework does not consider battery energy degradation during sustained bursty traffic
- **Unresolved Questions:**
  - Future work will extend the optimization to energy harvesting environments and evaluate asynchronous multi-device cooperative inference
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** high

#### However, the fundamental bottleneck lies in communication overhead and extreme client device heterogeneity where stragglers degrade global model convergence speed
- **Research Area:** Edge AI
- **Cluster:** 
- **Frequency:** 1
- **Status:** investigating
- **Known Limitations:**
  - A major limitation of this work is the assumption of independent and identically distributed channel states between training rounds
- **Unresolved Questions:**
  - Future research must address non-stationary communication channels and Byzantine client poisoning resilience
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** high

#### However, the challenge of activation memory footprint during backward passes remains unresolved for sub-megabyte devices
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** investigating
- **Known Limitations:**
  - Nevertheless, a critical limitation is that computational overhead increases total training energy consumption by 22%, making it unsuitable for battery-less ambient IoT nodes
- **Unresolved Questions:**
  - Future work plans to explore intermittent computing integration and hardware-aware sparse backpropagation
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** high

#### However, decentralized task scheduling across non-cooperative edge servers and base stations suffers from severe coordination overhead and partial observability bottlenecks
- **Research Area:** Edge Computing
- **Cluster:** Edge-cloud computing & Edge computing
- **Frequency:** 1
- **Status:** investigating
- **Known Limitations:**
  - However, a key limitation is the vulnerability to non-stationary policies when edge nodes join or leave dynamically in ad-hoc mobile networks
- **Unresolved Questions:**
  - Future work will investigate zero-shot transfer learning across heterogeneous topologies and formal safety constraints using control barrier functions
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** high

#### However, naive asynchronous federated updates suffer from stale gradient divergence and catastrophic forgetting on non-IID client partitions
- **Research Area:** Edge Computing
- **Cluster:** 
- **Frequency:** 1
- **Status:** investigating
- **Known Limitations:**
  - The primary limitation of this work is that it assumes trusted edge aggregation servers and does not provide formal differential privacy guarantees
- **Unresolved Questions:**
  - Future work will integrate homomorphic encryption and investigate decentralized peer-to-peer gossip aggregation without parameter servers
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** high

#### Prolonging device operational lifetime is the paramount challenge for battery-powered IoT and wearable edge devices running continuous neural inference
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** investigating
- **Known Limitations:**
  - However, the limitation is that the framework requires exact knowledge of battery internal resistance and temperature curves, which drift over battery aging cycles
- **Unresolved Questions:**
  - Future work will explore online reinforcement learning for battery state-of-health estimation and adaptive policy tuning
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** high

#### However, cold start initialization latencies in containerized runtimes exceed 500 ms on edge nodes with limited I/O throughput, violating interactive SLA requirements
- **Research Area:** Edge Computing
- **Cluster:** Edge-cloud computing & Edge computing
- **Frequency:** 1
- **Status:** investigating
- **Known Limitations:**
  - The core limitation is memory thrashing when total pre-warmed snapshot sizes exceed available edge RAM during bursty traffic spikes
- **Unresolved Questions:**
  - Future research will explore hierarchical snapshot tiering to NVMe storage and zero-copy shared memory IPC between FaaS invocations
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** high

#### The primary limitation is that the token recovery cache requires dedicated SRAM buffers that scale linearly with video resolution, creating bottlenecks on Ultra-HD streams
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** investigating
- **Known Limitations:**
  - The primary limitation is that the token recovery cache requires dedicated SRAM buffers that scale linearly with video resolution, creating bottlenecks on Ultra-HD streams
- **Unresolved Questions:**
  - Future work will investigate sparse linear attention mechanisms and hardware-software co-design with emerging NPU architectures
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** high

### New (2)

#### The limitation is that computing pairwise task similarity matrices introduces an O(N^2) communication bottleneck as the number of IIoT devices scales to thousands
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Known Limitations:**
  - The limitation is that computing pairwise task similarity matrices introduces an O(N^2) communication bottleneck as the number of IIoT devices scales to thousands
- **Unresolved Questions:**
  - Future work will explore hierarchical cluster representatives and decentralized discovery of cluster affiliations without central coordination
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** high

#### However, classical Paxos and Raft protocols suffer catastrophic availability loss during wide-area network partitions and frequent edge node churn
- **Research Area:** Edge Computing
- **Cluster:** Edge-cloud computing & Edge computing
- **Frequency:** 1
- **Status:** new
- **Known Limitations:**
  - However, a major limitation is that state convergence under high conflict rates incurs substantial storage overhead from tombstone accumulation
- **Unresolved Questions:**
  - Future work will investigate garbage collection protocols tailored for resource-constrained edge storage and formal verification of CRDT merge safety under Byzantine failures
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** high

---

## Research Gap Clusters

### Edge-cloud computing & Edge computing
- **Research Area:** Edge Computing
- **Problems:** 3
- **Papers:** 3
- **Recurring Limitations:**
  - However, a key limitation is the vulnerability to non-stationary policies when edge nodes join or leave dynamically in ad-hoc mobile networks
  - The core limitation is memory thrashing when total pre-warmed snapshot sizes exceed available edge RAM during bursty traffic spikes
  - However, a major limitation is that state convergence under high conflict rates incurs substantial storage overhead from tombstone accumulation
- **Open Questions:**
  - Future work will investigate zero-shot transfer learning across heterogeneous topologies and formal safety constraints using control barrier functions
  - Future research will explore hierarchical snapshot tiering to NVMe storage and zero-copy shared memory IPC between FaaS invocations
  - Future work will investigate garbage collection protocols tailored for resource-constrained edge storage and formal verification of CRDT merge safety under Byzantine failures

---

## Candidate Research Directions

### Deploying deep learning models on resource-constrained edge devices faces acute memory and latency bottlenecks
- **Gap:** Gap in Edge Computing: existing approaches (current methods) leave unresolved: However, the limitation is that the framework does not consider battery energy degradation during sustained bursty traffic
- **Research Questions:**
  1. How can extend the optimization to energy harvesting environments and evaluate asynchronous multi-device cooperative inference be effectively addressed in Edge Computing?
  1. What algorithmic or architectural approaches can overcome the limitation of limitation is that the framework does not consider battery energy degradation during sustained bursty traffic in Edge Computing?
- **Potential Contribution:** A novel theoretical and algorithmic framework addressing limitation is that the framework does not consider battery energy degradation during sustained bursty traffic in resource-constrained Edge Computing systems.
- **Possible Methodology:** Formulate the multi-objective optimization problem, combining Lyapunov drift-plus-penalty optimization with deep reinforcement learning, and validate on real-world Edge Computing testbeds.
- **Evidence Supported:** Yes

### However, the fundamental bottleneck lies in communication overhead and extreme client device heterogeneity where stragglers degrade global model convergence speed
- **Gap:** Gap in Edge AI: existing approaches (current methods) leave unresolved: A major limitation of this work is the assumption of independent and identically distributed channel states between training rounds
- **Research Questions:**
  1. How can address non-stationary communication channels and Byzantine client poisoning resilience be effectively addressed in Edge AI?
  1. What algorithmic or architectural approaches can overcome the limitation of the assumption of independent and identically distributed channel states between training rounds in Edge AI?
- **Potential Contribution:** A novel theoretical and algorithmic framework addressing the assumption of independent and identically distributed channel states between training rounds in resource-constrained Edge AI systems.
- **Possible Methodology:** Formulate the multi-objective optimization problem, combining Lyapunov drift-plus-penalty optimization with deep reinforcement learning, and validate on real-world Edge AI testbeds.
- **Evidence Supported:** Yes

### However, the challenge of activation memory footprint during backward passes remains unresolved for sub-megabyte devices
- **Gap:** Gap in AI for Resource-Constrained Systems: existing approaches (current methods) leave unresolved: Nevertheless, a critical limitation is that computational overhead increases total training energy consumption by 22%, making it unsuitable for battery-less ambient IoT nodes
- **Research Questions:**
  1. How can explore intermittent computing integration and hardware-aware sparse backpropagation be effectively addressed in AI for Resource-Constrained Systems?
  1. What algorithmic or architectural approaches can overcome the limitation of a critical limitation is that computational overhead increases total training energy consumption by 22%, making it unsuitable for battery-less ambient IoT nodes in AI for Resource-Constrained Systems?
- **Potential Contribution:** A novel theoretical and algorithmic framework addressing a critical limitation is that computational overhead increases total training energy consumption by 22%, making it unsuitable for battery-less ambient IoT nodes in resource-constrained AI for Resource-Constrained Systems systems.
- **Possible Methodology:** Formulate the multi-objective optimization problem, combining Lyapunov drift-plus-penalty optimization with deep reinforcement learning, and validate on real-world AI for Resource-Constrained Systems testbeds.
- **Evidence Supported:** Yes

### However, decentralized task scheduling across non-cooperative edge servers and base stations suffers from severe coordination overhead and partial observability bottlenecks
- **Gap:** Gap in Edge Computing: existing approaches (current methods) leave unresolved: However, a key limitation is the vulnerability to non-stationary policies when edge nodes join or leave dynamically in ad-hoc mobile networks
- **Research Questions:**
  1. How can investigate zero-shot transfer learning across heterogeneous topologies and formal safety constraints using control barrier functions be effectively addressed in Edge Computing?
  1. What algorithmic or architectural approaches can overcome the limitation of a key limitation is the vulnerability to non-stationary policies when edge nodes join or leave dynamically in ad-hoc mobile networks in Edge Computing?
- **Potential Contribution:** A novel theoretical and algorithmic framework addressing a key limitation is the vulnerability to non-stationary policies when edge nodes join or leave dynamically in ad-hoc mobile networks in resource-constrained Edge Computing systems.
- **Possible Methodology:** Formulate the multi-objective optimization problem, combining Lyapunov drift-plus-penalty optimization with deep reinforcement learning, and validate on real-world Edge Computing testbeds.
- **Evidence Supported:** Yes

### However, naive asynchronous federated updates suffer from stale gradient divergence and catastrophic forgetting on non-IID client partitions
- **Gap:** Gap in Edge Computing: existing approaches (current methods) leave unresolved: The primary limitation of this work is that it assumes trusted edge aggregation servers and does not provide formal differential privacy guarantees
- **Research Questions:**
  1. How can integrate homomorphic encryption and investigate decentralized peer-to-peer gossip aggregation without parameter servers be effectively addressed in Edge Computing?
  1. What algorithmic or architectural approaches can overcome the limitation of the primary limitation of this work is that it assumes trusted edge aggregation servers and does not provide formal differential privacy guarantees in Edge Computing?
- **Potential Contribution:** A novel theoretical and algorithmic framework addressing the primary limitation of this work is that it assumes trusted edge aggregation servers and does not provide formal differential privacy guarantees in resource-constrained Edge Computing systems.
- **Possible Methodology:** Formulate the multi-objective optimization problem, combining Lyapunov drift-plus-penalty optimization with deep reinforcement learning, and validate on real-world Edge Computing testbeds.
- **Evidence Supported:** Yes

### Prolonging device operational lifetime is the paramount challenge for battery-powered IoT and wearable edge devices running continuous neural inference
- **Gap:** Gap in AI for Resource-Constrained Systems: existing approaches (current methods) leave unresolved: However, the limitation is that the framework requires exact knowledge of battery internal resistance and temperature curves, which drift over battery aging cycles
- **Research Questions:**
  1. How can explore online reinforcement learning for battery state-of-health estimation and adaptive policy tuning be effectively addressed in AI for Resource-Constrained Systems?
  1. What algorithmic or architectural approaches can overcome the limitation of limitation is that the framework requires exact knowledge of battery internal resistance and temperature curves, which drift over battery aging cycles in AI for Resource-Constrained Systems?
- **Potential Contribution:** A novel theoretical and algorithmic framework addressing limitation is that the framework requires exact knowledge of battery internal resistance and temperature curves, which drift over battery aging cycles in resource-constrained AI for Resource-Constrained Systems systems.
- **Possible Methodology:** Formulate the multi-objective optimization problem, combining Lyapunov drift-plus-penalty optimization with deep reinforcement learning, and validate on real-world AI for Resource-Constrained Systems testbeds.
- **Evidence Supported:** Yes

### However, cold start initialization latencies in containerized runtimes exceed 500 ms on edge nodes with limited I/O throughput, violating interactive SLA requirements
- **Gap:** Gap in Edge Computing: existing approaches (current methods) leave unresolved: The core limitation is memory thrashing when total pre-warmed snapshot sizes exceed available edge RAM during bursty traffic spikes
- **Research Questions:**
  1. How can explore hierarchical snapshot tiering to NVMe storage and zero-copy shared memory IPC between FaaS invocations be effectively addressed in Edge Computing?
  1. What algorithmic or architectural approaches can overcome the limitation of memory thrashing when total pre-warmed snapshot sizes exceed available edge RAM during bursty traffic spikes in Edge Computing?
- **Potential Contribution:** A novel theoretical and algorithmic framework addressing memory thrashing when total pre-warmed snapshot sizes exceed available edge RAM during bursty traffic spikes in resource-constrained Edge Computing systems.
- **Possible Methodology:** Formulate the multi-objective optimization problem, combining Lyapunov drift-plus-penalty optimization with deep reinforcement learning, and validate on real-world Edge Computing testbeds.
- **Evidence Supported:** Yes

### The primary limitation is that the token recovery cache requires dedicated SRAM buffers that scale linearly with video resolution, creating bottlenecks on Ultra-HD streams
- **Gap:** Gap in AI for Resource-Constrained Systems: existing approaches (current methods) leave unresolved: The primary limitation is that the token recovery cache requires dedicated SRAM buffers that scale linearly with video resolution, creating bottlenecks on Ultra-HD streams
- **Research Questions:**
  1. How can investigate sparse linear attention mechanisms and hardware-software co-design with emerging NPU architectures be effectively addressed in AI for Resource-Constrained Systems?
  1. What algorithmic or architectural approaches can overcome the limitation of the token recovery cache requires dedicated SRAM buffers that scale linearly with video resolution, creating bottlenecks on Ultra-HD streams in AI for Resource-Constrained Systems?
- **Potential Contribution:** A novel theoretical and algorithmic framework addressing the token recovery cache requires dedicated SRAM buffers that scale linearly with video resolution, creating bottlenecks on Ultra-HD streams in resource-constrained AI for Resource-Constrained Systems systems.
- **Possible Methodology:** Formulate the multi-objective optimization problem, combining Lyapunov drift-plus-penalty optimization with deep reinforcement learning, and validate on real-world AI for Resource-Constrained Systems testbeds.
- **Evidence Supported:** Yes
