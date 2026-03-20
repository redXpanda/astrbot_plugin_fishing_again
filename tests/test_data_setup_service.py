from __future__ import annotations

import sys
import types


class _DummyLogger:
    def info(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass

    def debug(self, *args, **kwargs):
        pass


if "astrbot.api" not in sys.modules:
    astrbot_module = types.ModuleType("astrbot")
    api_module = types.ModuleType("astrbot.api")
    api_module.logger = _DummyLogger()
    astrbot_module.api = api_module
    sys.modules["astrbot"] = astrbot_module
    sys.modules["astrbot.api"] = api_module

from core.services.data_setup_service import DataSetupService


class FakeItemTemplateRepo:
    def get_all_fish(self):
        return []

    def add_fish_template(self, data):
        return data

    def add_bait_template(self, data):
        return data

    def add_rod_template(self, data):
        return data

    def add_accessory_template(self, data):
        return data

    def add_title_template(self, data):
        return data

    def get_all(self):
        return []

    def add(self, item):
        return item


class FakeGachaRepo:
    def __init__(self):
        self.item_calls = []

    def add_pool_template(self, data):
        return data

    def get_pool_items(self, pool_id):
        return []

    def add_item_to_pool(self, pool_id, data):
        self.item_calls.append((pool_id, data))
        return data


class FakeShopRepo:
    def get_all_shops(self):
        return [{"shop_id": 1}]


def test_setup_initial_data_uses_current_gacha_repo_api():
    gacha_repo = FakeGachaRepo()
    service = DataSetupService(FakeItemTemplateRepo(), gacha_repo, FakeShopRepo())

    service.setup_initial_data()

    assert (1, {"item_full_id": "rod-4", "quantity": 1, "weight": 10}) in gacha_repo.item_calls
    assert (1, {"item_full_id": "coins-0", "quantity": 10000, "weight": 57}) in gacha_repo.item_calls
    assert (2, {"item_full_id": "accessory-4", "quantity": 1, "weight": 5}) in gacha_repo.item_calls
    assert (2, {"item_full_id": "coins-0", "quantity": 20000, "weight": 80}) in gacha_repo.item_calls
