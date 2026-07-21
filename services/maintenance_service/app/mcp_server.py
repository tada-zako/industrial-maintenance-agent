"""FastMCP 服务入口；具体工具将在阶段二按共享 domain 服务逐步接入。"""

from fastmcp import FastMCP

mcp = FastMCP(
    name="maintenance-service",
    instructions=(
        "工业空压机运维工具服务。工具只提供查询、维修方案草案和工作流记录，"
        "不执行真实设备控制。"
    ),
)


def run() -> None:
    """启动 FastMCP；传输方式和挂载方式在 Hermes 联调阶段确定。"""

    mcp.run()


if __name__ == "__main__":
    run()
