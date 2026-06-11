from modules.sales_agent_pipeline.config import PipelineConfig


def test_telemetry_urls_default_to_port_4000_first():
    urls = PipelineConfig.telemetry_api_urls()
    assert urls[0] == "http://localhost:4000/api/telemetry"
    assert "http://localhost:3000/api/telemetry" in urls


def test_post_payload_reports_http_error(monkeypatch):
    from modules.sales_agent_pipeline.utils import telemetry_bridge

    def _raise_http_error(*_args, **_kwargs):
        from urllib.error import HTTPError

        raise HTTPError(
            url="http://localhost:4000/api/telemetry",
            code=503,
            msg="Service Unavailable",
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr(telemetry_bridge.request, "urlopen", _raise_http_error)
    ok, status, err = telemetry_bridge._post_payload(
        "http://localhost:4000/api/telemetry",
        {"updated_at": "test"},
    )
    assert ok is False
    assert status == 503
    assert "503" in (err or "")
