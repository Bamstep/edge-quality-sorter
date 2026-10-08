import cv2
import pytest
from starlette.testclient import TestClient
from src.api.server import app
from src.edge_vision.detector import generate_synthetic_workpiece


@pytest.fixture(scope='module')
def client():
    with TestClient(app) as c:
        yield c


def test_api_health_and_telemetry(client):
    res = client.get('/health')
    assert res.status_code == 200
    assert res.json()['status'] == 'healthy'

    res = client.get('/telemetry')
    assert res.status_code == 200
    data = res.json()
    assert 'inspected_count' in data
    assert 'line_running' in data
    assert data['line_running'] is True


def test_api_inspect_frame_upload(client):
    # 1. Inspect nominal part
    frame_good = generate_synthetic_workpiece(nominal_radius_px=60, with_defect=False)
    _, encoded_good = cv2.imencode('.png', frame_good)

    files = {'file': ('part_nominal.png', encoded_good.tobytes(), 'image/png')}
    res = client.post('/inspect/frame', files=files)
    assert res.status_code == 200
    data = res.json()
    assert data['is_defective'] is False
    assert data['defect_type'] is None

    # 2. Inspect defective part
    frame_bad = generate_synthetic_workpiece(nominal_radius_px=60, with_defect=True, defect_type='pit')
    _, encoded_bad = cv2.imencode('.png', frame_bad)

    files = {'file': ('part_defective.png', encoded_bad.tobytes(), 'image/png')}
    res = client.post('/inspect/frame', files=files)
    assert res.status_code == 200
    data = res.json()
    assert data['is_defective'] is True
    assert data['defect_type'] == 'Surface_Pitting_or_Crack'

    # 3. Check updated telemetry
    res_telem = client.get('/telemetry')
    telem = res_telem.json()
    assert telem['inspected_count'] >= 2
    assert telem['rejected_count'] >= 1


def test_api_manual_pulse(client):
    res = client.post('/actuator/manual-pulse')
    assert res.status_code == 200
    assert res.json()['status'] == 'success'
