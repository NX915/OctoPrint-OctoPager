# coding=utf-8
from __future__ import absolute_import
import octoprint.plugin
import requests
from datetime import datetime


class PdClient:
    BASE_URL = "https://api.pagerduty.com"

    def __init__(self, token):
        self.token = token

    def get_services(self):
        try:
            services = requests.get(
                f"{self.BASE_URL}/services", headers=self.__headers()).json()["services"]
            return services
        except:
            return []

    def get_service_by_id(self, service_id):
        try:
            service = requests.get(
                f"{self.BASE_URL}/services/{service_id}", headers=self.__headers()).json()["service"]
            return service
        except:
            return []

    def get_service_by_name(self, service_name):
        try:
            service = requests.get(
                f"{self.BASE_URL}/services", params={"query": service_name}, headers=self.__headers()).json()["services"][0]
            return service
        except:
            return []

    def get_intergration(self, service_id, intergration_id):
        try:
            intergration = requests.get(
                f"{self.BASE_URL}/services/{service_id}/integrations/{intergration_id}", headers=self.__headers()).json()["integration"]
            return intergration
        except:
            return []

    def get_users(self):
        return requests.get(f"{self.BASE_URL}/users", headers=self.__headers()).json()["users"]

    def post_incident(self, key, title, severity="critical", action="trigger"):
        # service = self.get_services()[0]
        # key = self.get_intergration()["integration_key"]
        # user = self.get_users()[0]
        return requests.post(f"https://events.pagerduty.com/v2/enqueue",
                             headers={
                                 "Content-Type": "application/json",
                                 "Accept": "application/vnd.pagerduty+json;version=2",
                             },
                             json={
                                 "payload": {
                                     "summary": title,
                                     "timestamp": datetime.now().isoformat(),
                                     "severity": severity,
                                     "source": "octoprint.local",
                                     #  "component": "mysql",
                                     #  "group": "prod-datapipe",
                                     #  "class": "error",
                                     #  "custom_details": {
                                     #      "free space": "1%",
                                     #      "ping time": "1500ms",
                                     #      "load avg": 0.75
                                     #  }
                                 },
                                 "routing_key": key,
                                 "event_action": action,
                                 "client": "Octoprint",
                                 "client_url": "https://octoprint.local",
                                 #  "links": [
                                 #      {
                                 #          "href": "https://octoprint.local",
                                 #          "text": "Local octoprint link."
                                 #      }
                                 #  ],
                                 #  "images": [
                                 #      {
                                 #          "src": "https://chart.googleapis.com/chart?chs=600x400&chd=t:6,2,9,5,2,5,7,4,8,2,1&cht=lc&chds=a&chxt=y&chm=D,0033FF,0,0,5,1",
                                 #          "href": "https://google.com",
                                 #          "alt": "An example link with an image"
                                 #      }
                                 #  ]
                             })

    def __headers(self):
        return {"Authorization": f"Token token={self.token}",
                "Content-Type": "application/json",
                "Accept": "application/vnd.pagerduty+json;version=2"}


class OctopagerPlugin(octoprint.plugin.StartupPlugin,
                      octoprint.plugin.SettingsPlugin,
                      #   octoprint.plugin.AssetPlugin,
                      octoprint.plugin.TemplatePlugin,
                      octoprint.plugin.EventHandlerPlugin
                      ):

    # def on_after_startup(self):
    # pd = PdClient(self._settings.get(["pd_token"]))
    # self._logger.info("Hello World! (more: %s)" %
    #                   self._settings.get(["pd_token"]))
    # self._logger.info(pd.get_services())
    # self._logger.info(pd.get_users())
    # self._logger.info(pd.post_incident(key,
    #     f"Print failed due to: hi").content)

    # ~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return dict(pd_token="",
                    pd_service_id="",
                    print_done=False,
                    print_failed=False,
                    test_start_alert=False,
                    )

    def on_event(self, event, payload):
        self._logger.info(event)
        self._logger.info(payload)
        pd = PdClient(self._settings.get(["pd_token"]))

        if event == octoprint.events.Events.STARTUP and self._settings.get(["test_start_alert"]):
            # reset test alert setting
            self._settings.set(["test_start_alert"], False)
            service = pd.get_service_by_id(
                self._settings.get(["pd_service_id"]))
            key = pd.get_intergration(service["id"], service["integrations"][0]["id"])[
                "integration_key"]
            pd.post_incident(key, f"Octopager test alert!")
        elif event == octoprint.events.Events.PRINT_FAILED and self._settings.get(["print_failed"]):
            service = pd.get_service_by_id(
                self._settings.get(["pd_service_id"]))
            key = pd.get_intergration(service["id"], service["integrations"][0]["id"])[
                "integration_key"]
            pd.post_incident(key, f"Print failed due to: {payload['reason']}")
        elif event == octoprint.events.Events.PRINT_DONE and self._settings.get(["print_done"]):
            service = pd.get_service_by_id(
                self._settings.get(["pd_service_id"]))
            key = pd.get_intergration(service["id"], service["integrations"][0]["id"])[
                "integration_key"]
            pd.post_incident(
                key, f"Print finished: {payload['name']}", "info")

    def get_template_vars(self):
        pd = PdClient(self._settings.get(["pd_token"]))
        return dict(services=pd.get_services())

    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=False)
        ]

    # ~~ AssetPlugin mixin

    # def get_assets(self):
    #     # Define your plugin's asset files to automatically include in the
    #     # core UI here.
    #     return {
    #         "js": ["js/octopager.js"],
    #         "css": ["css/octopager.css"],
    #         "less": ["less/octopager.less"]
    #     }

    # # ~~ Softwareupdate hook

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return {
            "octopager": {
                "displayName": "Octopager Plugin",
                "displayVersion": self._plugin_version,

                # version check: github repository
                "type": "github_release",
                "user": "NX915",
                "repo": "OctoPrint-OctoPager",
                "current": self._plugin_version,

                # update method: pip
                "pip": "https://github.com/NX915/OctoPrint-OctoPager/archive/{target_version}.zip",
            }
        }


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "OctoPager"


# Set the Python version your plugin is compatible with below. Recommended is Python 3 only for all new plugins.
# OctoPrint 1.4.0 - 1.7.x run under both Python 3 and the end-of-life Python 2.
# OctoPrint 1.8.0 onwards only supports Python 3.
__plugin_pythoncompat__ = ">=3,<4"  # Only Python 3


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = OctopagerPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        # "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
