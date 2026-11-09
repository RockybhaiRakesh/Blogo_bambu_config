"""
Integration and Unit Tests for PRINTMATE AI FastAPI Endpoints.
Verifies full REST API functionality across models, geometry analysis, splitting, settings,
3MF packaging, and G-code validation.
"""

import os
import io
import unittest
from fastapi.testclient import TestClient

from printmate.api.app import app
from printmate.api.job_manager import JobManager
from printmate.core.config import Config

class TestAPIEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        # Create a small valid test STL for fast testing
        cls.test_stl_content = (
            b"solid test_box\n"
            b"  facet normal 0 0 1\n"
            b"    outer loop\n"
            b"      vertex 0 0 10\n"
            b"      vertex 10 0 10\n"
            b"      vertex 10 10 10\n"
            b"    endloop\n"
            b"  endfacet\n"
            b"  facet normal 0 0 1\n"
            b"    outer loop\n"
            b"      vertex 0 0 10\n"
            b"      vertex 10 10 10\n"
            b"      vertex 0 10 10\n"
            b"    endloop\n"
            b"  endfacet\n"
            b"  facet normal 0 0 -1\n"
            b"    outer loop\n"
            b"      vertex 0 0 0\n"
            b"      vertex 10 10 0\n"
            b"      vertex 10 0 0\n"
            b"    endloop\n"
            b"  endfacet\n"
            b"  facet normal 0 0 -1\n"
            b"    outer loop\n"
            b"      vertex 0 0 0\n"
            b"      vertex 0 10 0\n"
            b"      vertex 10 10 0\n"
            b"    endloop\n"
            b"  endfacet\n"
            b"endsolid test_box\n"
        ) * 5  # > 100 bytes

    def test_health_check(self):
        """Verifies health check endpoint."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "PRINTMATE AI")

    def test_dashboard_stats(self):
        """Verifies dashboard stats endpoint."""
        res = self.client.get("/api/dashboard/stats")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total_projects", data)
        self.assertIn("bambu_studio_installed", data)
        self.assertEqual(data["test_suite_status"], "CERTIFIED_100_PERCENT_PASSING")

    def test_profiles_printers_and_filaments(self):
        """Verifies printer and filament profile registries endpoints."""
        res_p = self.client.get("/api/settings/printers")
        self.assertEqual(res_p.status_code, 200)
        printers = res_p.json()
        self.assertTrue(any("a1" in p["id"].lower() for p in printers))

        res_f = self.client.get("/api/settings/filaments")
        self.assertEqual(res_f.status_code, 200)
        filaments = res_f.json()
        self.assertTrue(any("pla_basic" in f["id"].lower() for f in filaments))

    def test_settings_optimize(self):
        """Verifies print settings optimization endpoint."""
        payload = {
            "printer_id": "bambu_a1",
            "filament_id": "pla_basic",
            "objective": "balanced_quality",
            "has_connectors": False
        }
        res = self.client.post("/api/settings/optimize", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("layer_height_mm", data)
        self.assertIn("nozzle_temperature", data)
        self.assertIn("bed_temperature", data)
        self.assertTrue(data["is_compatible"])

    def test_model_upload_and_lifecycle(self):
        """Verifies model upload, metadata retrieval, mesh download, analysis, and split recommendations."""
        # 1. Upload
        files = {"file": ("test_cube.stl", io.BytesIO(self.test_stl_content), "application/octet-stream")}
        upload_res = self.client.post("/api/models/upload", files=files)
        self.assertEqual(upload_res.status_code, 200)
        up_data = upload_res.json()
        self.assertTrue(up_data["success"])
        model_id = up_data["model"]["model_id"]

        # 2. Get metadata
        meta_res = self.client.get(f"/api/models/{model_id}")
        self.assertEqual(meta_res.status_code, 200)
        self.assertEqual(meta_res.json()["filename"], "test_cube.stl")

        # 3. Get mesh
        mesh_res = self.client.get(f"/api/models/{model_id}/mesh")
        self.assertEqual(mesh_res.status_code, 200)
        self.assertGreater(len(mesh_res.content), 0)

        # 4. Analyze
        ana_res = self.client.post(f"/api/models/{model_id}/analyze")
        self.assertEqual(ana_res.status_code, 200)
        ana_data = ana_res.json()
        self.assertIn("geometry", ana_data)
        self.assertIn("thickness", ana_data)
        self.assertIn("vision", ana_data)

        # 5. Split recommendations
        rec_res = self.client.get(f"/api/models/{model_id}/split-recommendations")
        self.assertEqual(rec_res.status_code, 200)
        rec_data = rec_res.json()
        self.assertIn("exceeds_build_volume", rec_data)

        # 6. Generate 3MF project
        proj_payload = {
            "printer_id": "bambu_lab_a1",
            "filament_id": "pla_basic",
            "objective": "balanced_quality",
            "include_split_parts": False
        }
        proj_res = self.client.post(f"/api/projects/{model_id}/generate-3mf", json=proj_payload)
        self.assertEqual(proj_res.status_code, 200)
        proj_data = proj_res.json()
        self.assertTrue(proj_data["success"])
        self.assertTrue(proj_data["validation"]["is_valid"])
        self.assertEqual(proj_data["validation"]["status"], "SLICING_REQUIRED")

        # 7. Download generated 3MF
        dl_res = self.client.get(proj_data["download_url"])
        self.assertEqual(dl_res.status_code, 200)
        self.assertGreater(len(dl_res.content), 0)

    def test_slicer_capabilities(self):
        """Verifies slicer capabilities endpoint."""
        res = self.client.get("/api/slicer/capabilities")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["slicer_name"], "Bambu Studio")
        self.assertIn("is_installed", data)

    def test_validate_gcode(self):
        """Verifies deep G-code inspection endpoint with real G-code file."""
        real_gcode = os.path.join(Config.WORKSPACE_DIR, "outputs", "gcode", "single_color_PLA_2h20m.gcode")
        if not os.path.exists(real_gcode):
            self.skipTest("Real G-code not found.")

        res = self.client.post("/api/slicer/validate-gcode", params={"gcode_path": real_gcode})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "SLICE_VALIDATED")
        self.assertTrue(data["fits_build_plate"])
        self.assertTrue(data["is_actual_slicer_output"])
        self.assertAlmostEqual(data["maintenance_bounds_x"][0], -48.2, places=1)

if __name__ == "__main__":
    unittest.main()

