"""
Pre-seeded realistic academic materials for UniVault.
Includes high-demand lecture notes, PYQs, cheat sheets, and lab manuals
across multiple university departments, branches, and semesters.
"""

SAMPLE_MATERIALS = [
    {
        "title": "Complete Data Structures & Algorithms Hand-written Master Notes",
        "description": "Comprehensive semester lecture notes covering Trees, Balanced BSTs, Graphs (Dijkstra, Bellman-Ford, Kruskal), Dynamic Programming patterns, and Time Complexity proofs with diagrams.",
        "subject_name": "Data Structures & Algorithms",
        "subject_code": "CS-201",
        "branch": "Computer Science & Engineering",
        "semester": "Semester 3",
        "university": "Stanford University",
        "material_type": "Lecture Notes",
        "academic_year": "2024",
        "file_url": "https://raw.githubusercontent.com/mathiasbynens/small/master/pdf.pdf",
        "file_type": "PDF",
        "file_size_kb": 3420,
        "page_count": 84,
        "uploader_name": "Alex Chen",
        "uploader_avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80",
        "downloads_count": 1420,
        "views_count": 5280,
        "upvotes_count": 389,
        "tags": "DSA,Trees,Graphs,DP,Algorithms,InterviewPrep",
        "is_featured": 1,
        "preview_content": """UNIT 1: Asymptotic Analysis & Recurrences
- Master Theorem: T(n) = aT(n/b) + f(n)
- Case 1: log_b(a) > c => Theta(n^{log_b(a)})
- Case 2: log_b(a) = c => Theta(n^c * log n)
- Case 3: log_b(a) < c => Theta(f(n))

UNIT 2: Trees & Disjoint Sets
- AVL Rotations: Left-Left, Right-Right, Left-Right, Right-Left balance factors.
- Red-Black Tree 5 Core Properties & Color Inversions.
- Disjoint-Set Union by Rank & Path Compression: O(alpha(n)) amortized.

UNIT 3: Graph Traversal & Shortest Path
- BFS for unweighted graphs (Queue)
- DFS for topological sorting & strongly connected components (Kosaraju & Tarjan)
- Dijkstra's Algorithm using Min-Heap: O((V + E) log V)
- Bellman-Ford for negative weight cycles: O(V * E)

UNIT 4: Dynamic Programming Archetypes
- 0/1 Knapsack & Fractional Knapsack
- Longest Common Subsequence (LCS)
- Matrix Chain Multiplication (MCM)
- Bellman Equation & Optimal Substructure proofs."""
    },
    {
        "title": "Operating Systems End-Sem Solved PYQs (2020 - 2024)",
        "description": "5 Years of solved university exam papers with model answers for CPU Scheduling, Deadlock Detection & Banker's Algorithm, Virtual Memory Paging, and Semaphores synchronization problems.",
        "subject_name": "Operating Systems",
        "subject_code": "CS-302",
        "branch": "Computer Science & Engineering",
        "semester": "Semester 4",
        "university": "MIT",
        "material_type": "Previous Year Questions (PYQs)",
        "academic_year": "2024",
        "file_url": "https://raw.githubusercontent.com/mathiasbynens/small/master/pdf.pdf",
        "file_type": "PDF",
        "file_size_kb": 4180,
        "page_count": 62,
        "uploader_name": "Sarah Jenkins",
        "uploader_avatar": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&auto=format&fit=crop&q=80",
        "downloads_count": 2180,
        "views_count": 6840,
        "upvotes_count": 512,
        "tags": "OS,BankersAlgorithm,Paging,Semaphores,PYQ,Solutions",
        "is_featured": 1,
        "preview_content": """[QUESTION 1 - DEC 2023 - 10 MARKS]
Consider 5 processes P0 through P4 and 3 resource types A, B, C.
Apply Banker's Safety Algorithm to find whether the current allocation is safe:
Available: [3, 3, 2]
Matrix calculation: Need = Max - Allocation.
Safe sequence exists: <P1, P3, P4, P0, P2>. Hence system is in a SAFE STATE.

[QUESTION 2 - MAY 2023 - 8 MARKS]
Explain Dining Philosophers problem using monitor construct and counting semaphores.
Solution includes full pseudo-code preventing circular wait condition.

[QUESTION 3 - DEC 2022 - 12 MARKS]
Numerical: FIFO, LRU, and Optimal Page Replacement for reference string:
7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1 with 3 frames.
Comparison of Page Faults:
- FIFO: 15 Page Faults (Demonstrating Belady's Anomaly)
- LRU: 12 Page Faults
- Optimal: 9 Page Faults."""
    },
    {
        "title": "DBMS Quick Revision Sheet: Normalization & SQL Queries",
        "description": "Crisp 12-page exam cheat sheet detailing 1NF, 2NF, 3NF, BCNF lossless decomposition, ACID properties, Transaction schedules, Concurrency Control, and complex SQL joins.",
        "subject_name": "Database Management Systems",
        "subject_code": "CS-204",
        "branch": "Computer Science & Engineering",
        "semester": "Semester 4",
        "university": "IIT Bombay",
        "material_type": "Formula Sheets / Cheat Sheets",
        "academic_year": "2023",
        "file_url": "https://raw.githubusercontent.com/mathiasbynens/small/master/pdf.pdf",
        "file_type": "PDF",
        "file_size_kb": 1820,
        "page_count": 14,
        "uploader_name": "Rohan Sharma",
        "uploader_avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&auto=format&fit=crop&q=80",
        "downloads_count": 3120,
        "views_count": 8900,
        "upvotes_count": 680,
        "tags": "DBMS,SQL,BCNF,Normalization,ACID,Transactions",
        "is_featured": 1,
        "preview_content": """QUICK NORMALIZATION CHECKLIST:
- 1NF: Atomic values only. No multi-valued attributes or nested relations.
- 2NF: 1NF + No partial dependency (No non-prime attribute depends on a proper subset of candidate key).
- 3NF: 2NF + No transitive dependency (For every X -> Y, X is Super Key or Y is Prime Attribute).
- BCNF: Stricter 3NF. For every non-trivial X -> Y, X MUST be a Super Key.

TRANSACTION SCHEDULES:
- Conflict Serializable: Precedence Graph has NO cycles.
- Recoverable Schedule: If Tj reads from Ti, Ti must commit before Tj commits.
- Cascadeless Schedule: Tj reads value written by Ti ONLY AFTER Ti has committed.

INDEXING:
- B-Tree vs B+ Tree: B+ Tree stores all data pointers only in leaf nodes; leaves are linked as sequential list for fast range queries."""
    },
    {
        "title": "Machine Learning & Deep Learning Formula Handbook",
        "description": "Every essential formula for university exams and interviews: Backpropagation calculus, Loss functions, SVM dual optimization, CNN layer math, Transformer self-attention equations, and Regularization.",
        "subject_name": "Machine Learning",
        "subject_code": "AI-401",
        "branch": "Artificial Intelligence & Data Science",
        "semester": "Semester 7",
        "university": "UC Berkeley",
        "material_type": "Formula Sheets / Cheat Sheets",
        "academic_year": "2024",
        "file_url": "https://raw.githubusercontent.com/mathiasbynens/small/master/pdf.pdf",
        "file_type": "PDF",
        "file_size_kb": 2240,
        "page_count": 22,
        "uploader_name": "Elena Rostova",
        "uploader_avatar": "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=100&auto=format&fit=crop&q=80",
        "downloads_count": 1890,
        "views_count": 5120,
        "upvotes_count": 420,
        "tags": "ML,DeepLearning,NeuralNetworks,Transformers,Calculus,CheatSheet",
        "is_featured": 0,
        "preview_content": """LOSS FUNCTIONS & GRADIENTS:
- MSE: L = (1/2m) * sum( (y_hat - y)^2 )
- Binary Cross Entropy: -[ y * log(p) + (1-y) * log(1-p) ]
- Softmax Cross Entropy: -sum( y_i * log(p_i) )

CNN DIMENSION MATH:
- Output size = floor((W - F + 2P)/S) + 1
- Parameter count per Conv Layer = (K_w * K_h * C_in + 1) * C_out

TRANSFORMER MULTI-HEAD ATTENTION:
- Attention(Q, K, V) = softmax( (Q * K^T) / sqrt(d_k) ) * V
- MultiHead(Q,K,V) = Concat(head_1, ..., head_h) * W_O"""
    },
    {
        "title": "Computer Networks Comprehensive Notes (OSI, TCP/IP, Routing)",
        "description": "Prof. Peterson curriculum lecture notes. Includes detailed packet headers, Sliding Window Protocols, Subnetting numericals with CIDR, OSPF vs BGP, and Congestion Control mechanisms (TCP Reno/Tahoe).",
        "subject_name": "Computer Networks",
        "subject_code": "CS-305",
        "branch": "Computer Science & Engineering",
        "semester": "Semester 5",
        "university": "Delhi University",
        "material_type": "Lecture Notes",
        "academic_year": "2023",
        "file_url": "https://raw.githubusercontent.com/mathiasbynens/small/master/pdf.pdf",
        "file_type": "PDF",
        "file_size_kb": 5120,
        "page_count": 96,
        "uploader_name": "Vikram Sethi",
        "uploader_avatar": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100&auto=format&fit=crop&q=80",
        "downloads_count": 1640,
        "views_count": 4820,
        "upvotes_count": 345,
        "tags": "Networks,TCP,IP,Subnetting,Routing,BGP,OSI",
        "is_featured": 0,
        "preview_content": """TOPIC 1: SUBNETTING NUMERICALS
Given IP: 192.168.10.0/27
- Subnet mask: 255.255.255.224
- Number of subnets: 2^3 = 8
- Usable hosts per subnet: 2^(32-27) - 2 = 30 hosts
- Block size = 256 - 224 = 32

TOPIC 2: SLIDING WINDOW PROTOCOLS
- Stop and Wait Efficiency: eta = 1 / (1 + 2a), where a = T_prop / T_trans
- Go-Back-N (GBN): Sender Window Size = 2^m - 1, Receiver Window Size = 1
- Selective Repeat (SR): Sender Window Size = 2^(m-1), Receiver Window Size = 2^(m-1)

TOPIC 3: TCP CONGESTION CONTROL
- Slow Start: cwnd doubles every RTT (exponential growth until ssthresh)
- Congestion Avoidance: cwnd increases by 1 MSS every RTT (additive increase)
- Fast Retransmit: Triggered by 3 duplicate ACKs without waiting for timeout."""
    },
    {
        "title": "Digital Signal Processing (DSP) University Exam Solved Papers",
        "description": "Solved question bank covering Radix-2 DIT/DIF FFT butterflies, Z-Transform pole-zero stability, Butterworth & Chebyshev IIR Filter design, and FIR window techniques.",
        "subject_name": "Digital Signal Processing",
        "subject_code": "EC-303",
        "branch": "Electronics & Communication",
        "semester": "Semester 5",
        "university": "Anna University",
        "material_type": "Solved Papers",
        "academic_year": "2024",
        "file_url": "https://raw.githubusercontent.com/mathiasbynens/small/master/pdf.pdf",
        "file_type": "PDF",
        "file_size_kb": 3890,
        "page_count": 58,
        "uploader_name": "Kavita Nair",
        "uploader_avatar": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=100&auto=format&fit=crop&q=80",
        "downloads_count": 980,
        "views_count": 2740,
        "upvotes_count": 210,
        "tags": "DSP,FFT,ZTransform,Butterworth,Chebyshev,SolvedPaper",
        "is_featured": 0,
        "preview_content": """PROBLEM 1: 8-POINT RADIX-2 DIT-FFT
Given sequence x[n] = {1, 2, 3, 4, 4, 3, 2, 1}.
Step 1: Bit-reversal permutation:
x[0], x[4], x[2], x[6], x[1], x[5], x[3], x[7]
Step 2: 3 Butterfly stages with twiddle factors W_8^0, W_8^1, W_8^2, W_8^3.
Step 3: Verification via Parseval's relation: Sum(|x[n]|^2) = (1/N) * Sum(|X[k]|^2).

PROBLEM 2: BUTTERWORTH FILTER SPECIFICATION
Design analog lowpass filter with passband edge 0.2 pi, attenuation <= 1 dB,
stopband edge 0.3 pi, attenuation >= 15 dB.
Calculated filter order N = 4, cutoff frequency Omega_c = 0.223 rad/sec."""
    },
    {
        "title": "Engineering Mathematics III (Transform Calculus & Fourier Series)",
        "description": "Complete classroom notes with 100+ worked problems for Laplace transforms, inverse Laplace by convolution, Fourier Series (Euler's formulas), Half-Range series, and PDE separation of variables.",
        "subject_name": "Engineering Mathematics III",
        "subject_code": "MA-301",
        "branch": "Applied Sciences & Mathematics",
        "semester": "Semester 3",
        "university": "VTU Karnataka",
        "material_type": "Lecture Notes",
        "academic_year": "2023",
        "file_url": "https://raw.githubusercontent.com/mathiasbynens/small/master/pdf.pdf",
        "file_type": "PDF",
        "file_size_kb": 4720,
        "page_count": 112,
        "uploader_name": "Prof. K. Venkatesh",
        "uploader_avatar": "https://images.unsplash.com/photo-1560250097-0b93528c311a?w=100&auto=format&fit=crop&q=80",
        "downloads_count": 4210,
        "views_count": 11300,
        "upvotes_count": 920,
        "tags": "Math,Laplace,Fourier,PDE,TransformCalculus,Handwritten",
        "is_featured": 1,
        "preview_content": """LAPLACE TRANSFORMS STANDARD TABLE:
- L{1} = 1/s
- L{t^n} = n! / s^{n+1}
- L{e^{at}} = 1 / (s - a)
- L{sin(at)} = a / (s^2 + a^2)
- L{cos(at)} = s / (s^2 + a^2)
- First Shifting Property: L{e^{at} * f(t)} = F(s - a)
- Convolution Theorem: L^{-1}{ F(s) * G(s) } = integral_0^t f(u) g(t - u) du

FOURIER SERIES EXPANSION in (-L, L):
f(x) = a_0/2 + sum_{n=1}^inf [ a_n cos(n pi x / L) + b_n sin(n pi x / L) ]
Euler's Formulae:
- a_0 = (1/L) * int_{-L}^L f(x) dx
- a_n = (1/L) * int_{-L}^L f(x) cos(n pi x / L) dx
- b_n = (1/L) * int_{-L}^L f(x) sin(n pi x / L) dx"""
    },
    {
        "title": "Thermodynamics & Heat Transfer Formula Bible",
        "description": "Concise mechanical formula handbook: 1st & 2nd Laws of Thermodynamics, Carnot efficiency, Otto & Diesel cycles, Rankine cycle reheat, Fourier's law of conduction, and Nusselt number correlations.",
        "subject_name": "Applied Thermodynamics",
        "subject_code": "ME-302",
        "branch": "Mechanical Engineering",
        "semester": "Semester 4",
        "university": "IIT Delhi",
        "material_type": "Formula Sheets / Cheat Sheets",
        "academic_year": "2024",
        "file_url": "https://raw.githubusercontent.com/mathiasbynens/small/master/pdf.pdf",
        "file_type": "PDF",
        "file_size_kb": 1940,
        "page_count": 16,
        "uploader_name": "Arjun Singhania",
        "uploader_avatar": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=100&auto=format&fit=crop&q=80",
        "downloads_count": 1150,
        "views_count": 3410,
        "upvotes_count": 280,
        "tags": "Thermodynamics,HeatTransfer,Carnot,Rankine,Mechanical",
        "is_featured": 0,
        "preview_content": """KEY EQUATIONS & CYCLES:
- First Law for Open System: q - w = h_2 - h_1 + (V_2^2 - V_1^2)/2000 + g(z_2 - z_1)/1000
- Carnot Efficiency: eta_Carnot = 1 - (T_L / T_H)
- Otto Cycle Efficiency: eta = 1 - 1 / (r^{gamma - 1}), where r = V1 / V2
- Diesel Cycle Efficiency: eta = 1 - (1 / r^{gamma - 1}) * [ (r_c^gamma - 1) / (gamma * (r_c - 1)) ]

HEAT TRANSFER:
- Conduction (Fourier's Law): q = -k * A * (dT / dx)
- Convection (Newton's Law): q = h * A * (T_s - T_inf)
- Radiation (Stefan-Boltzmann): q = epsilon * sigma * A * (T_s^4 - T_surr^4)"""
    },
    {
        "title": "Web Development & Cloud Computing Lab Practical Manual",
        "description": "Complete lab record experiments with working source code, circuit/network diagrams, RESTful API specifications, and Dockerfile deployment instructions for semester practical exam.",
        "subject_name": "Web Technologies & Cloud Lab",
        "subject_code": "CS-408L",
        "branch": "Computer Science & Engineering",
        "semester": "Semester 6",
        "university": "Stanford University",
        "material_type": "Lab Manuals",
        "academic_year": "2024",
        "file_url": "https://raw.githubusercontent.com/mathiasbynens/small/master/pdf.pdf",
        "file_type": "PDF",
        "file_size_kb": 3100,
        "page_count": 48,
        "uploader_name": "Maya Lin",
        "uploader_avatar": "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=100&auto=format&fit=crop&q=80",
        "downloads_count": 1720,
        "views_count": 4120,
        "upvotes_count": 310,
        "tags": "LabManual,WebDev,Docker,React,NodeJS,CloudLab",
        "is_featured": 0,
        "preview_content": """EXPERIMENT 1: REST API with JWT Authentication
- Architecture diagram and endpoint documentation
- Implementation of Bearer token validation middleware
- Unit testing with Mocha / Jest

EXPERIMENT 2: Microservice Containerization with Docker
- Multi-stage Dockerfile setup for Python/Flask and Node.js
- docker-compose.yml configuration with Redis cache and PostgreSQL

EXPERIMENT 3: Cloud Hosting and Object Storage
- Continuous Deployment from GitHub
- Environment Variable security and CORS management."""
    },
    {
        "title": "Computer Organization & Architecture (COA) Mid-Term PYQ Bank",
        "description": "Pipelining hazards, Booth's multiplication algorithm, Cache memory mapping (Direct, Fully Associative, Set Associative) numericals, and Microprogrammed control unit design.",
        "subject_name": "Computer Architecture",
        "subject_code": "CS-206",
        "branch": "Computer Science & Engineering",
        "semester": "Semester 3",
        "university": "MIT",
        "material_type": "Previous Year Questions (PYQs)",
        "academic_year": "2023",
        "file_url": "https://raw.githubusercontent.com/mathiasbynens/small/master/pdf.pdf",
        "file_type": "PDF",
        "file_size_kb": 2680,
        "page_count": 38,
        "uploader_name": "David Miller",
        "uploader_avatar": "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=100&auto=format&fit=crop&q=80",
        "downloads_count": 1390,
        "views_count": 3950,
        "upvotes_count": 275,
        "tags": "COA,Pipelining,CacheMapping,BoothsAlgorithm,PYQ",
        "is_featured": 0,
        "preview_content": """NUMERICAL 1: CACHE MEMORY MAPPING
Physical address space: 4 GB (32 bits).
Cache size: 64 KB, Block size: 32 Bytes.
Find Tag, Set/Index, and Word offset bits for 4-way Set Associative mapping:
- Word offset = log2(32) = 5 bits
- Number of lines = 64 KB / 32 B = 2048 lines
- Number of sets = 2048 / 4 = 512 sets => Set index = log2(512) = 9 bits
- Tag bits = 32 - (9 + 5) = 18 bits.

NUMERICAL 2: PIPELINE SPEEDUP
5-stage pipeline with clock cycle = 2 ns.
Number of instructions n = 1000.
Speedup over non-pipelined system (execution time = 10 ns per instruction):
Non-pipelined time = 1000 * 10 = 10,000 ns.
Pipelined time = (k + n - 1) * t_p = (5 + 999) * 2 = 2008 ns.
Speedup S = 10000 / 2008 = 4.98x."""
    },
    {
        "title": "Complete Civil Engineering Structural Analysis Formula Sheet",
        "description": "Moment distribution method, Slope-deflection equations, Bending moment & Shear force diagrams for indeterminate beams, Euler's column buckling formula, and Castigliano's theorems.",
        "subject_name": "Structural Analysis",
        "subject_code": "CE-301",
        "branch": "Civil Engineering",
        "semester": "Semester 5",
        "university": "IIT Bombay",
        "material_type": "Formula Sheets / Cheat Sheets",
        "academic_year": "2024",
        "file_url": "https://raw.githubusercontent.com/mathiasbynens/small/master/pdf.pdf",
        "file_type": "PDF",
        "file_size_kb": 2150,
        "page_count": 20,
        "uploader_name": "Pooja Hegde",
        "uploader_avatar": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=100&auto=format&fit=crop&q=80",
        "downloads_count": 870,
        "views_count": 2400,
        "upvotes_count": 180,
        "tags": "Civil,StructuralAnalysis,BMD,SFD,SlopeDeflection",
        "is_featured": 0,
        "preview_content": """CORE EQUATIONS:
- Slope-Deflection Equation:
  M_AB = M_FAB + (2EI/L) * [ 2*theta_A + theta_B - 3*delta/L ]
- Euler's Critical Buckling Load:
  P_cr = (pi^2 * E * I) / (L_eff^2)
  Effective lengths:
  - Both ends pinned: L_eff = L
  - Both ends fixed: L_eff = 0.5 L
  - One fixed, one pinned: L_eff = 0.707 L
  - One fixed, one free: L_eff = 2 L"""
    },
    {
        "title": "Official B.Tech Computer Science Syllabus & Exam Blueprint (2024-2028)",
        "description": "University official curriculum breakdown, credit distribution, recommended textbooks, and question paper marking blueprint for Semesters 1 through 8.",
        "subject_name": "Curriculum & Syllabus Guide",
        "subject_code": "SYL-2024",
        "branch": "Computer Science & Engineering",
        "semester": "Semester 1",
        "university": "Delhi University",
        "material_type": "Syllabus",
        "academic_year": "2024",
        "file_url": "https://raw.githubusercontent.com/mathiasbynens/small/master/pdf.pdf",
        "file_type": "PDF",
        "file_size_kb": 1450,
        "page_count": 32,
        "uploader_name": "Academic Office",
        "uploader_avatar": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&auto=format&fit=crop&q=80",
        "downloads_count": 3400,
        "views_count": 9200,
        "upvotes_count": 415,
        "tags": "Syllabus,Curriculum,Credits,ExamPattern,Official",
        "is_featured": 0,
        "preview_content": """SEMESTER 1-8 CREDIT MATRIX & WEIGHTAGE:
- Basic Science Courses: 24 Credits
- Engineering Science Courses: 22 Credits
- Professional Core Courses: 48 Credits
- Professional Electives: 18 Credits
- Open Electives: 12 Credits
- Capstone Project & Internship: 16 Credits

EXAM QUESTION PAPER SCHEME:
- Part A: 10 Objective / 2-mark conceptual questions (20 Marks)
- Part B: 5 Long-form analytical problems with internal choice (80 Marks)"""
    }
]

SAMPLE_REVIEWS = [
    {
        "material_id": 1,
        "author_name": "Daniel Kim",
        "rating": 5,
        "comment": "Literally saved my end-semester exam! The graph algorithms and dynamic programming explanations are clearer than any textbook."
    },
    {
        "material_id": 1,
        "author_name": "Ananya Roy",
        "rating": 5,
        "comment": "Handwritten diagrams make Red-Black trees and AVL rotations super intuitive. 10/10 recommend to all sophomores!"
    },
    {
        "material_id": 2,
        "author_name": "Marcus Vance",
        "rating": 5,
        "comment": "Every single numerical from the 2023 paper came up with slightly altered numbers. Got an A in OS thanks to this!"
    },
    {
        "material_id": 2,
        "author_name": "Tanya Verma",
        "rating": 4,
        "comment": "Great solutions for Banker's safety algorithm and FIFO/LRU page replacement. Very neat presentation."
    },
    {
        "material_id": 3,
        "author_name": "Siddharth Mehta",
        "rating": 5,
        "comment": "The BCNF and 3NF decomposition steps are explained with a 3-step checklist. Read this 2 hours before the exam and aced it."
    },
    {
        "material_id": 4,
        "author_name": "Sophia Zhang",
        "rating": 5,
        "comment": "Transformer self-attention matrix derivation is spot on! Essential for both ML finals and tech interviews."
    },
    {
        "material_id": 7,
        "author_name": "Harish Gowda",
        "rating": 5,
        "comment": "Engineering Math 3 is notoriously tough at VTU, but this Laplace & Fourier collection made it manageable."
    }
]

SAMPLE_CONTRIBUTORS = [
    {
        "name": "Alex Chen",
        "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80",
        "university": "Stanford University",
        "uploads_count": 28,
        "upvotes_count": 1420,
        "badge": "Gold Scholar",
        "reputation": 4850
    },
    {
        "name": "Sarah Jenkins",
        "avatar": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&auto=format&fit=crop&q=80",
        "university": "MIT",
        "uploads_count": 34,
        "upvotes_count": 2180,
        "badge": "Exam Savior",
        "reputation": 6200
    },
    {
        "name": "Rohan Sharma",
        "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&auto=format&fit=crop&q=80",
        "university": "IIT Bombay",
        "uploads_count": 22,
        "upvotes_count": 1890,
        "badge": "Notes Master",
        "reputation": 5100
    },
    {
        "name": "Elena Rostova",
        "avatar": "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=100&auto=format&fit=crop&q=80",
        "university": "UC Berkeley",
        "uploads_count": 19,
        "upvotes_count": 1240,
        "badge": "Formula Guru",
        "reputation": 3900
    },
    {
        "name": "Maya Lin",
        "avatar": "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=100&auto=format&fit=crop&q=80",
        "university": "Stanford University",
        "uploads_count": 15,
        "upvotes_count": 980,
        "badge": "Lab Ace",
        "reputation": 3150
    }
]
