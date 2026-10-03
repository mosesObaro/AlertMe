# Research Gap Analysis Report

*Generated: 2026-10-03*

**Papers analyzed:** 111  
**Research problems identified:** 111  
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

### New (103)

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

#### However, recent advances in the WebAssembly ecosystem have significantly matured the technology, raising the question of whether it can serve as a viable replacement for containers in cloud-native workloads
- **Research Area:** Edge Computing
- **Cluster:** Edge-cloud computing & Edge computing
- **Frequency:** 1
- **Status:** new
- **Known Limitations:**
  - Because of compatibility limitations, WebAssembly has mainly been applied to Function-as-a-Service (FaaS) and Edge Computing scenarios, where it has attracted growing research interest
  - Simultaneously, we confirm known limitations in CPU-intensive workloads
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** high

#### Straggling clients have been a problem for FL as they introduce delays in aggregating the local models and hence, the convergence of the global model
- **Research Area:** Federated Learning
- **Cluster:** Edge-cloud computing & Edge computing
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### This paper explores FL-as-a-service (FLaaS) in IoT, highlighting its potential for collaborative learning across applications while addressing challenges like security, privacy, and optimizing hierarchical architectures for efficient model convergence and accuracy
- **Research Area:** Federated Learning
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### To tackle these challenges, we propose FedOAG, which employs algorithmic components to automatically satisfy energy constraints via gradient normalization and evenly mix devices' updates through implicit gossiping
- **Research Area:** Federated Learning
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### However, non-IID task and environment distributions can induce representation drift and mutually incompatible robot-policy updates, making naive parameter aggregation destructive
- **Research Area:** Federated Learning
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### However, the training of large-scale 3D-GS models at wireless edge faces various technical challenges including the limited communication, computation, and graphics processing unit (GPU) memory resources at edge devices, the structural inconsistency issue across local models hindering their effective aggregation, as well as privacy leakage risks associated with raw visual content and camera parameters
- **Research Area:** Federated Learning
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### Privacy-preserving cross-client deduplication effectively mitigates this issue by eliminating duplicate training data
- **Research Area:** Federated Learning
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### Application developers of distributed learning services face challenges that a typical federated learning loop does not address
- **Research Area:** Federated Learning
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### Existing edge-inference designs, however, predominantly optimize performance metrics based on current or short-term system states, without explicitly coupling current assignments with future commitment fulfillment
- **Research Area:** Edge Computing
- **Cluster:** Edge-cloud computing & Edge computing
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### TMLE itself, however, has remained a fully centralized procedure
- **Research Area:** Federated Learning
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### Despite its conceptual appeal, adoption is hindered by the lack of quantitative evidence that sharing spare vehicular capacity is viable, profitable and sustainable
- **Research Area:** Edge Computing
- **Cluster:** Edge-cloud computing & Edge computing
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** low
- **Publication Potential:** medium

#### Unfortunately, this problem has not been paid attention to by existing research, and thus some valuable resources (e.g., microservice image cache) remain obscure
- **Research Area:** Edge Computing
- **Cluster:** Edge-cloud computing & Edge computing
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### Edge computing mitigates these challenges by deploying cloud services closer to the end users and data sources, thereby improving resilience to network disruptions and reducing latency, bandwidth usage, and exposure to security threats
- **Research Area:** Edge Computing
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### However, most analyses assume AoI with bounded moments, creating a gap between theory and practice
- **Research Area:** Federated Learning
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### We first design the kernel matrices of DPPs using gradient information and quality scores, which inherently enables a flexible quality-diversity trade-off
- **Research Area:** Federated Learning
- **Cluster:** Edge-cloud computing & Edge computing
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### We show that the stopping problem admits an optimal rule attained at a finite stage, and that the anchor schedule is order-optimal in the peer-risk gap and the confidence level
- **Research Area:** Federated Learning
- **Cluster:** Edge-cloud computing & Edge computing
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### However, their deployment in privacy-sensitive, multi-party settings is constrained by the need to avoid centralizing raw data and by the requirement that modern quantum circuits remain parameter-efficient to stay trainable at scale
- **Research Area:** Federated Learning
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### We first discuss and then characterize the optimization problem that \emph{distributionally agnostic} FedAvg actually solves when participation is entirely unknown, possibly highly skewed, and of variable size across rounds: uniform aggregation is shown to minimize a well-defined stochastic objective, weighted by the participation-induced marginal, at a standard $\mathcal{O}(1/\sqrt{T})$ rate for convex and possibly nonsmooth losses
- **Research Area:** Federated Learning
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### The symbiotic scaling of artificial intelligence models and high-performance computing systems continually creates algorithmic challenges in their convergence
- **Research Area:** Federated Learning
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### However, as the size of applications grows, the centralised client-server approach used by Cloud computing increasingly limits the applications' scalability
- **Research Area:** Edge Computing
- **Cluster:** Edge-cloud computing & Edge computing
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### In addition, it supports fine-grained replication and per-collection consistency levels, ranging from sequential to eventual consistency, leaving developers the choice of how to resolve the trade-off between consistency and performance
- **Research Area:** Edge Computing
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### It categorizes existing UAV inspection architectures, identifies their key system challenges and architectural requirements, and experimentally assesses the feasibility of semantic edge intelligence on NVIDIA Jetson UAV-class hardware using the COCO-Bridge dataset
- **Research Area:** Edge AI
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### Federated averaging assumes that averaging local models is a reasonable way to solve one shared problem when participants' data are broadly similar
- **Research Area:** Federated Learning
- **Cluster:** Edge-cloud computing & Edge computing
- **Frequency:** 1
- **Status:** new
- **Known Limitations:**
  - Work on non-IID federated learning has shown that this assumption can withstand differences in label and feature distributions
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** high

#### To address these challenges, we propose a federated random walk averaging (FedRW) framework, which is a variant of federated averaging (FedAvg) that mitigates data heterogeneity by updating models along random walk (RW) paths and aggregating them at the server
- **Research Area:** Federated Learning
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### 3D Gaussian avatars support fast rendering, however, their real-time animation is often challenged by the costly neural inference
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### Federated Learning (FL) enables privacy-preserving fine-tuning of Large Language Models (LLMs), yet the massive communication overhead remains a critical bottleneck
- **Research Area:** Federated Learning
- **Cluster:** Edge-cloud computing & Edge computing
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### On Noisy Intermediate-Scale Quantum (NISQ) devices, however, decoherence, gate imperfections, and measurement errors reduce policy quality and make learning less reliable
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### However, client drift remains one of the most critical challenges, hindering the efficient training of a global model
- **Research Area:** Federated Learning
- **Cluster:** Edge-cloud computing & Edge computing
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### To address this challenge, in this letter, we propose a novel personalized FL framework (denoted as FedMAD) for RS image classification problems
- **Research Area:** Federated Learning
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### However, edge devices typically either lack the memory to store increasingly large LLM weights or, even with enough memory, spend unaffordable energy on loading the weights
- **Research Area:** Edge Computing
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### We formulate a constrained end-to-end throughput maximization problem covering unicast, multicast, multicommodity, convergecast, and many-to-many communication
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### The key challenges are conflicting residual evidence from neighboring series and residual patterns that vary across TSFMs and forecasting tasks
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### While federated learning has often been regarded as a ``necessary evil'', implying an unavoidable performance trade-off in exchange for decentralization and privacy, many prior works overlook its potential to improve robustness to out-of-distribution data
- **Research Area:** Federated Learning
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### Federated learning faces severe communication bottlenecks when clients upload high-dimensional model updates
- **Research Area:** Federated Learning
- **Cluster:** Edge-cloud computing & Edge computing
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### Identifying which speaker a listener is attending to in a noisy room -- the cocktail-party problem -- is the missing ingredient for next-generation hearing aids and brain-computer interfaces: it tells the device whose voice to amplify
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** low
- **Publication Potential:** medium

#### Retrieval-augmented execution offers a natural remedy but faces two coupled bottlenecks: knowledge at scale is hard to acquire, and self-collected priors inevitably drift from the live environment due to version updates, promotions, ads, A/B tests, and personalization
- **Research Area:** Edge AI
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### However, most existing approaches rely on computationally intensive deep learning-based video encoders and decoders, which hinders their deployment in resource-constrained scenarios
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### Wireless split learning (SL) reduces on-device computation by offloading upper layers to a server, yet transmitting high-dimensional intermediate features at each iteration remains a major communication bottleneck
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### Moreover, our convergence analysis reveals a new, fundamental trade-off: clients with larger FO-trained segments can provide more accurate updates, but favoring them can underrepresent other clients' data
- **Research Area:** Federated Learning
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### To address these challenges, we propose a \textbf{M}ultimodal \textbf{Fed}erated learning Prototype-guided Bilateral Alignment (MFedPBA) framework
- **Research Area:** Federated Learning
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Known Limitations:**
  - However, existing methods predominantly rely on idealized assumptions of model homogeneity and balanced modality distributions, rendering them ill-suited for practical scenarios characterized by heterogeneous client architectures and severe modality imbalance
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** high

#### To address these challenges, we propose Mira, an algorithm-system co-design that enables high-capacity MoE inference on a single GPU
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### We address this problem through representation learning, where each client learns a personalized linear head, while collaboratively estimating a shared nonlinear representation through Byzantine-robust aggregation
- **Research Area:** Federated Learning
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### Large models pose a second challenge: full-precision weights, calibration activations, and second-order state cannot all remain on one accelerator, while assigning complete layers to devices leaves each time-consuming layer solve serial
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### Agnostic federated learning (AFL) seeks a model that performs reliably across $m$ heterogeneous workers, but communication remains a bottleneck
- **Research Area:** Federated Learning
- **Cluster:** Edge-cloud computing & Edge computing
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### We report a crawl of CSP deployment on 7,969 top sites and 431 B2B publishers, Heavy-Ad budgets, closed-form privacy-utility trade-offs, a re-identification simulation, and an assessment of which attributes are predictable at all: company type and size are, seniority largely is not
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### Furthermore, we evaluate structural, cross-cutting challenges persisting across the literature, including consensus latency on constrained devices, post-quantum cryptographic vulnerability, smart-contract attack surfaces, and the adversarial vulnerability of evolving LLM-based detection engines
- **Research Area:** IoT
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Known Limitations:**
  - While the literature on blockchain-assisted intrusion detection and prevention systems (IDS/IPS) for Internet of Things (IoT) and Industrial Internet of Things (IIoT) networks is mature, existing systematic reviews suffer from two critical limitations: they overlook the structural shift toward modern Endpoint Detection and Response (EDR) and Extended Detection and Response (XDR) architectures, and they conflate blockchain's distinct functional roles into a single monolithic category
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** high

#### Furthermore, we identify the key challenges that still hinder practical deployment, such as limited transmitter-to-tag operating range and packet loss in frequency-shifted backscatter
- **Research Area:** IoT
- **Cluster:** Edge-cloud computing & Edge computing
- **Frequency:** 1
- **Status:** new
- **Known Limitations:**
  - We then outline recent research trends toward higher throughput, concurrent communication, simplified deployment, commercial compatibility, and joint communication and sensing
- **Novelty:** high
- **Feasibility:** low
- **Publication Potential:** high

#### However, whether these models learn generalizable attack behavior or exploit spurious dataset shortcuts- such as static testbed IP/MAC addresses and chronological recording artifacts-remains an important question
- **Research Area:** IoT
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### Finally, we discuss the opportunities and challenges of IAR BSs for future communications design
- **Research Area:** IoT
- **Cluster:** Edge-cloud computing & Edge computing
- **Frequency:** 1
- **Status:** new
- **Known Limitations:**
  - Using reflection, refraction, and amplification, RISs can act as innovative relay nodes to overcome spatial limitations caused by blockages, and improve the coverage range of existing infrastructure
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** high

#### We also empirically identify an optimal trade-off point for the multi-modal vision tasks
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** low
- **Publication Potential:** medium

#### Our study characterizes the fundamental trade-off between estimation error and communication rate, revealing that proactive transmissions significantly improve MSE even under strict IoT rate constraints
- **Research Area:** IoT
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** low
- **Publication Potential:** medium

#### As digital commerce ecosystems expand into low-end consumer electronics (CE), hardware constraints-specifically limited CPU duty cycles and volatile heap fragmentation-become significant bottlenecks for complex transactional flows
- **Research Area:** IoT
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### Its idea comes from language modeling: we hand the model the desired trade-off as an input, such that a single model only needs to be trained once offline to return any desired point on the curve in one rollout
- **Research Area:** Edge Computing
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### However, that project assumed CSI data as input
- **Research Area:** IoT
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### However, communication alone does not guarantee multi-year operation
- **Research Area:** IoT
- **Cluster:** Edge-cloud computing & Edge computing
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### Centralizing this massive volume of data creates severe communication overhead, unacceptable latency bottlenecks, single points of failure, and complex cross-domain governance challenges
- **Research Area:** Federated Learning
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### Reliable marine-engine fault diagnosis in maritime IoT is challenged by distributed data ownership, heterogeneous fault distributions, and continuously changing operating conditions
- **Research Area:** IoT
- **Cluster:** Edge-cloud computing & Edge computing
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### We formulate the static offloading design problem as the minimization of the rate-weighted average task delay over the routing probabilities, and solve it through a differentiable optimization framework based on softmax parameterization, log-sum-exp smoothing, and a stability barrier on server utilizations
- **Research Area:** Edge Computing
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### Anomaly detection in Internet of Things (IoT) networks presents unique challenges due to the diversity of devices, lack of labeled data, and domain variability across environments
- **Research Area:** IoT
- **Cluster:** Edge-cloud computing & Edge computing
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### Understanding these trade-offs is essential for live deployment if we aim to use APs for both networking and ML workloads
- **Research Area:** IoT
- **Cluster:** Edge-cloud computing & Edge computing
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### Existing designs are, however, fundamentally mismatched with mobility and time-varying energy patterns
- **Research Area:** IoT
- **Cluster:** Edge-cloud computing & Edge computing
- **Frequency:** 1
- **Status:** new
- **Known Limitations:**
  - Using a prototype we built and real-world mobility and power traces, we compare our design against a rate-adaptive baseline that only considers the instantaneous channel conditions
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** high

#### We formalize the clustering optimization problem, derive closed-form decoding probability bounds for Markov erasure channels, and prove O(sqrt(T)) regret for online reconfiguration under the Follow-the-Regularized-Leader (FTRL) framework
- **Research Area:** Edge AI
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### Experimental results on heterogeneous MNIST and CIFAR-10 settings show that QEF-GT-AdamW consistently improves robustness and convergence performance over representative DecL baselines while achieving favorable accuracy-communication trade-offs under limited wireless resources
- **Research Area:** Federated Learning
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### However, conventional multipath routing usually splits traffic over predefined end-to-end paths, making it difficult to respond quickly to link fluctuations and topology changes in UAV networks
- **Research Area:** Edge Computing
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### The massive adoption of Internet of Things (IoT) devices across critical domains such as healthcare, smart cities, industrial automation, and critical infrastructure introduces significant cybersecurity and regulatory challenges
- **Research Area:** IoT
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### The emergence of high-frequency pulsating logistics unmanned aerial vehicle (UAV) swarms gives rise to ``Digital Tides'', i.e., complex traffic dynamics that challenge sustainable resource provisioning in mobile computing networks
- **Research Area:** Edge Computing
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### However, legal discrepancies, standardization challenges and ethical issues limit the convergence process
- **Research Area:** IoT
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### However, the increasing number of human-tiger conflicts in this region pose a significant threat to both human livelihoods and tiger conservation
- **Research Area:** Edge AI
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** low
- **Publication Potential:** medium

#### However, traditional data quality control (QC) primarily relies on fixed-threshold screening and manual spot checks, making it highly challenging to effectively identify sophisticated anomalies and possible artificial interference
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Known Limitations:**
  - To address the limitations of conventional methods—namely, low recognition rates for sporadic equipment failures and emerging anomalous patterns, as well as a heavy reliance on manual labels—this paper constructs an automated quality control model for industrial waste gas online monitoring data based on unsupervised learning
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** high

#### The study finds that the Min School Guqin has notable strengths in policy support and technology application, yet faces practical challenges including insufficiently unleashed market consumption demand and low audience participation
- **Research Area:** Edge AI
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### Once she is caught, however, the narrative reallocates agency and interpretive authority
- **Research Area:** Edge AI
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** low
- **Publication Potential:** medium

#### Reproducible low-fidelity numerical studies provide preliminary support for context-conditioned residual diagnosis and the revised thermal-continuity trade-off underlying health-aware derating, including robustness and sensitivity analyses
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### The reduction of synthetic pesticide reliance is a central challenge in modern agriculture
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### However, the risk of postoperative complicationsspecifically associated with sleeve lobectomy in lung cancer patients with obstructive pneumonia remains unknown.Case Report: The 83-year-old man who had a 59-pack-year smoking history was found to have a lesion obstructing the rightupper bronchus with complete atelectasis of the right upper lobe on chest computed tomography
- **Research Area:** Edge AI
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** low
- **Publication Potential:** medium

#### In May 2018, fifteen leading global container terminal operators and several port equipment manufacturers convened at Federation of European Private Port Companies and Terminals (FEPORT) headquarters in Brussels to address the pressing challenges facing the cargo handling sector
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### The lack of mechanization in India is due to small land holdings, improper row spacing, and a lack of skill in mechanization
- **Research Area:** Edge AI
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** low
- **Publication Potential:** medium

#### However, conventional cloud-centric architectures can introduce communication overhead, latency, privacy concerns, and additional energy costs
- **Research Area:** Edge Computing
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### However, enhanced skin permeation cannot by itself establish therapeutically meaningful delivery to deep anatomical targets
- **Research Area:** Edge AI
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### Meanwhile, more robust alternatives like SHA-256 and SHA-3 frequently encounter performance bottlenecks when processing large volumes of data in real-time web architectures
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Known Limitations:**
  - To address these limitations, this research integrates BLAKE3 a cutting-edge cryptographic hash function that pairs SHA-256-level security with superior throughput via a parallelized Merkle-tree design into a web-based platform dedicated to document integrity verification
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** high

#### It also identifies challenges in cultural-pragmatic accuracy, hallucinated expressions, assessment validity, data privacy, unequal access, teacher readiness, and learner dependency
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### Nevertheless, the practical implementation of FL presents technical and organizational challenges, as it generally requires complex communication infrastructures
- **Research Area:** Federated Learning
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### We have previously reported that mesenchymal stem cell–derived extracellular vesicles delay retinal degeneration by exerting anti-inflammatory effects though the miR-146a–nuclear receptor subfamily 4 group A member 3 axis; however, it remains unclear how NR4A3 drives inflammation
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### However, it remains unclear whether these methods can effectively update deprecated API knowledge and enable edited models to generate up-to-date APIs
- **Research Area:** Edge AI
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### However, smart contracts written in Move may still contain certain vulnerabilities that are beyond the reach of its type system
- **Research Area:** Edge AI
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### Our findings challenge the conventional belief that contamination inevitably leads to performance overestimation, providing new insights into the evaluation and deployment of code intelligence models
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### To address this challenge, prior work has adopted Retrieval-Augmented Generation (RAG) frameworks based on semantic indexing or structure-aware graph analysis
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Known Limitations:**
  - However, we identify key limitations of this approach, including sensitivity to noisy matches caused by high-frequency ambiguous keywords and context fragmentation due to rigid truncation boundaries
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** high

#### We implemented Gordian on top of the KLEE symbolic execution engine and evaluated it on synthetic “logic bombs” capturing distinct symbolic reasoning challenges, a popular mathematical library FDLibM, and four structured-input programs (libexpat, jq, bc and libyaml)
- **Research Area:** Edge AI
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Known Limitations:**
  - Recent work proposed replacing constraint solvers with large language models (LLMs) to bypass these limitations, but such approaches struggle to analyze real-world codebases, where deep execution paths require globally consistent reasoning across many interacting constraints
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** high

#### To address this issue, we introduce μSkia, a formal semantics for the Skia 2D graphics library, and mechanize this semantics in Lean
- **Research Area:** Edge Computing
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### However, evaluating these LLM-based agents remains challenging due to the complex, multi-step nature of geospatial workflows
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### However, reproducing the flaky-test failures remains a major challenge due to their inherent non-determinism
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### In addition, optimization problems driven by environmental processes encounter the issue of model ambiguity because of a lack of sufficient data for model identification
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### However, producing machine-checked proofs in such provers remains a bottleneck
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### However, despite decades of development in compiler testing, testing Cranelift still presents unique challenges, including (1) constructing valid IR under the strict enforcement of SSA form, (2) generating sequences with sufficient computational density to stress backend components, and (3) balancing broad backend coverage with efficient root cause analysis across heterogeneous architectures
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### However, attackers increasingly abuse this standardization to disguise malicious trap tokens
- **Research Area:** Edge Computing
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### This can be possible if teachers are assisted in mitigating the daily challenges of teaching such learners
- **Research Area:** Edge AI
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### However, its application in supporting technique development among beginner athletes remains insufficiently explored
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** Edge-cloud computing & Edge computing
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** low
- **Publication Potential:** medium

#### The findings show that, including the ability of national programmes such as NEP 2020, SWAYAM, DIKSHA, PM e-VIDYA, and others, to promote access to digital tools was low within periphery or hill areas (e.g., Nagaland), due to lack of infrastructural resources, digital divide, unprepared teachers and economic/social divides, and more
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### However, their mathematical systems differed fundamentally from each another, although they both dealt with the same domain of expansion
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** Edge-cloud computing & Edge computing
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### However, many of today's predominant needs assessment frameworks conceptualize needs assessments as linear or otherwise level-limited processes, making them less effective in highly complex and rapidly changing environments
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** medium

#### However, this performance increase comes with increased mechanical and electronic complexity
- **Research Area:** AI for Resource-Constrained Systems
- **Cluster:** Edge-cloud computing & Edge computing
- **Frequency:** 1
- **Status:** new
- **Novelty:** high
- **Feasibility:** low
- **Publication Potential:** medium

#### However, despite significant advancements, challenges persist in fabrication scalability, algorithm-hardware co-design, and lifecycle sustainability assessment
- **Research Area:** Edge AI
- **Cluster:** 
- **Frequency:** 1
- **Status:** new
- **Known Limitations:**
  - As traditional CMOS scaling nears its physical limitations, researchers are exploring bio-inspired Neuromorphic designs that mimic the brain's energy-efficient computing mechanisms using spiking neural networks (SNNs), as demonstrated by platforms like Intel’s Loihi and IBM’s True North (Davies et al., 2018; Merolla et al., 2014)
- **Novelty:** high
- **Feasibility:** medium
- **Publication Potential:** high

---

## Research Gap Clusters

### Edge-cloud computing & Edge computing
- **Research Area:** Edge Computing
- **Problems:** 26
- **Papers:** 26
- **Recurring Limitations:**
  - However, a key limitation is the vulnerability to non-stationary policies when edge nodes join or leave dynamically in ad-hoc mobile networks
  - The core limitation is memory thrashing when total pre-warmed snapshot sizes exceed available edge RAM during bursty traffic spikes
  - However, a major limitation is that state convergence under high conflict rates incurs substantial storage overhead from tombstone accumulation
  - Because of compatibility limitations, WebAssembly has mainly been applied to Function-as-a-Service (FaaS) and Edge Computing scenarios, where it has attracted growing research interest
  - Simultaneously, we confirm known limitations in CPU-intensive workloads
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
