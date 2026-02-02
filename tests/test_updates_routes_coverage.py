import pytest
from unittest.mock import patch, MagicMock

def test_get_update_status(client):
    with patch('app.api.updates_routes.get_updater') as mock_get_updater:
        mock_updater = MagicMock()
        mock_updater.is_running = True
        mock_updater.progress = {"symbols_updated": 10, "total_symbols": 100}
        mock_updater.get_status.return_value = {"message": "In Progress"}
        mock_get_updater.return_value = mock_updater
        
        response = client.get('/api/updates/status')
        assert response.status_code == 200
        assert response.json['status'] == "running"

def test_start_update_route(client):
    with patch('app.api.updates_routes.get_updater') as mock_get_updater:
        mock_updater = MagicMock()
        mock_updater.symbols_per_day = 100
        mock_get_updater.return_value = mock_updater
        
        response = client.post('/api/updates/start')
        assert response.status_code == 200
        assert "started" in response.json['message'].lower()
        mock_updater.start.assert_called_once()

def test_stop_update_route(client):
    with patch('app.api.updates_routes.get_updater') as mock_get_updater:
        mock_updater = MagicMock()
        mock_updater.progress = {"status": "stopped"}
        mock_get_updater.return_value = mock_updater
        
        response = client.post('/api/updates/stop')
        assert response.status_code == 200
        assert "stopped" in response.json['message'].lower()
        mock_updater.stop.assert_called_once()
