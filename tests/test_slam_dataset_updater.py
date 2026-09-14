import unittest

import slam_dataset_updater as updater


class FakeGitHub:
    def search_repositories(self, query, limit):
        return [{
            "full_name": "robot/demo-slam",
            "html_url": "https://github.com/robot/demo-slam",
            "name": "demo-slam",
            "description": "LiDAR SLAM benchmark with trajectory ground truth",
            "stargazers_count": 12,
        }]

    def readme(self, full_name):
        return (
            "Uses an Ouster OS1-64 3D LiDAR. "
            "The reference trajectory is ground truth. "
            "[Dataset](https://data.example.org/demo)"
        )


class UpdaterTests(unittest.TestCase):
    def test_hard_requirements(self):
        valid = updater.normalize_record({
            "name": "valid",
            "project": {"url": "https://github.com/a/b"},
            "dataset": {"url": "https://example.org/data"},
            "sensors": {"lidar_3d": "Velodyne HDL-32E"},
            "ground_truth": {"available": True},
        })
        self.assertEqual(updater.validate_record(valid), (True, []))

        invalid = updater.normalize_record({
            "name": "camera only",
            "project": {"url": "https://github.com/a/b"},
            "dataset": {"url": "https://example.org/data"},
            "sensors": {"camera": "RGB"},
            "ground_truth": {"available": True},
        })
        ok, errors = updater.validate_record(invalid)
        self.assertFalse(ok)
        self.assertIn("没有确认 3D 激光雷达", errors)

        two_d = updater.normalize_record({
            "name": "2D lidar",
            "project": {"url": "https://github.com/a/b"},
            "dataset": {"url": "https://example.org/2d"},
            "sensors": {"lidar_3d": "2D LiDAR"},
            "ground_truth": {"available": True},
        })
        self.assertFalse(updater.has_3d_lidar(two_d))

    def test_discovery_requires_both_evidence_types(self):
        records = updater.discover_from_github(FakeGitHub(), {
            "github_search_queries": ["slam"],
            "max_repositories_per_query": 1,
        })
        self.assertEqual(len(records), 1)
        self.assertIn("Ouster", records[0]["evidence"])
        self.assertEqual(records[0]["dataset"]["url"], "https://data.example.org/demo")
        self.assertFalse(updater.evidence_matches(
            "3D LiDAR semantic labels provide point-wise ground truth",
            updater.GROUND_TRUTH_PATTERNS,
        ))

    def test_json_parser_accepts_fenced_output(self):
        self.assertEqual(
            updater.parse_json_object('```json\n{"confidence": 0.9}\n```'),
            {"confidence": 0.9},
        )


if __name__ == "__main__":
    unittest.main()
