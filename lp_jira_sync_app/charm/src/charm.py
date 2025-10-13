#!/usr/bin/env python3
# Copyright 2025
# See LICENSE file for licensing details.

import ops
from charms.nginx_ingress_integrator.v0.nginx_route import require_nginx_route
# The workload container name must match the oci-image resource key in charmcraft.yaml
CONTAINER_NAME = "lp-jira-sync-bot"
# Label for the Pebble service inside the container
SERVICE_NAME = "fastapi"
PORT = 8000


class LpJiraSyncBotCharm(ops.CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        # Workload container (K8s charm)
        require_nginx_route(
            charm=self,
            service_hostname=self.app.name,
            service_name=self.app.name,
            service_port=int(self.config["port"]),
        )
        # Event handlers

        self.framework.observe(self.on[CONTAINER_NAME].pebble_ready, self._on_config_changed)
        self.framework.observe(self.on.config_changed, self._on_config_changed)

    def _pebble_layer(self) -> dict:
        """Define the Pebble layer for running the FastAPI app with uvicorn."""
        env = {
            # Non-secret config values passed as env vars. These keys align with app expectations.
            "launchpad_webhook_secret_code": self.config.get("launchpad_webhook_secret_code", ""),
            "launchpad_url": self.config.get("launchpad_url", ""),
            "jira_instance": self.config.get("jira_instance", ""),
            "jira_username": self.config.get("jira_username", ""),
            "jira_token": self.config.get("jira_token", ""),
            "port":self.config.get("port", PORT),
        }

        return {
            "summary": "Pebble layer for lp-jira-sync-bot",
            "services": {
                SERVICE_NAME: {
                    "override": "replace",
                    "summary": "Run FastAPI via Uvicorn",
                    "command": f"uvicorn main:app --host 0.0.0.0 --port {PORT}",
                    "startup": "enabled",
                    "working-dir": "/app",
                    "environment": env,
                }
            },
        }

    def _on_config_changed(self, event: ops.ConfigChangedEvent):
        self._handle_ports()

        container = self.unit.get_container("lp-jira-sync-bot")
        if container.can_connect():
            # Push an updated layer with the new config
            container.add_layer("lp_jira_sync_bot", self._pebble_layer(), combine=True)
            container.replan()

            self.unit.status = ops.ActiveStatus()
        else:
            # We were unable to connect to the Pebble API, so we defer this event
            event.defer()
            self.unit.status = ops.WaitingStatus("Waiting for Pebble API")

    def _handle_ports(self):
        port = int(self.config["port"])
        opened_ports = self.unit.opened_ports()

        if port in [i.port for i in opened_ports]:
            return

        for o_port in opened_ports:
            self.unit.close_port(o_port.protocol, o_port.port)

        self.unit.open_port("tcp", port)

if __name__ == "__main__":
    ops.main.main(LpJiraSyncBotCharm)