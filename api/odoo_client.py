"""
odoo_client.py
==============
Cliente JSON-RPC 2 de SOLO LECTURA para Odoo 19 SaaS.

Ruta única confirmada para Odoo 19 SaaS:
  - TODAS las llamadas van a POST /jsonrpc
  - Autenticación : service=common  / method=authenticate
  - Consultas     : service=object  / method=execute_kw
  - Versión       : service=common  / method=version

Principios de seguridad:
  - write/create/unlink bloqueados en Python antes de cualquier petición de red.
  - Login email + API Key en .env (nunca la contraseña real en código).
"""

import os
import logging
from typing import Any, Optional
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

ODOO_URL     = os.getenv("ODOO_URL",   "https://electriganadero.odoo.com")
ODOO_DB      = os.getenv("ODOO_DB",    "electriganadero")
ODOO_LOGIN   = os.getenv("ODOO_LOGIN", "electriganadero.apps@gmail.com")
ODOO_API_KEY = os.getenv("ODOO_API_KEY", "")
ODOO_YOLO    = os.getenv("ODOO_YOLO",  "read")

_FORBIDDEN_METHODS = frozenset({
    "write", "create", "unlink", "copy",
    "button_confirm", "button_cancel", "button_draft",
    "action_confirm", "action_cancel", "action_done",
    "post", "action_post", "reset_to_draft",
})

# ─────────────────────────────────────────────
#  Helpers de payload JSON-RPC 2
# ─────────────────────────────────────────────
_rpc_id = 0

def _next_id() -> int:
    global _rpc_id
    _rpc_id += 1
    return _rpc_id

def _rpc_payload(method: str, params: dict) -> dict:
    """Wrapper estándar JSON-RPC 2 que Odoo espera."""
    return {
        "jsonrpc": "2.0",
        "method":  method,       # siempre "call" para Odoo
        "id":      _next_id(),
        "params":  params,
    }


class OdooReadOnlyClient:
    """Cliente JSON-RPC 2 solo lectura para Odoo 19."""

    def __init__(self):
        self.url     = ODOO_URL.rstrip("/")
        self.db      = ODOO_DB
        self.login   = ODOO_LOGIN
        self.api_key = ODOO_API_KEY
        self._uid: Optional[int] = None
        self._http   = httpx.Client(timeout=30.0, follow_redirects=True)

    # ──────────────────────────────────────────
    #  Autenticación — /jsonrpc, service=common
    # ──────────────────────────────────────────
    def authenticate(self) -> int:
        """
        Autentica vía /jsonrpc con service=common / method=authenticate.
        Usa email real (ODOO_LOGIN) + API Key como contraseña.
        Confirmado funcional en Odoo 19 SaaS → devuelve UID=2.
        """
        if not self.api_key:
            raise ValueError(
                "❌ ODOO_API_KEY no configurada. "
                "Añádela al archivo backend/.env"
            )

        payload = _rpc_payload("call", {
            "service": "common",
            "method":  "authenticate",
            "args":    [self.db, self.login, self.api_key, {}],
        })

        resp = self._post("/jsonrpc", payload)
        uid  = resp.get("result")

        if not uid:
            raise ConnectionError(
                f"❌ Autenticación fallida en Odoo.\n"
                f"  • URL:   {self.url}\n"
                f"  • DB:    {self.db}\n"
                f"  • Login: {self.login}\n"
                f"  • Respuesta: {resp}"
            )

        self._uid = uid
        logger.info(f"✅ Autenticado en Odoo 19 SaaS — UID={uid}, login={self.login}")
        return uid

    # ──────────────────────────────────────────
    #  API pública de lectura
    # ──────────────────────────────────────────
    def search_read(
        self,
        model: str,
        domain: list,
        fields: list,
        limit: int = 200,
        order: str = "",
    ) -> list:
        kwargs: dict = {"fields": fields, "limit": limit}
        if order:
            kwargs["order"] = order
        return self._execute_kw(model, "search_read", [domain], kwargs)

    def read_group(self, model: str, domain: list, fields: list, groupby: list) -> list:
        return self._execute_kw(model, "read_group", [domain, fields, groupby], {"lazy": False})

    def search_count(self, model: str, domain: list) -> int:
        return self._execute_kw(model, "search_count", [domain], {})

    def fields_get(self, model: str, attributes: list = None) -> dict:
        kwargs = {}
        if attributes:
            kwargs["attributes"] = attributes
        return self._execute_kw(model, "fields_get", [], kwargs)

    # ──────────────────────────────────────────
    #  Health / ping — /jsonrpc, service=common
    # ──────────────────────────────────────────
    def version_info(self) -> dict:
        """Versión pública de Odoo — no requiere autenticación."""
        payload = _rpc_payload("call", {
            "service": "common",
            "method":  "version",
            "args":    [],
        })
        try:
            resp   = self._post("/jsonrpc", payload)
            result = resp.get("result") or {}
            return {
                "server_version":      result.get("server_version", "?"),
                "server_version_info": result.get("server_version_info", []),
            }
        except Exception as e:
            logger.warning(f"version_info falló: {e}")
            return {"server_version": None, "error": str(e)}

    # ──────────────────────────────────────────
    #  Core RPC
    # ──────────────────────────────────────────
    def _ensure_auth(self):
        if self._uid is None:
            self.authenticate()

    def _execute_kw(self, model: str, method: str, args: list, kwargs: dict) -> Any:
        """
        Llama a service=object / execute_kw vía /jsonrpc.
        Odoo 19 SaaS: usa uid + api_key como credenciales de objeto.
        """
        if method.lower() in _FORBIDDEN_METHODS:
            raise RuntimeError(
                f"⛔ SOLO LECTURA: '{method}' está bloqueado. "
                "Este cliente no puede modificar datos en Odoo."
            )

        self._ensure_auth()

        payload = _rpc_payload("call", {
            "service": "object",
            "method":  "execute_kw",
            "args": [
                self.db,
                self._uid,
                self.api_key,
                model,
                method,
                args,
                kwargs,
            ],
        })

        resp = self._post("/jsonrpc", payload)

        if "error" in resp:
            err  = resp["error"]
            data = err.get("data", {})
            raise RuntimeError(
                f"❌ Odoo error en {model}.{method}: "
                f"{data.get('message', err.get('message', str(err)))}"
            )

        return resp.get("result")

    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.url}{path}"
        logger.debug(f"→ POST {url}")
        try:
            resp = self._http.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            body = ""
            try:
                body = e.response.text[:300]
            except Exception:
                pass
            raise ConnectionError(
                f"HTTP {e.response.status_code} desde Odoo [{path}]: {body}"
            )
        except httpx.RequestError as e:
            raise ConnectionError(f"No se puede conectar a {self.url}: {e}")


# Singleton
odoo = OdooReadOnlyClient()
