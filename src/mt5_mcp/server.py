import mcp.server.stdio
from mcp.server import Server
from mcp.types import Tool, TextContent, EmbeddedResource
from .backend.mock import MockBackend
from .backend.live import LiveBackend
from .config import settings

server = Server("mt5-mcp")

def get_backend():
    if settings.mode == "live":
        return LiveBackend()
    return MockBackend()

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_account_info",
            description="Get current trading account details",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_symbol_info",
            description="Get trading constraints for a symbol (digits, lot step, min/max lot)",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Trading symbol (e.g., EURUSD)"}
                },
                "required": ["symbol"]
            }
        ),
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent]:
    backend = get_backend()
    
    if name == "get_account_info":
        info = await backend.get_account_info()
        return [TextContent(type="text", text=str(info))]
    
    elif name == "get_symbol_info":
        symbol = arguments.get("symbol")
        if not symbol:
            return [TextContent(type="text", text="Error: Missing symbol argument")]
        
        info = await backend.get_symbol_info(symbol)
        if not info:
            return [TextContent(type="text", text=f"Error: Symbol {symbol} not found")]
            
        return [TextContent(type="text", text=str(info))]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )
