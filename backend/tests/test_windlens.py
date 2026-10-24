"""
Test suite for WindLens UK backend.

All tests use small deterministic fixtures — never actual January 2026 data.
Fixture data is clearly labelled and never presented as real observations.
"""
import pytest
import math
from datetime import date, datetime, timedelta
import pytz

# ============================================================
# Test helpers
# ============================================================

UTC = pytz.UTC


def make_actual(start_time_utc: datetime, generation_mw: float, sp: int = 1):
    from app.schemas.data_models import ActualRecord
    return ActualRecord(
        start_time_utc=start_time_utc,
        generation_mw=generation_mw,
        settlement_period=sp,
        dataset="FUELHH",
    )


def make_forecast(start_time_utc: datetime, publish_time_utc: datetime, generation_mw: float):
    from app.schemas.data_models import ForecastRecord
    return ForecastRecord(
        start_time_utc=start_time_utc,
        publish_time_utc=publish_time_utc,
        generation_mw=generation_mw,
        dataset="WINDFOR",
    )


# ============================================================
# FUELHH parser tests
# ============================================================

class TestFuelHHParser:
    def setup_method(self):
        from app.services.elexon.fuelhh_client import FuelHHClient
        self.client = FuelHHClient()

    def test_filters_to_wind(self):
        """Only WIND records should be returned."""
        items = [
            {"startTime": "2026-01-15T00:00:00Z", "publishTime": "2026-01-15T00:30:00Z",
             "fuelType": "WIND", "generation": 8000, "settlementPeriod": 1},
            {"startTime": "2026-01-15T00:00:00Z", "publishTime": "2026-01-15T00:30:00Z",
             "fuelType": "GAS", "generation": 5000, "settlementPeriod": 1},
            {"startTime": "2026-01-15T00:00:00Z", "publishTime": "2026-01-15T00:30:00Z",
             "fuelType": "NUCLEAR", "generation": 7000, "settlementPeriod": 1},
        ]
        records, excluded = self.client._parse_records(items, date(2026, 1, 15))
        assert len(records) == 1
        assert records[0].generation_mw == 8000
        assert excluded == 2

    def test_case_insensitive_fuel_type(self):
        """fuelType matching should be case-insensitive."""
        items = [
            {"startTime": "2026-01-15T00:00:00Z", "publishTime": "2026-01-15T00:30:00Z",
             "fuelType": "wind", "generation": 8000, "settlementPeriod": 1},
        ]
        records, excluded = self.client._parse_records(items, date(2026, 1, 15))
        assert len(records) == 1

    def test_excludes_negative_generation(self):
        """Negative generation values must be excluded."""
        items = [
            {"startTime": "2026-01-15T00:00:00Z", "publishTime": "2026-01-15T00:30:00Z",
             "fuelType": "WIND", "generation": -100, "settlementPeriod": 1},
        ]
        records, excluded = self.client._parse_records(items, date(2026, 1, 15))
        assert len(records) == 0
        assert excluded == 1

    def test_excludes_null_generation(self):
        """None generation must be excluded."""
        items = [
            {"startTime": "2026-01-15T00:00:00Z", "publishTime": "2026-01-15T00:30:00Z",
             "fuelType": "WIND", "generation": None, "settlementPeriod": 1},
        ]
        records, excluded = self.client._parse_records(items, date(2026, 1, 15))
        assert len(records) == 0
        assert excluded == 1

    def test_deduplicates_on_start_time(self):
        """Duplicate startTime records — keep first occurrence."""
        items = [
            {"startTime": "2026-01-15T00:00:00Z", "publishTime": "2026-01-15T00:30:00Z",
             "fuelType": "WIND", "generation": 8000, "settlementPeriod": 1},
            {"startTime": "2026-01-15T00:00:00Z", "publishTime": "2026-01-15T00:30:00Z",
             "fuelType": "WIND", "generation": 8500, "settlementPeriod": 1},
        ]
        records, excluded = self.client._parse_records(items, date(2026, 1, 15))
        assert len(records) == 1
        assert records[0].generation_mw == 8000  # first wins

    def test_filters_to_target_date(self):
        """Records from a different date should be excluded."""
        items = [
            {"startTime": "2026-01-14T23:30:00Z", "publishTime": "2026-01-15T00:00:00Z",
             "fuelType": "WIND", "generation": 7500, "settlementPeriod": 48},
            {"startTime": "2026-01-15T00:00:00Z", "publishTime": "2026-01-15T00:30:00Z",
             "fuelType": "WIND", "generation": 8000, "settlementPeriod": 1},
        ]
        records, excluded = self.client._parse_records(items, date(2026, 1, 15))
        assert len(records) == 1
        assert records[0].generation_mw == 8000

    def test_excludes_missing_fuel_type(self):
        """Records with missing fuelType must be excluded."""
        items = [
            {"startTime": "2026-01-15T00:00:00Z", "publishTime": "2026-01-15T00:30:00Z",
             "generation": 8000, "settlementPeriod": 1},
        ]
        records, excluded = self.client._parse_records(items, date(2026, 1, 15))
        assert len(records) == 0

    def test_handles_non_numeric_generation(self):
        """Non-numeric generation must be excluded."""
        items = [
            {"startTime": "2026-01-15T00:00:00Z", "publishTime": "2026-01-15T00:30:00Z",
             "fuelType": "WIND", "generation": "N/A", "settlementPeriod": 1},
        ]
        records, excluded = self.client._parse_records(items, date(2026, 1, 15))
        assert len(records) == 0


# ============================================================
# WINDFOR parser tests
# ============================================================

class TestWindForParser:
    def setup_method(self):
        from app.services.elexon.windfor_client import WindForClient
        self.client = WindForClient()

    def test_parses_valid_records(self):
        items = [
            {"startTime": "2026-01-15T00:00:00Z", "publishTime": "2026-01-14T10:00:00Z",
             "generation": 9000},
            {"startTime": "2026-01-15T01:00:00Z", "publishTime": "2026-01-14T10:00:00Z",
             "generation": 9500},
        ]
        records, excluded = self.client._parse_records(items)
        assert len(records) == 2
        assert excluded == 0

    def test_excludes_missing_publish_time(self):
        items = [{"startTime": "2026-01-15T00:00:00Z", "generation": 9000}]
        records, excluded = self.client._parse_records(items)
        assert len(records) == 0
        assert excluded == 1

    def test_excludes_negative_generation(self):
        items = [
            {"startTime": "2026-01-15T00:00:00Z", "publishTime": "2026-01-14T10:00:00Z",
             "generation": -500},
        ]
        records, excluded = self.client._parse_records(items)
        assert len(records) == 0


# ============================================================
# Forecast selection tests
# ============================================================

class TestForecastSelection:
    DELIVERY_DATE = date(2026, 1, 15)
    CUTOFF_TIME = "11:00"

    # In January (GMT), midnight UK = midnight UTC
    DAY_START = datetime(2026, 1, 15, 0, 0, 0, tzinfo=UTC)
    CUTOFF_UTC = datetime(2026, 1, 14, 11, 0, 0, tzinfo=UTC)  # 11:00 on D-1

    def _make_actuals_for_day(self, n=48, base_mw=8000):
        actuals = []
        for i in range(n):
            t = self.DAY_START + timedelta(minutes=30 * i)
            actuals.append(make_actual(t, base_mw + i * 10, sp=i + 1))
        return actuals

    def _make_forecasts_hourly(self, n_hours=24, publish_time=None, base_mw=8200):
        if publish_time is None:
            publish_time = datetime(2026, 1, 14, 10, 30, 0, tzinfo=UTC)
        forecasts = []
        for i in range(n_hours):
            t = self.DAY_START + timedelta(hours=i)
            forecasts.append(make_forecast(t, publish_time, base_mw + i * 5))
        return forecasts

    def test_selects_latest_eligible_forecast(self):
        """Must select the forecast with the latest publishTime <= cutoff."""
        from app.services.analytics.forecast_selection import select_forecasts

        t0 = self.DAY_START  # hour 0 delivery period

        early_pub = datetime(2026, 1, 14, 8, 0, 0, tzinfo=UTC)
        late_pub = datetime(2026, 1, 14, 10, 30, 0, tzinfo=UTC)
        post_cutoff_pub = datetime(2026, 1, 14, 12, 0, 0, tzinfo=UTC)

        actuals = self._make_actuals_for_day()
        forecasts = [
            make_forecast(t0, early_pub, 7800),
            make_forecast(t0, late_pub, 8100),   # ← should be selected
            make_forecast(t0, post_cutoff_pub, 8500),  # post-cutoff: must not be selected
        ]

        periods, _ = select_forecasts(actuals, forecasts, self.DELIVERY_DATE, self.CUTOFF_TIME)
        period_0 = next(p for p in periods if p.start_time_utc == t0)

        assert period_0.forecast_mw == 8100
        assert period_0.forecast_publish_time_utc == late_pub
        assert period_0.forecast_selected is True

    def test_rejects_post_cutoff_forecast(self):
        """A forecast published after the cutoff must not be used for decision."""
        from app.services.analytics.forecast_selection import select_forecasts

        t0 = self.DAY_START
        post_cutoff_pub = datetime(2026, 1, 14, 12, 0, 0, tzinfo=UTC)

        actuals = self._make_actuals_for_day()
        forecasts = [make_forecast(t0, post_cutoff_pub, 8500)]

        periods, _ = select_forecasts(actuals, forecasts, self.DELIVERY_DATE, self.CUTOFF_TIME)
        period_0 = next(p for p in periods if p.start_time_utc == t0)

        assert period_0.forecast_mw is None
        assert period_0.missing_forecast is True

    def test_handles_missing_actual(self):
        """Periods with no actual should have actual_available=False."""
        from app.services.analytics.forecast_selection import select_forecasts

        forecasts = self._make_forecasts_hourly()
        periods, _ = select_forecasts([], forecasts, self.DELIVERY_DATE, self.CUTOFF_TIME)

        assert all(p.missing_actual for p in periods)
        assert all(p.actual_mw is None for p in periods)

    def test_handles_missing_forecast(self):
        """Periods with no forecast should have missing_forecast=True."""
        from app.services.analytics.forecast_selection import select_forecasts

        actuals = self._make_actuals_for_day()
        periods, _ = select_forecasts(actuals, [], self.DELIVERY_DATE, self.CUTOFF_TIME)

        assert all(p.missing_forecast for p in periods)
        assert all(p.forecast_mw is None for p in periods)

    def test_error_signs(self):
        """error_mw = forecast - actual. Positive = over-forecast."""
        from app.services.analytics.forecast_selection import select_forecasts

        t0 = self.DAY_START
        pub = datetime(2026, 1, 14, 10, 0, 0, tzinfo=UTC)
        actuals = [make_actual(t0, 8000)]
        forecasts = [make_forecast(t0, pub, 8500)]

        periods, _ = select_forecasts(actuals, forecasts, self.DELIVERY_DATE, self.CUTOFF_TIME)
        p = next(p for p in periods if p.start_time_utc == t0)
        assert p.error_mw == pytest.approx(500.0)  # over-forecast

    def test_joins_on_delivery_timestamp(self):
        """Forecast and actual must be joined on matching delivery start time."""
        from app.services.analytics.forecast_selection import select_forecasts

        t0 = self.DAY_START
        t1 = self.DAY_START + timedelta(minutes=30)
        pub = datetime(2026, 1, 14, 10, 0, 0, tzinfo=UTC)

        actuals = [make_actual(t0, 8000), make_actual(t1, 8200)]
        # Forecast covers t0 (hourly) — should match both t0 and t1
        forecasts = [make_forecast(t0, pub, 8100)]

        periods, _ = select_forecasts(actuals, forecasts, self.DELIVERY_DATE, self.CUTOFF_TIME)
        p0 = next(p for p in periods if p.start_time_utc == t0)
        p1 = next(p for p in periods if p.start_time_utc == t1)

        # Both HH periods in the same hour should use the same hourly forecast
        assert p0.forecast_mw == 8100
        assert p1.forecast_mw == 8100  # same hourly forecast


# ============================================================
# Analytics / metrics tests
# ============================================================

class TestMetrics:
    def _make_matched_periods(self, pairs: list):
        """Create MatchedPeriod list from (forecast, actual) tuples."""
        from app.schemas.data_models import MatchedPeriod
        periods = []
        for i, (f, a) in enumerate(pairs):
            t = datetime(2026, 1, 15, 0, 0, 0, tzinfo=UTC) + timedelta(minutes=30 * i)
            mp = MatchedPeriod(
                start_time_utc=t,
                delivery_date=date(2026, 1, 15),
                decision_cutoff_utc=datetime(2026, 1, 14, 11, 0, 0, tzinfo=UTC),
                forecast_mw=f,
                actual_mw=a,
                actual_available=a is not None,
                forecast_selected=f is not None,
                missing_forecast=f is None,
                missing_actual=a is None,
            )
            mp.compute_errors()
            periods.append(mp)
        return periods

    def test_mae(self):
        from app.services.analytics.metrics import compute_mae
        periods = self._make_matched_periods([(9000, 8000), (8500, 9000), (7000, 7500)])
        mae, n = compute_mae(periods)
        assert n == 3
        # errors: 1000, -500, -500 → abs: 1000, 500, 500 → mean = 666.67
        assert mae == pytest.approx(666.67, abs=0.5)

    def test_rmse(self):
        from app.services.analytics.metrics import compute_rmse
        periods = self._make_matched_periods([(9000, 8000), (8000, 8000)])
        rmse, n = compute_rmse(periods)
        assert n == 2
        # (1000^2 + 0^2)/2 = 500000, sqrt = 707.11
        assert rmse == pytest.approx(707.11, abs=0.5)

    def test_bias_positive(self):
        """Positive bias means forecasts over-estimated actual wind."""
        from app.services.analytics.metrics import compute_bias
        periods = self._make_matched_periods([(9000, 8000), (8500, 8000)])
        bias, n = compute_bias(periods)
        assert n == 2
        assert bias > 0

    def test_bias_negative(self):
        """Negative bias means forecasts under-estimated actual wind."""
        from app.services.analytics.metrics import compute_bias
        periods = self._make_matched_periods([(7000, 8000), (7500, 8000)])
        bias, n = compute_bias(periods)
        assert n == 2
        assert bias < 0

    def test_mape_excludes_zero_actual(self):
        """MAPE must exclude periods where actual = 0."""
        from app.services.analytics.metrics import compute_mape
        periods = self._make_matched_periods([
            (8000, 8000),   # error=0, pct=0
            (8000, 0),      # actual=0, must be excluded
            (9000, 8000),   # error=1000, pct=12.5%
        ])
        mape, n_valid, n_excl = compute_mape(periods)
        assert n_excl == 1
        assert n_valid == 2
        assert mape is not None
        assert mape == pytest.approx(6.25, abs=0.1)  # (0 + 12.5)/2

    def test_mape_all_zero_actual(self):
        """When all actuals are zero, MAPE is undefined."""
        from app.services.analytics.metrics import compute_mape
        periods = self._make_matched_periods([(8000, 0), (9000, 0)])
        mape, n_valid, n_excl = compute_mape(periods)
        assert mape is None
        assert n_valid == 0
        assert n_excl == 2

    def test_metrics_empty_returns_none(self):
        """Empty period list returns None for all metrics."""
        from app.services.analytics.metrics import compute_mae, compute_rmse, compute_bias, compute_mape
        periods = []
        assert compute_mae(periods) == (None, 0)
        assert compute_rmse(periods) == (None, 0)
        assert compute_bias(periods) == (None, 0)
        assert compute_mape(periods) == (None, 0, 0)

    def test_missing_pairs_excluded(self):
        """Periods with missing forecast or actual are excluded from metrics."""
        from app.services.analytics.metrics import compute_mae
        periods = self._make_matched_periods([
            (9000, 8000),
            (None, 8000),   # missing forecast
            (8000, None),   # missing actual
        ])
        mae, n = compute_mae(periods)
        assert n == 1  # only the matched pair counts


# ============================================================
# Timezone tests
# ============================================================

class TestTimezone:
    def test_delivery_date_uk_winter(self):
        """In January (GMT), UTC and UK date are the same."""
        from app.core.timezone import delivery_date_uk
        dt = datetime(2026, 1, 15, 23, 30, 0, tzinfo=pytz.UTC)
        assert delivery_date_uk(dt) == date(2026, 1, 15)

    def test_settlement_period_first(self):
        """Midnight UK = SP 1 in January."""
        from app.core.timezone import settlement_period_from_start
        dt = datetime(2026, 1, 15, 0, 0, 0, tzinfo=pytz.UTC)
        assert settlement_period_from_start(dt) == 1

    def test_settlement_period_last(self):
        """23:30 UK = SP 48 in January."""
        from app.core.timezone import settlement_period_from_start
        dt = datetime(2026, 1, 15, 23, 30, 0, tzinfo=pytz.UTC)
        assert settlement_period_from_start(dt) == 48

    def test_cutoff_utc_january(self):
        """11:00 UK on 2026-01-14 (GMT) should be 11:00 UTC."""
        from app.core.timezone import cutoff_utc
        result = cutoff_utc(date(2026, 1, 14), "11:00")
        assert result.hour == 11
        assert result.minute == 0
        assert result.tzinfo is not None

    def test_parse_utc_with_z(self):
        """ISO 8601 strings ending in Z should parse to UTC."""
        from app.core.timezone import parse_utc
        dt = parse_utc("2026-01-15T11:30:00Z")
        assert dt.tzinfo is not None
        assert dt.hour == 11

    def test_uk_midnight_utc_january(self):
        """UK midnight on Jan 15 2026 (GMT) = 2026-01-15T00:00:00Z."""
        from app.core.timezone import uk_midnight_utc
        result = uk_midnight_utc(date(2026, 1, 15))
        assert result.year == 2026
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 0


# ============================================================
# Scenario calculation tests
# ============================================================

class TestScenario:
    def test_residual_non_negative(self):
        """Residual demand should never be negative."""
        assumed_demand = 30000
        wind_forecast = 25000
        other_supply = 8000
        residual = max(0, assumed_demand - wind_forecast - other_supply)
        assert residual == 0  # capped at 0

    def test_residual_positive(self):
        """When wind covers less than demand minus other, residual is positive."""
        assumed_demand = 30000
        wind_forecast = 5000
        other_supply = 8000
        residual = max(0, assumed_demand - wind_forecast - other_supply)
        assert residual == 17000

    def test_invalid_demand_rejected(self):
        """Demand above 80,000 MW should fail validation."""
        from app.schemas.responses import ScenarioInput
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ScenarioInput(
                assumed_demand_mw=100000,
                delivery_date=date(2026, 1, 15),
            )


# ============================================================
# API integration tests (no live network calls)
# ============================================================

@pytest.mark.asyncio
class TestAPIEndpoints:
    @pytest.fixture(autouse=True)
    def client(self):
        from fastapi.testclient import TestClient
        from app.main import app
        self.tc = TestClient(app)

    def test_health_returns_200(self):
        r = self.tc.get("/api/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_overview_default(self):
        r = self.tc.get("/api/overview")
        assert r.status_code == 200
        data = r.json()
        assert data["is_fixture_data"] is True
        assert len(data["metrics"]) == 4

    def test_overview_valid_date(self):
        r = self.tc.get("/api/overview?delivery_date=2026-01-10")
        assert r.status_code == 200

    def test_overview_invalid_date(self):
        r = self.tc.get("/api/overview?delivery_date=2025-12-01")
        assert r.status_code == 400

    def test_forecast_default(self):
        r = self.tc.get("/api/forecast")
        assert r.status_code == 200
        data = r.json()
        assert len(data["periods"]) == 48  # 48 HH periods in Jan (GMT)

    def test_forecast_versions(self):
        r = self.tc.get(
            "/api/forecast/versions?delivery_date=2026-01-15&start_time_utc=2026-01-15T00:00:00Z"
        )
        assert r.status_code == 200
        data = r.json()
        assert "versions" in data
        assert len(data["versions"]) > 0

    def test_analytics_accuracy(self):
        r = self.tc.get("/api/analytics/accuracy?start_date=2026-01-01&end_date=2026-01-07")
        assert r.status_code == 200
        data = r.json()
        assert "metrics" in data
        assert "coverage" in data

    def test_settlement_periods(self):
        r = self.tc.get("/api/settlement-periods?start_date=2026-01-01&end_date=2026-01-02")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] > 0

    def test_settlement_export(self):
        r = self.tc.get("/api/settlement-periods/export?start_date=2026-01-01&end_date=2026-01-01")
        assert r.status_code == 200
        assert "text/csv" in r.headers["content-type"]
        assert b"delivery_date" in r.content

    def test_scenario_post(self):
        r = self.tc.post("/api/scenarios/residual-demand", json={
            "assumed_demand_mw": 30000,
            "assumed_other_supply_mw": 5000,
            "delivery_date": "2026-01-15",
        })
        assert r.status_code == 200
        data = r.json()
        assert "disclaimer" in data
        assert "ILLUSTRATIVE" in data["disclaimer"]

    def test_scenario_invalid_demand(self):
        r = self.tc.post("/api/scenarios/residual-demand", json={
            "assumed_demand_mw": -1000,
            "delivery_date": "2026-01-15",
        })
        assert r.status_code == 422
