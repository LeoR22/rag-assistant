import os
from typing import Any
from loguru import logger
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()


class McpConnector:
    """
    Conecta el agente al servidor MCP via Streamable HTTP.
    Usa langchain-mcp-adapters para integrar las tools MCP con LangGraph.
    """

    def __init__(self):
        self._server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp")
        logger.success(f"McpConnector inicializado — servidor: {self._server_url}")

    async def get_tools(self) -> list:
        """Obtiene las tools disponibles del servidor MCP"""
        async with MultiServerMCPClient(
            {
                "bancolombia": {
                    "url": self._server_url,
                    "transport": "streamable_http",
                }
            }
        ) as client:
            tools = client.get_tools()
            logger.info(f"Tools MCP disponibles: {[t.name for t in tools]}")
            return tools

    def get_client_config(self) -> dict:
        """Retorna la configuración del cliente MCP para LangGraph"""
        return {
            "bancolombia": {
                "url": self._server_url,
                "transport": "streamable_http",
            }
        }