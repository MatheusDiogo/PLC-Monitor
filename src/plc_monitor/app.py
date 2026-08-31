import webview

from plc_monitor.config.settings import WEB_DIR
from plc_monitor.web.api import Api


def main():
    api = Api()
    window = webview.create_window(
        "Monitor de CLPs",
        url=f"{WEB_DIR}/index.html",
        js_api=api,
        width=1400,
        height=900,
        min_size=(900, 600),
        background_color="#0b0e13",
    )
    window.events.closed += api.shutdown
    webview.start()


if __name__ == "__main__":
    main()
