from __future__ import annotations
from typing import Any


PROMPTS: dict[str, Any] = {}

PROMPTS["DEFAULT_LANGUAGE"] = "English"
PROMPTS["DEFAULT_TUPLE_DELIMITER"] = "<|>"
PROMPTS["DEFAULT_RECORD_DELIMITER"] = "##"
PROMPTS["DEFAULT_COMPLETION_DELIMITER"] = "<|COMPLETE|>"

PROMPTS["DEFAULT_ENTITY_TYPES"] = ["项目基本信息", "空间位置", "时间安排", "资源设施", "规范要求", "风险因素", "缓解措施", "关联项目"]

PROMPTS["DEFAULT_USER_PROMPT"] = "n/a"

PROMPTS["entity_extraction"] = """---Goal---
You are an expert in construction project management and documentation analysis. Your goal is to analyze individual construction project documents to extract standardized, structured information that can be used for future multi-project coordination and analysis.
Given a text document and a list of entity types, identify all entities and their relationships within the single project. Focus on extracting comprehensive project information including technical specifications, resource requirements, construction methods, regulatory compliance, safety measures, and cost details in a standardized format.
Use {language} as output language.

---Steps---
1. Identify all entities. For each identified entity, extract the following information:
- entity_name: Name of the entity, use same language as input text. If English, capitalized the name.
- entity_type: One of the following types: [{entity_types}]
- entity_description: Structured description focusing on rule-relevant attributes. For each entity type, include:
  * 项目基本信息: project name, type, scope, objectives, stakeholders
  * 空间位置: specific locations, coordinates, boundaries, distances, overlaps with other areas
  * 时间安排: start/end dates, durations, phases, schedules, deadlines, dependencies
  * 资源设施: equipment, materials, infrastructure, capacity, availability, shared resources
  * 规范要求: applicable standards, regulations, compliance requirements, approval status
  * 风险因素: safety risks, environmental impacts, regulatory risks, potential conflicts
  * 缓解措施: risk mitigation strategies, protective measures, monitoring systems
  * 关联项目: related projects, dependencies, coordination requirements, potential conflicts

**Time Format Requirements**: When describing temporal information, use standardized formats:
- Dates: YYYY-MM-DD (e.g., "2024-03-15")
- Date ranges: YYYY-MM-DD to YYYY-MM-DD (e.g., "2024-03-15 to 2024-12-31")  
- Duration: X months/weeks/days (e.g., "18 months", "3 weeks", "45 days")
- Time periods: HH:MM-HH:MM (e.g., "08:00-18:00", "22:00-06:00")
- Phases: Phase name (start_date to end_date) (e.g., "基坑开挖阶段 (2024-07-01 to 2024-09-30)")

Format each entity as ("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>)

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other
- relationship_strength: a numeric score indicating strength of the relationship between the source entity and target entity
- relationship_keywords: standardized relationship types from four categories:
  * 空间关系: 位于, 邻近, 重叠, 距离, 包含, 跨越
  * 时间关系: 先于, 并行, 冲突, 依赖, 同期, 延续
  * 合规关系: 符合, 违反, 需要, 缺少, 要求, 批准
  * 资源关系: 共享, 竞争, 依赖, 冲突, 使用, 占用
  Choose the most appropriate relationship type(s) that best describe the connection between entities.
Format each relationship as ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_keywords>{tuple_delimiter}<relationship_strength>)

3. Identify high-level key words that summarize the main concepts, themes, or topics of the entire text. These should capture the overarching ideas present in the document.
Format the content-level key words as ("content_keywords"{tuple_delimiter}<high_level_keywords>)

4. Return output in {language} as a single list of all the entities and relationships identified in steps 1 and 2. Use **{record_delimiter}** as the list delimiter.

5. When finished, output {completion_delimiter}

######################
---Examples---
######################
{examples}

#############################
---Real Data---
######################
Entity_types: [{entity_types}]
Text:
{input_text}
######################
Output:"""

PROMPTS["entity_extraction_examples"] = [
    """Example 1:

Entity_types: [项目基本信息, 空间位置, 时间安排, 资源设施, 规范要求, 风险因素, 缓解措施, 关联项目]
Text:
```
本基坑工程紧邻运营中的地铁2号线，为确保万无一失，依据《建筑基坑支护技术规程》JGJ 120-2012，采用800mm厚地下连续墙作为支护结构。施工中最大的风险是基坑开挖可能导致地铁隧道上浮，因此，必须在隧道内设置多点自动化应力监测计，24小时监控，确保其隆起值不超过5mm。此项监测措施的专项费用为80万元。项目总工期为18个月，其中基坑开挖阶段计划用时3个月，需使用2台大型挖掘机和1台旋挖钻机。地下连续墙采用C35防水混凝土，钢筋保护层厚度不小于50mm。
```

Output:
("entity"{tuple_delimiter}"基坑工程项目"{tuple_delimiter}"项目基本信息"{tuple_delimiter}"本项目为基坑支护工程，紧邻地铁2号线，总工期18个月，主要目标是确保基坑稳定和地铁运营安全。"){record_delimiter}
("entity"{tuple_delimiter}"紧邻地铁2号线位置"{tuple_delimiter}"空间位置"{tuple_delimiter}"工程位置紧邻运营中的地铁2号线，空间距离极近，存在相互影响的风险，是项目的核心空间约束条件。"){record_delimiter}
("entity"{tuple_delimiter}"项目总工期和开挖阶段"{tuple_delimiter}"时间安排"{tuple_delimiter}"项目总工期为18 months，其中基坑开挖阶段计划用时3 months，时间安排紧凑，是风险控制的重点时期。"){record_delimiter}
("entity"{tuple_delimiter}"支护设备和监测设备"{tuple_delimiter}"资源设施"{tuple_delimiter}"包括800mm厚地下连续墙、2台大型挖掘机、1台旋挖钻机、多点自动化应力监测计，设备配置完整，监测专项费用80万元。"){record_delimiter}
("entity"{tuple_delimiter}"《建筑基坑支护技术规程》JGJ 120-2012"{tuple_delimiter}"规范要求"{tuple_delimiter}"项目选择支护技术和施工的直接法规依据，规定了基坑支护的技术要求和安全标准，隆起值控制不超过5mm。"){record_delimiter}
("entity"{tuple_delimiter}"地铁隧道上浮风险"{tuple_delimiter}"风险因素"{tuple_delimiter}"基坑开挖可能引起的邻近隧道隆起变形，是施工期间的主要安全风险，若处理不当可能导致地铁运营安全问题。"){record_delimiter}
("entity"{tuple_delimiter}"自动化应力监测系统"{tuple_delimiter}"缓解措施"{tuple_delimiter}"针对隧道上浮风险采取的关键控制措施，通过24小时监控来预警，确保施工过程中隧道变形在安全范围内。"){record_delimiter}
("entity"{tuple_delimiter}"地铁2号线运营"{tuple_delimiter}"关联项目"{tuple_delimiter}"正在运营的地铁线路，与本基坑工程存在空间邻近关系，需要协调确保其运营安全不受影响。"){record_delimiter}
("relationship"{tuple_delimiter}"支护设备和监测设备"{tuple_delimiter}"《建筑基坑支护技术规程》JGJ 120-2012"{tuple_delimiter}"支护设备的设计和配置严格遵循JGJ 120-2012规范的要求，确保支护结构的安全性和有效性。"{tuple_delimiter}"符合"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"自动化应力监测系统"{tuple_delimiter}"地铁隧道上浮风险"{tuple_delimiter}"自动化监测系统专门用于监控和应对地铁隧道的上浮风险，是关键的风险控制措施。"{tuple_delimiter}"缓解"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"紧邻地铁2号线位置"{tuple_delimiter}"基坑工程项目"{tuple_delimiter}"基坑工程位置紧邻地铁2号线，空间距离极近，存在直接的空间影响关系。"{tuple_delimiter}"邻近"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"项目总工期和开挖阶段"{tuple_delimiter}"地铁隧道上浮风险"{tuple_delimiter}"基坑开挖阶段是隧道上浮风险的高发时期，时间安排需要特别关注风险控制。"{tuple_delimiter}"同期"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"支护设备和监测设备"{tuple_delimiter}"地铁2号线运营"{tuple_delimiter}"支护和监测设备共同使用空间资源，需要协调确保不影响地铁正常运营。"{tuple_delimiter}"共享"{tuple_delimiter}7){record_delimiter}
("content_keywords"{tuple_delimiter}"基坑支护, 地铁保护, 安全监测, 风险控制, 施工技术, 合规性"){completion_delimiter}
#############################""",
    """Example 2:

Entity_types: [项目基本信息, 空间位置, 时间安排, 资源设施, 规范要求, 风险因素, 缓解措施, 关联项目]
Text:
```
某大型商业综合体项目地下室采用逆作法施工，总建筑面积约12万平方米，地下四层，基坑深度18米。由于周边200米范围内有三栋历史保护建筑，根据《历史文化名城保护条例》要求，基坑开挖过程中需控制周边建筑物沉降变形小于10mm。施工方案采用SMW工法桩+内支撑体系，工法桩直径850mm，C30防水混凝土，钢筋HRB400。为监控周边建筑物变形，设置了全自动监测系统，包括16个沉降监测点和24个倾斜监测点，监测费用为56万元。地下室防水等级为一级，采用1.5mm厚HDPE防水卷材+防水混凝土的复合防水措施。整个地下结构工期为10个月，其中逆作法施工的主要风险是支撑体系稳定性和地下水控制。
```

Output:
("entity"{tuple_delimiter}"商业综合体地下室项目"{tuple_delimiter}"项目基本信息"{tuple_delimiter}"大型商业综合体地下室工程，总建筑面积约12万平方米，地下四层，基坑深度18米，采用逆作法施工，工期10个月。"){record_delimiter}
("entity"{tuple_delimiter}"周边历史保护建筑区域"{tuple_delimiter}"空间位置"{tuple_delimiter}"项目周边200米范围内有三栋历史保护建筑，对基坑变形控制提出了严格的空间约束要求。"){record_delimiter}
("entity"{tuple_delimiter}"地下结构施工时间安排"{tuple_delimiter}"时间安排"{tuple_delimiter}"整个地下结构施工计划的时间周期为10 months，逆作法施工是主要的施工阶段，需要严格控制进度。"){record_delimiter}
("entity"{tuple_delimiter}"SMW工法桩支护系统"{tuple_delimiter}"资源设施"{tuple_delimiter}"包括SMW工法桩（直径850mm）、内支撑体系、C30防水混凝土、HRB400钢筋，以及全自动监测系统（16个沉降监测点和24个倾斜监测点），监测费用56万元。"){record_delimiter}
("entity"{tuple_delimiter}"《历史文化名城保护条例》"{tuple_delimiter}"规范要求"{tuple_delimiter}"规定了在历史文化保护区内施工的相关要求，要求沉降变形控制小于10mm，是本项目必须遵守的法规标准。"){record_delimiter}
("entity"{tuple_delimiter}"支撑体系稳定性和地下水控制风险"{tuple_delimiter}"风险因素"{tuple_delimiter}"逆作法施工过程中的主要风险，包括支撑失效、基坑坍塌、涌水、流砂等问题，影响施工安全和质量。"){record_delimiter}
("entity"{tuple_delimiter}"全自动监测和防水措施"{tuple_delimiter}"缓解措施"{tuple_delimiter}"为监控周边建筑物变形设置的监测系统，以及采用1.5mm厚HDPE防水卷材+防水混凝土的复合防水措施，确保一级防水等级。"){record_delimiter}
("entity"{tuple_delimiter}"周边历史保护建筑"{tuple_delimiter}"关联项目"{tuple_delimiter}"周边200米范围内的三栋历史保护建筑，与本项目存在空间邻近关系，需要协调确保其安全不受影响。"){record_delimiter}
("relationship"{tuple_delimiter}"SMW工法桩支护系统"{tuple_delimiter}"《历史文化名城保护条例》"{tuple_delimiter}"支护系统的设计和施工严格遵循历史文化名城保护条例的要求，确保沉降变形控制在10mm以内。"{tuple_delimiter}"符合"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"周边历史保护建筑区域"{tuple_delimiter}"商业综合体地下室项目"{tuple_delimiter}"项目位于历史保护建筑200米范围内，存在直接的空间约束关系。"{tuple_delimiter}"邻近"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"全自动监测和防水措施"{tuple_delimiter}"支撑体系稳定性和地下水控制风险"{tuple_delimiter}"监测和防水措施专门用于应对支撑体系稳定性和地下水控制风险，是关键的风险控制手段。"{tuple_delimiter}"缓解"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"地下结构施工时间安排"{tuple_delimiter}"支撑体系稳定性和地下水控制风险"{tuple_delimiter}"逆作法施工期间是支撑体系稳定性和地下水控制风险的高发时期，需要严格的时间管理。"{tuple_delimiter}"同期"{tuple_delimiter}8){record_delimiter}
("content_keywords"{tuple_delimiter}"逆作法施工, 历史建筑保护, 基坑支护, 变形控制, 安全监测, 防水技术"){completion_delimiter}
#############################""",
    """Example 3:

Entity_types: [项目基本信息, 空间位置, 时间安排, 资源设施, 规范要求, 风险因素, 缓解措施, 关联项目]
Text:
```
某开发区内有三个同期施工的建设项目：A栋办公楼（2024年3月-12月）、B栋商业楼（2024年5月-2025年2月）、C栋住宅楼（2024年7月-2025年4月）。三个项目均位于距离主干道200米范围内，共用一条施工便道，每日运输车辆总计约150车次。A、B两项目距离仅50米，施工高峰期（7-9月）将同时进行土方开挖作业，预计产生的噪音叠加将达到85分贝，超出《建筑施工场界环境噪音排放标准》75分贝的限制。项目群共需租用8台塔吊，但当地设备租赁公司仅能提供6台，存在2台的缺口。为减少对周边居民区的影响，三个项目协调后决定：A、C项目的混凝土浇筑作业避开22:00-6:00时段，B项目承担夜间应急浇筑任务。三个项目的渣土清运将统一委托给同一家公司，预计可节省15%的运输成本。
```

Output:
("entity"{tuple_delimiter}"A栋办公楼项目"{tuple_delimiter}"项目基本信息"{tuple_delimiter}"办公楼建设项目，施工期为2024-03-01 to 2024-12-31，位于距离主干道200米范围内，与B项目距离仅50米，参与项目群协调管理。"){record_delimiter}
("entity"{tuple_delimiter}"B栋商业楼项目"{tuple_delimiter}"项目基本信息"{tuple_delimiter}"商业楼建设项目，施工期为2024-05-01 to 2025-02-28，与A项目邻近（距离50米），承担夜间应急浇筑任务。"){record_delimiter}
("entity"{tuple_delimiter}"C栋住宅楼项目"{tuple_delimiter}"项目基本信息"{tuple_delimiter}"住宅楼建设项目，施工期为2024-07-01 to 2025-04-30，位于项目群内，参与协调统一的渣土清运。"){record_delimiter}
("entity"{tuple_delimiter}"开发区主干道200米范围"{tuple_delimiter}"空间位置"{tuple_delimiter}"三个项目共同所在的空间区域，以距离主干道200米为界限，A、B两项目距离仅50米，存在空间邻近关系。"){record_delimiter}
("entity"{tuple_delimiter}"施工高峰期和夜间协调安排"{tuple_delimiter}"时间安排"{tuple_delimiter}"施工高峰期（2024-07-01 to 2024-09-30）A、B项目同时土方开挖，夜间协调安排A、C项目避开22:00-06:00浇筑，B项目承担夜间应急任务。"){record_delimiter}
("entity"{tuple_delimiter}"塔吊和运输设备资源"{tuple_delimiter}"资源设施"{tuple_delimiter}"项目群共需8台塔吊但仅能提供6台存在缺口，共用施工便道承载每日150车次运输，统一渣土清运可节省15%成本。"){record_delimiter}
("entity"{tuple_delimiter}"《建筑施工场界环境噪音排放标准》"{tuple_delimiter}"规范要求"{tuple_delimiter}"规定建筑施工环境噪音限制为75分贝，A、B项目同时施工的噪音叠加85分贝超出此标准要求。"){record_delimiter}
("entity"{tuple_delimiter}"噪音叠加和设备资源冲突"{tuple_delimiter}"风险因素"{tuple_delimiter}"A、B项目同时土方开挖产生85分贝噪音叠加超标，塔吊设备缺口2台形成资源瓶颈，影响项目群协调。"){record_delimiter}
("entity"{tuple_delimiter}"夜间施工协调和统一清运"{tuple_delimiter}"缓解措施"{tuple_delimiter}"A、C项目避开22:00-06:00浇筑，B项目承担夜间应急任务，统一渣土清运节省15%成本。"){record_delimiter}
("entity"{tuple_delimiter}"周边居民区和相邻项目"{tuple_delimiter}"关联项目"{tuple_delimiter}"周边居民区受到噪音影响，A、B、C三个项目相互关联，需要协调确保不产生叠加影响。"){record_delimiter}
("relationship"{tuple_delimiter}"A栋办公楼项目"{tuple_delimiter}"B栋商业楼项目"{tuple_delimiter}"两个项目距离仅50米，在施工高峰期同时进行土方开挖，存在直接的空间相互影响。"{tuple_delimiter}"邻近"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"施工高峰期和夜间协调安排"{tuple_delimiter}"噪音叠加和设备资源冲突"{tuple_delimiter}"在施工高峰期，A、B项目同时土方开挖导致噪音叠加和设备资源冲突，需要时间协调来缓解。"{tuple_delimiter}"同期"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"噪音叠加和设备资源冲突"{tuple_delimiter}"《建筑施工场界环境噪音排放标准》"{tuple_delimiter}"项目群产生的噪音叠加水平超出了国家环保标准的限制要求，构成合规性问题。"{tuple_delimiter}"违反"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"塔吊和运输设备资源"{tuple_delimiter}"A栋办公楼项目"{tuple_delimiter}"三个项目对塔吊设备的总需求超过了当地供应能力，形成资源竞争和供应瓶颈。"{tuple_delimiter}"竞争"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"夜间施工协调和统一清运"{tuple_delimiter}"噪音叠加和设备资源冲突"{tuple_delimiter}"通过时间协调和统一清运方案，来缓解噪音叠加对周边居民的影响和资源冲突问题。"{tuple_delimiter}"缓解"{tuple_delimiter}7){record_delimiter}
("content_keywords"{tuple_delimiter}"项目群协同, 资源共享, 环境影响叠加, 时空冲突, 成本优化, 施工协调"){completion_delimiter}
#############################""",
]

PROMPTS[
    "summarize_entity_descriptions"
] = """You are a helpful assistant responsible for generating a comprehensive summary of the data provided below.
Given one or two entities, and a list of descriptions, all related to the same entity or group of entities.
Please concatenate all of these into a single, comprehensive description. Make sure to include information collected from all the descriptions.
If the provided descriptions are contradictory, please resolve the contradictions and provide a single, coherent summary.
Make sure it is written in third person, and include the entity names so we the have full context.
Use {language} as output language.

#######
---Data---
Entities: {entity_name}
Description List: {description_list}
#######
Output:
"""

PROMPTS["entity_continue_extraction"] = """
MANY entities and relationships were missed in the last extraction.

---Remember Steps---

1. Identify all entities. For each identified entity, extract the following information:
- entity_name: Name of the entity, use same language as input text. If English, capitalized the name.
- entity_type: One of the following types: [{entity_types}]
- entity_description: Comprehensive description of the entity's attributes and activities. Focus on the core technical and managerial aspects, including safety risks, compliance requirements, and cost implications. Pay special attention to temporal information (durations, schedules, deadlines), spatial relationships (locations, distances, overlaps), resource requirements, and potential impacts on other projects. Include specific quantitative data when available (distances, timeframes, capacities, thresholds).

**Time Format Requirements**: When describing temporal information, use standardized formats:
- Dates: YYYY-MM-DD (e.g., "2024-03-15")
- Date ranges: YYYY-MM-DD to YYYY-MM-DD (e.g., "2024-03-15 to 2024-12-31")  
- Duration: X months/weeks/days (e.g., "18 months", "3 weeks", "45 days")
- Time periods: HH:MM-HH:MM (e.g., "08:00-18:00", "22:00-06:00")
- Phases: Phase name (start_date to end_date) (e.g., "基坑开挖阶段 (2024-07-01 to 2024-09-30)")

Format each entity as ("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>)

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other
- relationship_strength: a numeric score indicating strength of the relationship between the source entity and target entity
- relationship_keywords: one or more high-level key words that summarize the overarching nature of the relationship, focusing on concepts or themes rather than specific details. For construction projects, consider using relationship types like COMPLIES_WITH, ADDRESSES, PAYS_FOR, DEPENDS_ON, MITIGATES, CAUSES, ENABLES, REQUIRES, ADJACENT_TO, CONCURRENT_WITH, PRECEDES, SHARES_RESOURCE, AMPLIFIES_IMPACT, BLOCKS_ACCESS, or CREATES_BOTTLENECK when appropriate.
Format each relationship as ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_keywords>{tuple_delimiter}<relationship_strength>)

3. Identify high-level key words that summarize the main concepts, themes, or topics of the entire text. These should capture the overarching ideas present in the document.
Format the content-level key words as ("content_keywords"{tuple_delimiter}<high_level_keywords>)

4. Return output in {language} as a single list of all the entities and relationships identified in steps 1 and 2. Use **{record_delimiter}** as the list delimiter.

5. When finished, output {completion_delimiter}

---Output---

Add them below using the same format:\n
""".strip()

PROMPTS["entity_if_loop_extraction"] = """
---Goal---'

It appears some entities may have still been missed.

---Output---

Answer ONLY by `YES` OR `NO` if there are still entities that need to be added.
""".strip()

PROMPTS["fail_response"] = (
    "Sorry, I'm not able to provide an answer to that question.[no-context]"
)

PROMPTS["rag_response"] = """---Role---

You are a helpful assistant responding to user query about Knowledge Graph and Document Chunks provided in JSON format below.


---Goal---

Generate a concise response based on Knowledge Base and follow Response Rules, considering both the conversation history and the current query. Summarize all information in the provided Knowledge Base, and incorporating general knowledge relevant to the Knowledge Base. Do not include information not provided by Knowledge Base.

When handling relationships with timestamps:
1. Each relationship has a "created_at" timestamp indicating when we acquired this knowledge
2. When encountering conflicting relationships, consider both the semantic content and the timestamp
3. Don't automatically prefer the most recently created relationships - use judgment based on the context
4. For time-specific queries, prioritize temporal information in the content before considering creation timestamps

---Conversation History---
{history}

---Knowledge Graph and Document Chunks---
{context_data}

---Response Rules---

- Target format and length: {response_type}
- Use markdown formatting with appropriate section headings
- Please respond in the same language as the user's question.
- Ensure the response maintains continuity with the conversation history.
- List up to 5 most important reference sources at the end under "References" section. Clearly indicating whether each source is from Knowledge Graph (KG) or Document Chunks (DC), and include the file path if available, in the following format: [KG/DC] file_path
- If you don't know the answer, just say so.
- Do not make anything up. Do not include information not provided by the Knowledge Base.
- Addtional user prompt: {user_prompt}

Response:"""

PROMPTS["keywords_extraction"] = """---Role---

You are a helpful assistant tasked with identifying both high-level and low-level keywords in the user's query and conversation history.

---Goal---

Given the query and conversation history, list both high-level and low-level keywords. High-level keywords focus on overarching concepts or themes, while low-level keywords focus on specific entities, details, or concrete terms.

---Instructions---

- Consider both the current query and relevant conversation history when extracting keywords
- Output the keywords in JSON format, it will be parsed by a JSON parser, do not add any extra content in output
- The JSON should have two keys:
  - "high_level_keywords" for overarching concepts or themes
  - "low_level_keywords" for specific entities or details

######################
---Examples---
######################
{examples}

#############################
---Real Data---
######################
Conversation History:
{history}

Current Query: {query}
######################
The `Output` should be human text, not unicode characters. Keep the same language as `Query`.
Output:

"""

PROMPTS["keywords_extraction_examples"] = [
    """Example 1:

Query: "How does international trade influence global economic stability?"
################
Output:
{
  "high_level_keywords": ["International trade", "Global economic stability", "Economic impact"],
  "low_level_keywords": ["Trade agreements", "Tariffs", "Currency exchange", "Imports", "Exports"]
}
#############################""",
    """Example 2:

Query: "What are the environmental consequences of deforestation on biodiversity?"
################
Output:
{
  "high_level_keywords": ["Environmental consequences", "Deforestation", "Biodiversity loss"],
  "low_level_keywords": ["Species extinction", "Habitat destruction", "Carbon emissions", "Rainforest", "Ecosystem"]
}
#############################""",
    """Example 3:

Query: "What is the role of education in reducing poverty?"
################
Output:
{
  "high_level_keywords": ["Education", "Poverty reduction", "Socioeconomic development"],
  "low_level_keywords": ["School access", "Literacy rates", "Job training", "Income inequality"]
}
#############################""",
]

PROMPTS["naive_rag_response"] = """---Role---

You are a helpful assistant responding to user query about Document Chunks provided provided in JSON format below.

---Goal---

Generate a concise response based on Document Chunks and follow Response Rules, considering both the conversation history and the current query. Summarize all information in the provided Document Chunks, and incorporating general knowledge relevant to the Document Chunks. Do not include information not provided by Document Chunks.

When handling content with timestamps:
1. Each piece of content has a "created_at" timestamp indicating when we acquired this knowledge
2. When encountering conflicting information, consider both the content and the timestamp
3. Don't automatically prefer the most recent content - use judgment based on the context
4. For time-specific queries, prioritize temporal information in the content before considering creation timestamps

---Conversation History---
{history}

---Document Chunks(DC)---
{content_data}

---Response Rules---

- Target format and length: {response_type}
- Use markdown formatting with appropriate section headings
- Please respond in the same language as the user's question.
- Ensure the response maintains continuity with the conversation history.
- List up to 5 most important reference sources at the end under "References" section. Clearly indicating each source from Document Chunks(DC), and include the file path if available, in the following format: [DC] file_path
- If you don't know the answer, just say so.
- Do not include information not provided by the Document Chunks.
- Addtional user prompt: {user_prompt}

Response:"""

# TODO: deprecated
PROMPTS[
    "similarity_check"
] = """Please analyze the similarity between these two questions:

Question 1: {original_prompt}
Question 2: {cached_prompt}

Please evaluate whether these two questions are semantically similar, and whether the answer to Question 2 can be used to answer Question 1, provide a similarity score between 0 and 1 directly.

Similarity score criteria:
0: Completely unrelated or answer cannot be reused, including but not limited to:
   - The questions have different topics
   - The locations mentioned in the questions are different
   - The times mentioned in the questions are different
   - The specific individuals mentioned in the questions are different
   - The specific events mentioned in the questions are different
   - The background information in the questions is different
   - The key conditions in the questions are different
1: Identical and answer can be directly reused
0.5: Partially related and answer needs modification to be used
Return only a number between 0-1, without any additional content.
"""

PROMPTS["entity_deduplication"] = """---Goal---
You are an expert at identifying whether different entity names refer to the same real-world object or concept. 
Your task is to analyze a group of potentially similar entities and determine if they should be unified under a single canonical name.

---Task---
Analyze the following entities and determine if they refer to the same real-world object:

{entity_group}

Each entity has the following information:
{entity_descriptions}

---Instructions---
1. Consider the following factors when making your decision:
   - Semantic similarity of names (e.g., "Apple Inc." vs "苹果公司")
   - Overlap in entity descriptions and attributes
   - Same entity type or closely related types
   - Context and domain knowledge

2. Be conservative: Only merge entities if you are confident they refer to the same thing
3. Consider language variations, abbreviations, and alternative names
4. Take into account the entity type - entities of very different types are unlikely to be the same

---Output Format---
Respond with the following format:
SAME_ENTITY: YES/NO
CANONICAL_NAME: [If YES, provide the most standard/official name]
REASON: [Brief explanation for your decision]

---Examples---
Example 1:
SAME_ENTITY: YES
CANONICAL_NAME: Apple Inc.
REASON: "Apple Inc.", "苹果公司", and "Apple" all refer to the same technology company, with "Apple Inc." being the official corporate name.

Example 2:
SAME_ENTITY: NO
CANONICAL_NAME: N/A
REASON: "Apple Inc." (technology company) and "Apple Store" (retail location) are related but distinct entities with different functions.

---Analysis---
Please analyze the provided entities:"""
