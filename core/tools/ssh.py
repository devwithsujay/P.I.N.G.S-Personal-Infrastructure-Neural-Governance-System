import logging
import asyncio
from typing import Any, Dict, Optional

import paramiko

from core.config import settings
from core.tools.base import BaseTool

logger = logging.getLogger("pings.tools.ssh")


async def get_ssh_config_from_db() -> Dict[str, Any]:
    from core.memory.db import get_setting
    host = await get_setting("SSH_HOST") or settings.SSH_HOST
    port = await get_setting("SSH_PORT") or str(settings.SSH_PORT)
    user = await get_setting("SSH_USER") or settings.SSH_USER
    auth_type = await get_setting("SSH_AUTH_TYPE") or settings.SSH_AUTH_TYPE
    key_path = await get_setting("SSH_KEY_PATH") or settings.SSH_KEY_PATH
    password = await get_setting("SSH_PASSWORD") or settings.SSH_PASSWORD
    return {
        "host": host,
        "port": int(port),
        "user": user,
        "auth_type": auth_type,
        "key_path": key_path,
        "password": password,
    }


async def run_ssh_command(command: str) -> str:
    config = await get_ssh_config_from_db()
    return await asyncio.get_event_loop().run_in_executor(
        None, _run_ssh_sync, command, config
    )


def _run_ssh_sync(command: str, config: Dict[str, Any]) -> str:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        connect_kwargs: Dict[str, Any] = {
            "hostname": config.get("host", settings.SSH_HOST),
            "port": int(config.get("port", settings.SSH_PORT)),
            "username": config.get("user", settings.SSH_USER),
            "timeout": 15,
        }
        auth_type = config.get("auth_type", settings.SSH_AUTH_TYPE)
        if auth_type == "key":
            key_path = config.get("key_path", settings.SSH_KEY_PATH)
            connect_kwargs["key_filename"] = key_path
        else:
            connect_kwargs["password"] = config.get("password", settings.SSH_PASSWORD)

        client.connect(**connect_kwargs)
        stdin, stdout, stderr = client.exec_command(command, timeout=30)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")

        if exit_code != 0:
            result = f"[exit {exit_code}]\n{err}\n{out}"
        else:
            result = out if out else err
        return result.strip()
    except paramiko.AuthenticationException:
        return "[SSH Error] Authentication failed. Check credentials."
    except paramiko.SSHException as e:
        return f"[SSH Error] {str(e)}"
    except Exception as e:
        return f"[SSH Error] Connection failed: {str(e)}"
    finally:
        client.close()


async def test_ssh_connection(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if config is None:
        config = await get_ssh_config_from_db()
    return await asyncio.get_event_loop().run_in_executor(
        None, _test_ssh_sync, config
    )


def _test_ssh_sync(config: Dict[str, Any]) -> Dict[str, Any]:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        connect_kwargs: Dict[str, Any] = {
            "hostname": config.get("host", settings.SSH_HOST),
            "port": int(config.get("port", settings.SSH_PORT)),
            "username": config.get("user", settings.SSH_USER),
            "timeout": 10,
        }
        auth_type = config.get("auth_type", settings.SSH_AUTH_TYPE)
        if auth_type == "key":
            key_path = config.get("key_path", settings.SSH_KEY_PATH)
            connect_kwargs["key_filename"] = key_path
        else:
            connect_kwargs["password"] = config.get("password", settings.SSH_PASSWORD)

        client.connect(**connect_kwargs)
        stdin, stdout, stderr = client.exec_command("hostname && uptime", timeout=10)
        output = stdout.read().decode("utf-8", errors="replace").strip()
        return {"success": True, "status": "connected", "info": output}
    except Exception as e:
        return {"success": False, "status": "failed", "error": str(e)}
    finally:
        client.close()


class SshTool(BaseTool):
    name = "ssh"
    description = "Execute SSH commands on the remote server"
    trigger_patterns = ["ssh", "server", "remote", "execute on", "run on host"]
    priority = 50

    async def run(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        command = message
        for prefix in ["ssh ", "execute ", "run on server ", "run on host ", "remote "]:
            if message.lower().startswith(prefix):
                command = message[len(prefix):]
                break
        logger.info(f"SSH tool executing: {command[:100]}")
        result = await run_ssh_command(command)
        return result
