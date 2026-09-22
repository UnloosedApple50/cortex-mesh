"""
Tests for HermesMesh profiles system.
"""

import pytest
from datetime import datetime, timezone

from hermesmesh.core.profiles import ProfileManager, ResourceProfile


class TestResourceProfile:
    def test_create_profile(self):
        profile = ResourceProfile(
            name="test-profile",
            description="A test profile",
            cpu_limit_percent=80.0,
            memory_limit_percent=85.0,
            priority="high",
        )
        assert profile.name == "test-profile"
        assert profile.cpu_limit_percent == 80.0
        assert profile.priority == "high"
        assert profile.profile_id is not None

    def test_default_values(self):
        profile = ResourceProfile(name="default")
        assert profile.cpu_limit_percent is None
        assert profile.memory_limit_percent is None
        assert profile.priority == "normal"
        assert profile.allowed_node_roles == []

    def test_is_active_no_hours(self):
        profile = ResourceProfile(name="always-on")
        assert profile.is_active() is True

    def test_is_active_within_hours(self):
        profile = ResourceProfile(
            name="night-shift",
            allowed_hours_start=22,
            allowed_hours_end=6,
        )
        # Test hour 23 (11 PM) - within range (wraps midnight)
        assert profile.is_active(hour=23) is True
        # Test hour 3 (3 AM) - within range
        assert profile.is_active(hour=3) is True
        # Test hour 12 (noon) - outside range
        assert profile.is_active(hour=12) is False

    def test_is_active_normal_hours(self):
        profile = ResourceProfile(
            name="day-shift",
            allowed_hours_start=8,
            allowed_hours_end=18,
        )
        assert profile.is_active(hour=12) is True
        assert profile.is_active(hour=6) is False
        assert profile.is_active(hour=20) is False

    def test_to_dict(self):
        profile = ResourceProfile(
            name="test",
            cpu_limit_percent=75.0,
        )
        d = profile.to_dict()
        assert d["name"] == "test"
        assert d["cpu_limit_percent"] == 75.0
        assert "profile_id" in d
        assert "created_at" in d

    def test_from_dict(self):
        data = {
            "profile_id": "test-id",
            "name": "restored",
            "cpu_limit_percent": 90.0,
            "priority": "high",
        }
        profile = ResourceProfile.from_dict(data)
        assert profile.profile_id == "test-id"
        assert profile.name == "restored"
        assert profile.cpu_limit_percent == 90.0
        assert profile.priority == "high"


class TestProfileManager:
    def test_create_profile(self):
        manager = ProfileManager()
        profile = manager.create_profile(name="test", cpu_limit_percent=80.0)
        assert profile.name == "test"
        assert profile.profile_id is not None

    def test_get_profile(self):
        manager = ProfileManager()
        profile = manager.create_profile(name="test")
        retrieved = manager.get_profile(profile.profile_id)
        assert retrieved is not None
        assert retrieved.profile_id == profile.profile_id

    def test_update_profile(self):
        manager = ProfileManager()
        profile = manager.create_profile(name="test", cpu_limit_percent=80.0)
        updated = manager.update_profile(profile.profile_id, cpu_limit_percent=90.0)
        assert updated is not None
        assert updated.cpu_limit_percent == 90.0

    def test_delete_profile(self):
        manager = ProfileManager()
        profile = manager.create_profile(name="test")
        result = manager.delete_profile(profile.profile_id)
        assert result is True
        assert manager.get_profile(profile.profile_id) is None

    def test_list_profiles(self):
        manager = ProfileManager()
        manager.create_profile(name="profile-1")
        manager.create_profile(name="profile-2")
        profiles = manager.list_profiles()
        assert len(profiles) == 2

    def test_get_active_profiles(self):
        manager = ProfileManager()
        # Always active
        p1 = manager.create_profile(name="always-on")
        # Only active at night
        p2 = manager.create_profile(
            name="night-only",
            allowed_hours_start=22,
            allowed_hours_end=6,
        )
        
        # At noon, only "always-on" should be active
        active = manager.get_active_profiles(hour=12)
        assert len(active) == 1
        assert active[0].name == "always-on"

        # At midnight, both should be active
        active = manager.get_active_profiles(hour=0)
        assert len(active) == 2
