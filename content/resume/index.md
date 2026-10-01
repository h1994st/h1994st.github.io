+++
title = "Resume"
description = "Resume of Shengtuo Hu, a security-focused software engineer with a Ph.D. in Computer Science from the University of Michigan: experience, projects, publications and service."
template = "resume.html"
# The old /publications/ page was merged into this one.
aliases = ["/publications/"]

# Everything on this page is rendered by templates/resume.html from the
# tables below. Experience entries take role metadata and at most a one-line
# `summary` of the domain; there is no field for detailed duties on purpose.
[extra]
styles = ["css/resume.css"]
headline = "Security-focused Software Engineer, Ph.D. in Computer Science"
contact = [
  { label = "shengtuo.me", url = "https://shengtuo.me" },
  { label = "github.com/h1994st", url = "https://github.com/h1994st" },
  { label = "linkedin.com/in/shengtuo", url = "https://www.linkedin.com/in/shengtuo/" },
]
summary = "Security-focused software engineer with a Ph.D. in Computer Science and 5+ years of experience building security tooling, program analysis infrastructure, and large-scale detection systems. Strong background in vulnerability discovery, fuzzing, and network protocol security."
skills = [
  { label = "Languages/Tools", value = "C/C++, Python, Rust, Go, Java, SQL (BigQuery, Postgres), Terraform, Bazel/Buck, Docker, LLVM, Google ADK" },
  { label = "Skills", value = "Fuzzing, Program Analysis, Secure SDLC, Vulnerability Discovery, Network and System Security, Access Control (RBAC), LLM Agents" },
]

[[extra.experience]]
title = "Principal Engineer"
org = "Palo Alto Networks"
location = "Santa Clara, CA"
start = "Aug 2024"
end = "Present"
summary = "Program analysis, developer tooling, and LLM-agent platforms for network security products."

[[extra.experience]]
title = "Backend Software Engineer (Senior)"
org = "ByteDance"
location = "San Jose, CA"
start = "Jan 2023"
end = "Aug 2024"
summary = "Large-scale security incident detection and analysis infrastructure."

[[extra.experience]]
title = "Research Scientist"
org = "Meta"
location = "Menlo Park, CA"
start = "Oct 2022"
end = "Jan 2023"
summary = "Security and fuzzing research."

[[extra.experience]]
title = "Software Engineer Intern, Product Security"
org = "Facebook"
location = "Remote"
start = "Jun 2021"
end = "Aug 2021"
summary = "Large-scale fuzzing and automated vulnerability discovery for C/C++ codebases."

[[extra.projects]]
name = "Whole Program LLVM in Rust"
org = "rllvm"
start = "May 2022"
end = "Present"
url = "https://github.com/h1994st/rllvm"
link_text = "github.com/h1994st/rllvm"
summary = "A drop-in Rust replacement for wllvm/gllvm that extracts whole-program LLVM bitcode from any build, with source-level queries for coding agents through an MCP server and a Claude Code plugin."

[[extra.projects]]
name = "A Flexible Grammar Mutator"
org = "AFL++, Google Summer of Code 2020"
start = "Jun 2020"
end = "Present"
url = "https://github.com/AFLplusplus/Grammar-Mutator"
link_text = "github.com/AFLplusplus/Grammar-Mutator"
summary = "A grammar mutator for AFL++ with tree-based mutation and trimming for structured-input fuzzing."

[[extra.education]]
org = "University of Michigan"
location = "Ann Arbor, MI"
degree = "Ph.D. in Computer Science and Engineering"
start = "Aug 2017"
end = "Sep 2022"
dissertation = "Securing Connected and Automated Vehicle through Proactive Vulnerability Analysis and Security Enhancement"

[[extra.education]]
org = "University of Michigan"
location = "Ann Arbor, MI"
degree = "M.S. in Computer Science and Engineering"
start = "Aug 2017"
end = "Apr 2022"

[[extra.education]]
org = "Tongji University"
location = "Shanghai, China"
degree = "B.Eng. in Software Engineering"
start = "Sep 2012"
end = "Jul 2016"

[[extra.publications]]
title = "A method, device, equipment, medium and product for processing alarm events"
authors = "Weifeng Peng, Shengtuo Hu, Xiaowei Chen, Zhaoshuo Bi, Yunzhe Liu, and Jin Zhong"
venue = "Patent CN119537159A, 2025"

[[extra.publications]]
title = "On Adversarial Robustness of Trajectory Prediction for Autonomous Vehicles"
authors = "Qingzhao Zhang, Shengtuo Hu, Jiachen Sun, Qi Alfred Chen, and Z. Morley Mao"
venue = "IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR 2022)"
links = [
  { label = "Paper", url = "https://openaccess.thecvf.com/content/CVPR2022/papers/Zhang_On_Adversarial_Robustness_of_Trajectory_Prediction_for_Autonomous_Vehicles_CVPR_2022_paper.pdf" },
  { label = "arXiv", url = "https://arxiv.org/pdf/2201.05057.pdf" },
  { label = "Code", url = "https://github.com/zqzqz/AdvTrajectoryPrediction" },
]

[[extra.publications]]
title = "Gatekeeper: A Gateway-based Broadcast Authentication Protocol for the In-Vehicle Ethernet"
authors = "Shengtuo Hu, Qingzhao Zhang, André Weimerskirch, and Z. Morley Mao"
venue = "ACM ASIA Conference on Computer and Communications Security (AsiaCCS 2022)"
links = [
  { label = "Paper", url = "https://dl.acm.org/doi/10.1145/3488932.3517396" },
  { label = "Code", url = "https://github.com/h1994st/Gatekeeper" },
]

[[extra.publications]]
title = "Automated Discovery of Denial-of-Service Vulnerabilities in Connected Vehicle Protocols"
authors = "Shengtuo Hu, Qi Alfred Chen, Jiachen Sun, Yiheng Feng, Z. Morley Mao, and Henry X. Liu"
venue = "USENIX Security Symposium (USENIX Security 2021)"
links = [
  { label = "Website", url = "https://sites.google.com/view/cav-sec/cvanalyzer" },
  { label = "Paper", url = "https://www.usenix.org/system/files/sec21-hu-shengtuo.pdf" },
  { label = "Slides", url = "https://www.usenix.org/system/files/sec21_slides_hu-shengtuo.pdf" },
]

[[extra.publications]]
title = "CVShield: Guarding Sensor Data in Connected Vehicle with Trusted Execution Environment"
authors = "Shengtuo Hu, Qi Alfred Chen, Jiwon Joung, Can Carlak, Yiheng Feng, Z. Morley Mao, and Henry X. Liu"
venue = "ACM Workshop on Automotive Cybersecurity (AutoSec@CODASPY 2020)"
award = "Best Paper Award"
links = [
  { label = "Paper", url = "https://dl.acm.org/doi/10.1145/3375706.3380552" },
]

[[extra.publications]]
title = "CommPact: Evaluating the Feasibility of Autonomous Vehicle Contracts"
authors = "Jeremy Erickson, Shibo Chen, Mel Savich, Shengtuo Hu, and Z. Morley Mao"
venue = "IEEE Vehicular Networking Conference (VNC 2018)"
links = [
  { label = "Paper", url = "https://ieeexplore.ieee.org/document/8628319" },
  { label = "Code", url = "https://github.com/jericks-umich/commpact" },
]

[[extra.publications]]
title = "AutoFlowLeaker: Circumventing Web Censorship through Automation Services"
authors = "Shengtuo Hu, Xiaobo Ma, Muhui Jiang, Xiapu Luo, and Man Ho Au"
venue = "IEEE International Symposium on Reliable Distributed Systems (SRDS 2017)"
links = [
  { label = "Paper", url = "https://ieeexplore.ieee.org/document/8069084" },
  { label = "Code", url = "https://github.com/h1994st/AutoFlowLeaker" },
]

[[extra.publications]]
title = "Are HTTP/2 Servers Ready Yet?"
authors = "Muhui Jiang, Xiapu Luo, TungNgai Miu, Shengtuo Hu, and Weixiong Rao"
venue = "IEEE International Conference on Distributed Computing Systems (ICDCS 2017)"
links = [
  { label = "Paper", url = "https://ieeexplore.ieee.org/document/7980103" },
  { label = "Code", url = "https://github.com/valour01/H2Scope" },
]

[[extra.service]]
text = "Vehicle Security and Privacy (VehicleSec) Technical Program Committee"
years = "2024–2026"

[[extra.service]]
text = "USENIX Security Artifact Evaluation Committee"
years = "2022–2026"

[[extra.service]]
text = "Cyber Security in Cars Workshop (CSCS) Program Committee"
years = "2025"

[[extra.service]]
text = "IEEE Transactions on Network and Service Management (TNSM) Reviewer"
years = "2026"

[[extra.service]]
text = "IEEE Transactions on Dependable and Secure Computing (TDSC) Reviewer"
years = "2024–2026"

[[extra.service]]
text = "IEEE Transactions on Intelligent Transportation Systems (ITS) Reviewer"
years = "2024–2026"

[[extra.service]]
text = "IEEE/ACM Transactions on Networking (ToN) Reviewer"
years = "2024–2025"

[[extra.service]]
text = "ACM Multimedia (MM) Reviewer"
years = "2024"

[[extra.service]]
text = "Privacy Enhancing Technologies Symposium (PETS) External Reviewer"
years = "2022"

[[extra.service]]
text = "UMich Multidisciplinary Design Program (MDP) Undergraduate Supervisor"
years = "2021–2022"

[[extra.honors]]
text = "AutoSec Workshop Best Paper Award"
years = "2020"

[[extra.honors]]
text = "Shanghai Excellent Graduate, Shanghai Municipal Education Commission (top 5%)"
years = "2016"

[[extra.honors]]
text = "Google Excellence Scholarship, Google (top 58 students nationwide in China)"
years = "2015"

[[extra.honors]]
text = "National Scholarship, Ministry of Education, China (top 0.2% nationwide)"
years = "2013, 2014"
+++
