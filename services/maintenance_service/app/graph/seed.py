"""工业空压机 Neo4j Mock 图谱的幂等初始化。"""

from .client import graph_driver


async def initialize_knowledge_graph() -> None:
    """使用固定标签和参数化属性，重复执行不会创建重复节点或关系。"""

    async with graph_driver() as driver:
        async with driver.session() as session:
            await session.run(
                "UNWIND $items AS item MERGE (:DeviceModel {name: item.name})",
                {
                    "items": [
                        {"name": "AC-Model-A"},
                        {"name": "AC-Model-B"},
                        {"name": "AC-Model-C"},
                    ]
                },
            )
            await session.run(
                """
                UNWIND $items AS item
                MERGE (device:Device {code: item.code})
                ON CREATE SET device.name = item.name
                WITH device, item
                MATCH (model:DeviceModel {name: item.model})
                MERGE (device)-[:INSTANCE_OF]->(model)
                """,
                {
                    "items": [
                        {"code": "AC-001", "name": "一号空压机", "model": "AC-Model-A"},
                        {"code": "AC-002", "name": "二号空压机", "model": "AC-Model-A"},
                        {"code": "AC-003", "name": "三号空压机", "model": "AC-Model-B"},
                        {"code": "AC-004", "name": "四号空压机", "model": "AC-Model-B"},
                        {"code": "AC-005", "name": "五号空压机", "model": "AC-Model-C"},
                        {"code": "AC-006", "name": "六号空压机", "model": "AC-Model-C"},
                    ]
                },
            )
            await session.run(
                """
                UNWIND $items AS item
                MERGE (component:Component {name: item.component})
                WITH component, item
                MATCH (device:Device {code: item.device_code})
                MERGE (device)-[:CONTAINS]->(component)
                """,
                {
                    "items": [
                        {"device_code": "AC-001", "component": "冷却风扇"},
                        {"device_code": "AC-001", "component": "润滑系统"},
                        {"device_code": "AC-002", "component": "排气阀"},
                    ]
                },
            )
            await session.run(
                """
                UNWIND $items AS item
                MERGE (symptom:FaultSymptom {name: item.symptom})
                MERGE (cause:FaultCause {name: item.cause})
                MERGE (action:MaintenanceAction {name: item.action})
                MERGE (sop:SOP {name: item.sop})
                MERGE (notice:SafetyNotice {name: item.notice})
                MERGE (symptom)-[:MAY_BE_CAUSED_BY]->(cause)
                MERGE (cause)-[:SOLVED_BY]->(action)
                MERGE (action)-[:REFER_TO]->(sop)
                MERGE (action)-[:REQUIRES]->(notice)
                """,
                {
                    "items": [
                        {
                            "symptom": "温度过高",
                            "cause": "冷却风扇效率下降",
                            "action": "检查并清洁冷却风扇",
                            "sop": "空压机停机检查 SOP",
                            "notice": "停机、泄压并执行上锁挂牌后再检查",
                        },
                        {
                            "symptom": "排气压力异常",
                            "cause": "排气阀磨损",
                            "action": "检查排气阀并按手册更换",
                            "sop": "排气系统检查 SOP",
                            "notice": "确认压力归零，佩戴防护用品",
                        },
                        {
                            "symptom": "振动异常",
                            "cause": "联轴器松动",
                            "action": "检查联轴器紧固状态",
                            "sop": "机械传动检查 SOP",
                            "notice": "禁止在设备运行时接触旋转部件",
                        },
                    ]
                },
            )
            await session.run(
                """
                UNWIND $items AS item
                MERGE (case:MaintenanceCase {name: item.name})
                WITH case, item
                MATCH (model:DeviceModel {name: item.model})
                MATCH (symptom:FaultSymptom {name: item.symptom})
                MERGE (case)-[:APPLIES_TO]->(model)
                MERGE (case)-[:ADDRESSES]->(symptom)
                """,
                {
                    "items": [
                        {"name": "夏季高温案例", "model": "AC-Model-A", "symptom": "温度过高"},
                        {"name": "阀门磨损案例", "model": "AC-Model-B", "symptom": "排气压力异常"},
                    ]
                },
            )
